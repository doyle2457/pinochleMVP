from weakref import WeakSet

from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtWidgets import QLabel

from display_themes import DEFAULT_THEME, THEMES

NORMAL_BORDER_WIDTH = 3
ACTION_BORDER_WIDTH = 10
NORMAL_BORDER_RADIUS = 5
ACTION_BORDER_RADIUS = 14


class SelectableLabel(QLabel):
    """A card image whose left-click toggles its selected state."""

    clicked = pyqtSignal(bool)
    drag_requested = pyqtSignal()
    _instances = WeakSet()
    _colors = THEMES[DEFAULT_THEME]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self._selected = False
        self._newly_drawn = False
        self._press_position = QPoint()
        self._drag_started = False
        self._instances.add(self)
        self._update_style()

    @classmethod
    def set_theme(cls, theme):
        """Apply action-border colors to existing and future cards."""
        cls._colors = theme
        for instance in tuple(cls._instances):
            instance._update_style()

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        self._selected = value
        self._update_style()

    @property
    def newly_drawn(self):
        return self._newly_drawn

    @newly_drawn.setter
    def newly_drawn(self, value):
        self._newly_drawn = value
        self._update_style()

    def _update_style(self):
        if self._selected:
            color = self._colors["selected"]
            width = ACTION_BORDER_WIDTH
            radius = ACTION_BORDER_RADIUS
        elif self._newly_drawn:
            color = self._colors["newly_drawn"]
            width = ACTION_BORDER_WIDTH
            radius = ACTION_BORDER_RADIUS
        else:
            color = self._colors["card_border"]
            width = NORMAL_BORDER_WIDTH
            radius = NORMAL_BORDER_RADIUS
        self.setStyleSheet(
            f"border: {width}px solid {color}; border-radius: {radius}px;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_position = event.pos()
            self._drag_started = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return super().mouseMoveEvent(event)
        if not self._drag_started and (event.pos() - self._press_position).manhattanLength() >= 10:
            self._drag_started = True
            self.drag_requested.emit()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and not self._drag_started:
            if self.newly_drawn:
                # The first click only acknowledges a drawn card; a later
                # click can select it normally for play or meld.
                self.newly_drawn = False
                self.clicked.emit(False)
            else:
                self.selected = not self.selected
                self.clicked.emit(self.selected)
        super().mouseReleaseEvent(event)
