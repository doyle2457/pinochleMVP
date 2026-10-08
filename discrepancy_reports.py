"""Discrepancy-report records and durable JSON/Markdown storage."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, timezone
from pathlib import Path


PRIORITIES = ("Critical", "High", "Medium", "Low")
STATUSES = (
    "Reported",
    "Analyzing",
    "Planned",
    "In Progress",
    "Resolved",
    "Verified",
    "Closed",
    "Deferred",
)
DISPOSITION_HELP = {
    "Fix Planned": (
        "The discrepancy is valid. Reproduce it, add a failing test when "
        "practical, implement the correction, and verify the result. The "
        "disposition field may include a proposed solution."
    ),
    "Deferred": (
        "The discrepancy is valid but does not justify immediate work. Record "
        "why it is being postponed and when it should be reconsidered."
    ),
    "Cannot Reproduce": (
        "The reported behavior could not be repeated. Record the environments, "
        "attempts, and additional evidence needed before closing it."
    ),
    "Duplicate": (
        "Another DR already covers the same underlying problem. Reference the "
        "controlling DR number in the disposition note."
    ),
    "Working as Designed": (
        "The behavior matches the chosen rules or design. Note the governing "
        "rule and whether clearer hints or documentation are still needed."
    ),
    "More Information Needed": (
        "The report lacks enough evidence for a decision. Identify the missing "
        "game state, cards, messages, screenshots, or reproduction steps."
    ),
}


@dataclass
class DiscrepancyReport:
    report_id: str = ""
    title: str = ""
    reported_date: str = ""
    priority: str = "Medium"
    status: str = "Reported"
    what_happened: str = ""
    expected_behavior: str = ""
    game_stage: str = ""
    player: str = ""
    cards_involved: str = ""
    displayed_text: str = ""
    reproduction_steps: str = ""
    disposition_category: str = ""
    disposition: str = ""
    resolution_notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    @classmethod
    def fresh(cls) -> "DiscrepancyReport":
        return cls(reported_date=date.today().isoformat())

    @classmethod
    def from_dict(cls, values: dict) -> "DiscrepancyReport":
        if not isinstance(values, dict):
            raise ValueError("The discrepancy report data is invalid.")
        known_values = {
            field.name: values[field.name]
            for field in fields(cls)
            if field.name in values
        }
        report = cls(**known_values)
        report.validate(require_id=True)
        return report

    def validate(self, require_id: bool = False) -> None:
        if require_id and not re.fullmatch(r"DR-\d{4,}", self.report_id):
            raise ValueError("The discrepancy report has an invalid report ID.")
        if not self.title.strip():
            raise ValueError("Enter a title for the discrepancy report.")
        try:
            date.fromisoformat(self.reported_date)
        except (TypeError, ValueError) as error:
            raise ValueError("Enter a valid report date.") from error
        if self.priority not in PRIORITIES:
            raise ValueError("Select a valid priority.")
        if self.status not in STATUSES:
            raise ValueError("Select a valid status.")
        if self.disposition_category not in ("", *DISPOSITION_HELP):
            raise ValueError("Select a valid disposition category.")


class DiscrepancyReportStore:
    """Save editable JSON records and matching GPT-readable Markdown files."""

    FORMAT_VERSION = 1

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = (
            Path(directory)
            if directory
            else Path.home() / ".pinochleMVP" / "discrepancy_reports"
        )

    def _next_id(self) -> str:
        highest = 0
        if self.directory.exists():
            for path in self.directory.glob("DR-*.*"):
                if path.suffix not in {".json", ".md"}:
                    continue
                match = re.fullmatch(r"DR-(\d+)", path.stem)
                if match:
                    highest = max(highest, int(match.group(1)))
        return f"DR-{highest + 1:04d}"

    def _path(self, report_id: str, suffix: str) -> Path:
        if not re.fullmatch(r"DR-\d{4,}", report_id):
            raise ValueError("The discrepancy report has an invalid report ID.")
        return self.directory / f"{report_id}{suffix}"

    def list(self) -> list[DiscrepancyReport]:
        if not self.directory.exists():
            return []
        reports = []
        for path in self.directory.glob("DR-*.json"):
            try:
                reports.append(self._read(path))
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
        return sorted(reports, key=lambda report: report.report_id, reverse=True)

    def save(self, report: DiscrepancyReport) -> DiscrepancyReport:
        report.title = report.title.strip()
        report.validate(require_id=bool(report.report_id))

        now = datetime.now(timezone.utc).isoformat()
        if not report.report_id:
            report.report_id = self._next_id()
            report.created_at = now
        report.updated_at = now
        report.validate(require_id=True)
        self.directory.mkdir(parents=True, exist_ok=True)

        envelope = {
            "format_version": self.FORMAT_VERSION,
            "report": asdict(report),
        }
        self._atomic_write(
            self._path(report.report_id, ".json"),
            json.dumps(envelope, indent=2, ensure_ascii=False) + "\n",
        )
        self._atomic_write(
            self._path(report.report_id, ".md"),
            self.to_markdown(report),
        )
        return report

    def load(self, report_id: str) -> DiscrepancyReport:
        return self._read(self._path(report_id, ".json"))

    def _read(self, path: Path) -> DiscrepancyReport:
        with path.open("r", encoding="utf-8") as stream:
            envelope = json.load(stream)
        if not isinstance(envelope, dict):
            raise ValueError("The discrepancy-report file is invalid.")
        if envelope.get("format_version") != self.FORMAT_VERSION:
            raise ValueError("This discrepancy-report format is not supported.")
        return DiscrepancyReport.from_dict(envelope["report"])

    def delete(self, report_id: str) -> None:
        for suffix in (".json", ".md"):
            path = self._path(report_id, suffix)
            if path.exists():
                path.unlink()

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        temporary = target.with_suffix(target.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)

    @staticmethod
    def to_markdown(report: DiscrepancyReport) -> str:
        def section(title: str, value: str) -> str:
            content = value.strip() or "_Not provided._"
            return f"## {title}\n\n{content}\n"

        return "\n".join(
            (
                f"# {report.report_id}: {report.title}",
                "",
                f"- **Reported:** {report.reported_date}",
                f"- **Priority:** {report.priority}",
                f"- **Status:** {report.status}",
                f"- **Disposition category:** "
                f"{report.disposition_category or 'Not yet assigned'}",
                f"- **Created:** {report.created_at}",
                f"- **Updated:** {report.updated_at}",
                "",
                section("What happened", report.what_happened),
                section("What should have happened", report.expected_behavior),
                section("Game stage", report.game_stage),
                section("Player", report.player),
                section("Cards involved", report.cards_involved),
                section("Exact hint, score, or message displayed", report.displayed_text),
                section("Steps to reproduce", report.reproduction_steps),
                section(
                    "Disposition, planned action, or proposed solution",
                    report.disposition,
                ),
                section("Resolution and verification notes", report.resolution_notes),
            )
        ).rstrip() + "\n"
