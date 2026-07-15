from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel


class SelectableLabel(QLabel):
    """A card image whose left-click toggles its selected state."""

    clicked = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._selected = False
        self._update_style()

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self._update_style()

    def _update_style(self):
        color = "red" if self._selected else "black"
        self.setStyleSheet(f"border: 3px solid {color}; border-radius: 5px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected = not self.selected
            self.clicked.emit(self.selected)
        super().mousePressEvent(event)
