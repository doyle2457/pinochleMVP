"""Clickable PyQt forms for creating and managing discrepancy reports."""

from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import QDate, QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from discrepancy_reports import (
    DISPOSITION_HELP,
    PRIORITIES,
    STATUSES,
    DiscrepancyReport,
    DiscrepancyReportStore,
)


class DiscrepancyReportEditor(QDialog):
    """Edit one discrepancy report using a scrollable computer form."""

    def __init__(
        self,
        store: DiscrepancyReportStore,
        report: DiscrepancyReport | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.report = report or DiscrepancyReport.fresh()
        self.setWindowTitle(
            f"Discrepancy Report {self.report.report_id}".strip()
        )
        self.resize(900, 760)

        outer = QVBoxLayout(self)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        form_widget = QWidget(scroll)
        form = QVBoxLayout(form_widget)

        summary = QFormLayout()
        self.report_id = QLabel(self.report.report_id or "Assigned when first saved")
        self.title = QLineEdit(self.report.title)
        self.reported_date = QDateEdit(self)
        self.reported_date.setCalendarPopup(True)
        parsed_date = QDate.fromString(self.report.reported_date, Qt.ISODate)
        self.reported_date.setDate(parsed_date if parsed_date.isValid() else QDate.currentDate())
        summary.addRow("DR number:", self.report_id)
        summary.addRow("Title:", self.title)
        summary.addRow("Date:", self.reported_date)
        form.addLayout(summary)

        self.priority_group, self.priority_buttons = self._choice_group(
            "Priority", PRIORITIES, self.report.priority, columns=4
        )
        form.addWidget(self.priority_group)
        self.status_group, self.status_buttons = self._choice_group(
            "Disposition status — select the current phase",
            STATUSES,
            self.report.status,
            columns=4,
            checkboxes=True,
        )
        form.addWidget(self.status_group)

        self.what_happened = self._add_text(
            form, "What happened", self.report.what_happened
        )
        self.expected_behavior = self._add_text(
            form, "What should have happened", self.report.expected_behavior
        )
        self.game_stage = self._add_text(form, "Game stage", self.report.game_stage, 65)
        self.player = self._add_text(form, "Player", self.report.player, 65)
        self.cards_involved = self._add_text(
            form, "Cards involved", self.report.cards_involved, 80
        )
        self.displayed_text = self._add_text(
            form,
            "Exact hint, score, or message displayed",
            self.report.displayed_text,
            80,
        )
        self.reproduction_steps = self._add_text(
            form, "Steps to reproduce", self.report.reproduction_steps, 120
        )
        (
            self.disposition_category_group,
            self.disposition_category_buttons,
        ) = self._choice_group(
            "Disposition decision — select one after analysis",
            tuple(DISPOSITION_HELP),
            self.report.disposition_category,
            columns=3,
            checkboxes=True,
            tooltips=DISPOSITION_HELP,
        )
        form.addWidget(self.disposition_category_group)
        self.disposition_help = QLabel(self)
        self.disposition_help.setWordWrap(True)
        self.disposition_help.setStyleSheet(
            "padding: 6px; border: 1px solid palette(mid);"
        )
        form.addWidget(self.disposition_help)
        for button in self.disposition_category_buttons.buttons():
            button.clicked.connect(
                lambda checked, choice=button.text(): checked
                and self._show_disposition_help(choice)
            )
        self._show_disposition_help(self.report.disposition_category)
        self.disposition = self._add_text(
            form,
            "Disposition, planned action, or proposed solution",
            self.report.disposition,
            100,
        )
        self.resolution_notes = self._add_text(
            form,
            "Resolution and verification notes",
            self.report.resolution_notes,
            100,
        )

        scroll.setWidget(form_widget)
        outer.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=self)
        save = QPushButton("Save", self)
        save_close = QPushButton("Save && Close", self)
        buttons.addButton(save, QDialogButtonBox.ActionRole)
        buttons.addButton(save_close, QDialogButtonBox.AcceptRole)
        save.clicked.connect(self.save_report)
        save_close.clicked.connect(lambda: self.save_report(close=True))
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    @staticmethod
    def _choice_group(
        title, choices, selected, columns, checkboxes=False, tooltips=None
    ):
        group_box = QGroupBox(title)
        layout = QGridLayout(group_box)
        button_group = QButtonGroup(group_box)
        button_group.setExclusive(True)
        for index, choice in enumerate(choices):
            button_type = QCheckBox if checkboxes else QRadioButton
            button = button_type(choice, group_box)
            button.setChecked(choice == selected)
            if tooltips and choice in tooltips:
                button.setToolTip(tooltips[choice])
            button_group.addButton(button)
            layout.addWidget(button, index // columns, index % columns)
        return group_box, button_group

    def _show_disposition_help(self, choice):
        self.disposition_help.setText(
            DISPOSITION_HELP.get(
                choice,
                "Select a disposition decision after the report has been analyzed.",
            )
        )

    @staticmethod
    def _add_text(layout, label, value, height=95):
        layout.addWidget(QLabel(f"{label}:"))
        editor = QPlainTextEdit(value)
        editor.setMinimumHeight(height)
        layout.addWidget(editor)
        return editor

    @staticmethod
    def _selected_text(group: QButtonGroup) -> str:
        selected = group.checkedButton()
        return selected.text() if selected else ""

    def save_report(self, close=False):
        self.report.title = self.title.text()
        self.report.reported_date = self.reported_date.date().toString(Qt.ISODate)
        self.report.priority = self._selected_text(self.priority_buttons)
        self.report.status = self._selected_text(self.status_buttons)
        self.report.disposition_category = self._selected_text(
            self.disposition_category_buttons
        )
        for field in (
            "what_happened",
            "expected_behavior",
            "game_stage",
            "player",
            "cards_involved",
            "displayed_text",
            "reproduction_steps",
            "disposition",
            "resolution_notes",
        ):
            setattr(self.report, field, getattr(self, field).toPlainText())
        try:
            self.store.save(self.report)
            self.report_id.setText(self.report.report_id)
            self.setWindowTitle(f"Discrepancy Report {self.report.report_id}")
            if close:
                self.accept()
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.critical(self, "Unable to Save DR", str(error))


class DiscrepancyReportManager(QDialog):
    """Create, reopen, delete, and locate saved discrepancy reports."""

    def __init__(self, store: DiscrepancyReportStore, settings=None, parent=None) -> None:
        super().__init__(parent)
        self.store = store
        self.settings = settings
        self.setWindowTitle("Discrepancy Reports")
        self.resize(820, 470)
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Create a fresh DR or reopen an existing report. Each saved DR "
                "also has a Markdown copy for Codex/GPT analysis and disposition."
            )
        )
        self.report_list = QListWidget(self)
        self.report_list.itemDoubleClicked.connect(lambda _item: self.open_report())
        layout.addWidget(self.report_list)
        self.folder_label = QLabel(str(self.store.directory), self)
        self.folder_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.folder_label)

        row = QHBoxLayout()
        for label, slot in (
            ("New DR", self.new_report),
            ("Open", self.open_report),
            ("Delete", self.delete_report),
            ("Choose Folder", self.choose_folder),
            ("Open Folder", self.open_folder),
        ):
            button = QPushButton(label, self)
            button.clicked.connect(slot)
            row.addWidget(button)
        row.addStretch()
        close = QPushButton("Close", self)
        close.clicked.connect(self.accept)
        row.addWidget(close)
        layout.addLayout(row)
        self.refresh()

    def refresh(self):
        self.report_list.clear()
        for report in self.store.list():
            item = QListWidgetItem(
                f"{report.report_id}  |  {report.priority}  |  "
                f"{report.status}  |  {report.title}"
            )
            item.setData(Qt.UserRole, report.report_id)
            self.report_list.addItem(item)

    def new_report(self):
        editor = DiscrepancyReportEditor(self.store, parent=self)
        editor.exec_()
        self.refresh()

    def open_report(self):
        item = self.report_list.currentItem()
        if item is None:
            return
        try:
            report = self.store.load(item.data(Qt.UserRole))
            editor = DiscrepancyReportEditor(self.store, report, self)
            editor.exec_()
            self.refresh()
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.critical(self, "Unable to Open DR", str(error))

    def delete_report(self):
        item = self.report_list.currentItem()
        if item is None:
            return
        report_id = item.data(Qt.UserRole)
        if QMessageBox.question(
            self,
            "Delete Discrepancy Report",
            f"Permanently delete {report_id} and its Markdown copy?",
        ) != QMessageBox.Yes:
            return
        try:
            self.store.delete(report_id)
            self.refresh()
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Unable to Delete DR", str(error))

    def open_folder(self):
        self.store.directory.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.store.directory.resolve())))

    def choose_folder(self):
        selected = QFileDialog.getExistingDirectory(
            self,
            "Choose Discrepancy Report Folder",
            str(self.store.directory),
        )
        if not selected:
            return
        self.set_directory(selected)

    def set_directory(self, directory):
        self.store.directory = Path(directory)
        if self.settings is not None:
            self.settings.setValue(
                "discrepancy_report_directory", str(self.store.directory)
            )
        self.folder_label.setText(str(self.store.directory))
        self.refresh()
