"""Reusable card-row widget for the Pinochle table."""

import json

from PyQt5.QtCore import QMimeData, Qt, pyqtSignal
from PyQt5.QtGui import QDrag, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from display_themes import DEFAULT_THEME, THEMES
from game import Player
from selectable_label import SelectableLabel

CARD_W = 100
CARD_H = 142
RAISE_PIXELS = 8


class CardPanel(QWidget):
    """Display face-up cards or a single face-down pile.

    ``card_clicked`` emits ``(deck_card_id, hand_position)``. The deck ID is
    stable across sorting and the hand position is the visible order at click.
    """

    card_clicked = pyqtSignal(int, int)
    cards_dropped = pyqtSignal(str, object)

    def __init__(self, game, parent=None, panel_name=""):
        super().__init__(parent)
        self.game = game
        self.panel_name = panel_name
        self.cards = []
        self.labels = []
        self._holders = []
        self._source_pixmaps = []
        self._badges = []
        self._drop_hint = None
        self._theme = THEMES[DEFAULT_THEME]
        self.selection_peers = []
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setAcceptDrops(True)
        # Use one card-derived height for every table panel.  Letting the
        # vertical layouts distribute surplus pixels independently can make
        # otherwise identical rows differ by a pixel at some window sizes.
        self.setFixedHeight(CARD_H + 16)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if panel_name.startswith(("trick", "meld")):
            area_name = "TRICK" if panel_name.startswith("trick") else "MELD"
            player_number = panel_name[-1]
            self.setMinimumWidth(CARD_W + 16)
            card_word = "CARD" if area_name == "TRICK" else "SELECTED CARDS"
            self._drop_hint = QLabel(
                f"{Player(int(player_number)).display_name.upper()} {area_name}\n"
                f"DROP {card_word} HERE",
                self,
            )
            self._drop_hint.setAlignment(Qt.AlignCenter)
            self._drop_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
            self.layout.addWidget(self._drop_hint)
            self._set_drop_target_style(False)

    def _set_drop_target_style(self, active):
        """Make play-area panels visible and highlight them during a drag."""
        if self._drop_hint is None:
            return
        color = self._theme["active_target"] if active else self._theme["muted"]
        background = (
            self._theme["target_background"]
            if active
            else self._theme["idle_target_background"]
        )
        self.setStyleSheet(
            f"CardPanel {{ border: 3px dashed {color}; border-radius: 8px; "
            f"background-color: {background}; }}"
        )
        self._drop_hint.setStyleSheet(f"color: {color}; font-weight: bold;")

    def set_theme(self, theme):
        """Refresh this panel's themed drop-target treatment."""
        self._theme = theme
        self._set_drop_target_style(False)
        for badge in self._badges:
            self._style_badge(badge)

    def _style_badge(self, badge):
        """Keep pile counters legible and consistent in every theme."""
        badge.setStyleSheet(
            f"background: {self._theme['badge_background']}; "
            f"color: {self._theme['badge_text']}; "
            f"border: 1px solid {self._theme['border']}; "
            "border-radius: 8px; padding: 2px 6px; "
            "font-size: 15pt; font-weight: bold;"
        )
        badge.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_cards()

    def _card_size(self):
        count = len(self.labels)
        if not count:
            return CARD_W, CARD_H
        card_h = min(CARD_H, max(1, self.height() - RAISE_PIXELS))
        card_w = round(card_h * CARD_W / CARD_H)
        available_width = max(1, self.width() - self.layout.spacing() * (count - 1))
        if card_w * count > available_width:
            card_w = max(1, available_width // count)
            card_h = max(1, round(card_w * CARD_H / CARD_W))
        return card_w, card_h

    def _resize_cards(self):
        card_w, card_h = self._card_size()
        for holder, label, source in zip(self._holders, self.labels, self._source_pixmaps):
            holder.setFixedSize(card_w, card_h + RAISE_PIXELS)
            label.setFixedSize(card_w, card_h)
            label.setPixmap(source.scaled(card_w, card_h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self._position_label(label)

    @staticmethod
    def _position_label(label):
        label.move(0, 0 if label.selected or label.newly_drawn else RAISE_PIXELS)

    def _handle_label_click(self, hand_position, selected):
        self._position_label(self.labels[hand_position])
        self.card_clicked.emit(self.cards[hand_position], hand_position)

    def _add_card(self, source, hand_position=None, badge=None, newly_drawn=False):
        if self._drop_hint is not None:
            self._drop_hint.hide()
        holder = QWidget(self)
        label = SelectableLabel(holder)
        label.setPixmap(source)
        label.newly_drawn = newly_drawn
        if hand_position is None:
            label.setEnabled(False)
            label.setCursor(Qt.ArrowCursor)
        else:
            label.clicked.connect(lambda selected, position=hand_position: self._handle_label_click(position, selected))
            label.drag_requested.connect(lambda widget=label: self._start_drag(widget))
        self._holders.append(holder)
        self.labels.append(label)
        self._source_pixmaps.append(source)
        if badge is not None:
            badge_label = QLabel(str(badge), holder)
            badge_label.move(4, 4)
            self._badges.append(badge_label)
            self._style_badge(badge_label)
        self.layout.addWidget(holder)

    def _start_drag(self, label):
        panels = [self, *self.selection_peers]
        selected_ids = [
            panel.cards[index]
            for panel in panels
            for index, widget in enumerate(panel.labels)
            if widget.selected
        ]
        if not selected_ids:
            selected_ids = [self.cards[self.labels.index(label)]]
        mime = QMimeData()
        mime.setData("application/x-pinochle-cards", json.dumps({
            "source": self.panel_name, "cards": selected_ids
        }).encode("utf-8"))
        drag = QDrag(label)
        drag.setMimeData(mime)
        drag.setPixmap(label.pixmap())
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-pinochle-cards"):
            self._set_drop_target_style(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-pinochle-cards"):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_drop_target_style(False)
        event.accept()

    def dropEvent(self, event):
        try:
            payload = json.loads(bytes(event.mimeData().data("application/x-pinochle-cards")).decode("utf-8"))
            self.cards_dropped.emit(payload["source"], payload["cards"])
            event.acceptProposedAction()
        except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            event.ignore()
        finally:
            self._set_drop_target_style(False)

    def set_cards(self, card_index_list, newly_drawn_ids=()):
        self.clear()
        self.cards = list(card_index_list)
        newly_drawn_ids = set(newly_drawn_ids)
        for hand_position, card_index in enumerate(self.cards):
            self._add_card(
                QPixmap(self.game.deck.cards[card_index].filename),
                hand_position,
                newly_drawn=card_index in newly_drawn_ids,
            )
        self._resize_cards()

    def set_card_back(self, image_path, count=None, selectable_card_id=None):
        """Show a card back, optionally exposing its card ID for click actions."""
        self.clear()
        hand_position = None
        if selectable_card_id is not None:
            self.cards = [selectable_card_id]
            hand_position = 0
        self._add_card(QPixmap(image_path), hand_position=hand_position, badge=count)
        self._resize_cards()

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self._drop_hint:
                widget.deleteLater()
        self.cards.clear()
        self.labels.clear()
        self._holders.clear()
        self._source_pixmaps.clear()
        self._badges.clear()
        if self._drop_hint is not None:
            self.layout.addWidget(self._drop_hint)
            self._drop_hint.show()
