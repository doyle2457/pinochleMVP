"""Durable, versioned storage for named Pinochle game snapshots."""

from __future__ import annotations

import json
import os
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from game import Game


class SavedGameStore:
    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory else Path.home() / ".pinochleMVP" / "saved_games"

    @staticmethod
    def _filename(name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()).strip("._")
        if not safe:
            raise ValueError("Enter a saved-game name containing letters or numbers.")
        digest = hashlib.sha256(name.strip().encode("utf-8")).hexdigest()[:12]
        return f"{safe[:80]}-{digest}.json"

    def list(self) -> list[dict]:
        if not self.directory.exists():
            return []
        saves = []
        for path in self.directory.glob("*.json"):
            try:
                with path.open("r", encoding="utf-8") as stream:
                    envelope = json.load(stream)
                saves.append({"name": envelope["name"], "saved_at": envelope["saved_at"]})
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return sorted(saves, key=lambda item: item["saved_at"], reverse=True)

    def save(self, name: str, game: Game) -> None:
        name = name.strip()
        filename = self._filename(name)
        self.directory.mkdir(parents=True, exist_ok=True)
        envelope = {
            "name": name,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "game": game.to_dict(),
        }
        target = self.directory / filename
        temporary = target.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(envelope, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(target)

    def load(self, name: str) -> Game:
        with (self.directory / self._filename(name)).open("r", encoding="utf-8") as stream:
            envelope = json.load(stream)
        return Game.from_dict(envelope["game"])

    def delete(self, name: str) -> None:
        (self.directory / self._filename(name)).unlink()
