"""Reusable card-row widget for the Pinochle table."""

import json

from PyQt5.QtCore import QMimeData, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QDrag, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from display_themes import DEFAULT_THEME, THEMES
from game import Player
from selectable_label import SelectableLabel

CARD_W = 100
CARD_H = 142
RAISE_PIXELS = 8
PANEL_PADDING = 16
TRICK_TARGET_MIN_WIDTH = 260


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
        self.drop_enabled = True
        self.click_sources = []
        self._theme = THEMES[DEFAULT_THEME]
        self._table_font = self.font()
        self._preferred_card_height = CARD_H
        self.selection_peers = []
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(
            (Qt.AlignHCenter if panel_name.startswith("trick") else Qt.AlignLeft)
            | Qt.AlignVCenter
        )
        self.setAcceptDrops(True)
        # Use one card-derived height for every table panel.  Letting the
        # vertical layouts distribute surplus pixels independently can make
        # otherwise identical rows differ by a pixel at some window sizes.
        self.setFixedHeight(CARD_H + PANEL_PADDING)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if panel_name.startswith(("trick", "meld")) or panel_name == "trump":
            area_name = (
                "TRICK" if panel_name.startswith("trick")
                else "MELD" if panel_name.startswith("meld")
                else "TRUMP"
            )
            self.setMinimumWidth(
                TRICK_TARGET_MIN_WIDTH
                if panel_name.startswith("trick")
                else CARD_W + 16
            )
            if panel_name == "trump":
                hint = "TRUMP\nDROP DIX HERE"
            else:
                player_number = panel_name[-1]
                card_word = "CARD" if area_name == "TRICK" else "SELECTED CARDS"
                if area_name == "TRICK":
                    hint = (
                        f"{Player(int(player_number)).display_name.upper()}\n"
                        "TRICK\nDROP HERE"
                    )
                else:
                    hint = (
                        f"{Player(int(player_number)).display_name.upper()} "
                        f"{area_name}\nDROP {card_word} HERE"
                    )
            self._drop_hint = QLabel(
                hint,
                self,
            )
            self._drop_hint.setAlignment(Qt.AlignCenter)
            self._drop_hint.setAttribute(Qt.WA_TransparentForMouseEvents)
            self._drop_hint.setFont(self._table_font)
            self.layout.addWidget(self._drop_hint)
            self._set_drop_target_style(False)

    def _set_drop_target_style(self, active):
        """Make play-area panels visible and highlight them during a drag."""
        if self._drop_hint is None:
            return
        active = active and self.drop_enabled
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
        self._drop_hint.setStyleSheet(f"color: {color};")

    def set_table_font(self, font):
        """Apply the user-selected font to panel text, not card artwork."""
        self._table_font = font
        if self._drop_hint is not None:
            self._drop_hint.setFont(font)
        for badge in self._badges:
            badge.setFont(font)
            badge.adjustSize()

    def set_drop_enabled(self, enabled):
        self.drop_enabled = bool(enabled)
        self.setAcceptDrops(self.drop_enabled)
        self._set_drop_target_style(False)

    def set_drop_hint(self, text):
        if self._drop_hint is not None:
            self._drop_hint.setText(text)
            self._drop_hint.show()

    def _selected_payload(self):
        selected = [
            (panel.panel_name, panel.cards[index])
            for panel in self.click_sources
            for index, widget in enumerate(panel.labels)
            if widget.selected
        ]
        if not selected:
            return None
        return selected[0][0], [card_id for _source, card_id in selected]

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
            "border-radius: 8px; padding: 2px 6px;"
        )
        badge.setFont(self._table_font)
        badge.adjustSize()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_cards()

    def set_card_height(self, height):
        """Set a shared responsive card height for this table row."""
        height = max(1, int(height))
        if height == self._preferred_card_height:
            return
        self._preferred_card_height = height
        self.setFixedHeight(height + PANEL_PADDING)
        self._resize_cards()

    def _card_size(self):
        if not self.labels:
            return CARD_W, CARD_H
        card_h = min(
            self._preferred_card_height,
            max(1, self.height() - RAISE_PIXELS),
        )
        card_w = round(card_h * CARD_W / CARD_H)
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
        drag.setDragCursor(self._valid_drop_cursor(), Qt.MoveAction)
        drag.exec_(Qt.MoveAction)

    @staticmethod
    def _valid_drop_cursor():
        """Return a large, high-contrast valid-drop indicator."""
        size = 48
        cursor = QPixmap(size, size)
        cursor.fill(Qt.transparent)
        painter = QPainter(cursor)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#0b5d1e"), 3))
        painter.setBrush(QColor("#22c55e"))
        painter.drawEllipse(3, 3, size - 6, size - 6)
        painter.setPen(QPen(QColor("white"), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(13, 25, 21, 33)
        painter.drawLine(21, 33, 36, 16)
        painter.end()
        return cursor

    def dragEnterEvent(self, event):
        if self.drop_enabled and event.mimeData().hasFormat("application/x-pinochle-cards"):
            self._set_drop_target_style(True)
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-pinochle-cards"):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self._set_drop_target_style(False)
        event.accept()

    def dropEvent(self, event):
        if not self.drop_enabled:
            event.ignore()
            return
        try:
            payload = json.loads(bytes(event.mimeData().data("application/x-pinochle-cards")).decode("utf-8"))
            self.cards_dropped.emit(payload["source"], payload["cards"])
            event.acceptProposedAction()
        except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
            event.ignore()
        finally:
            self._set_drop_target_style(False)

    def enterEvent(self, event):
        if self.drop_enabled and self._selected_payload():
            self._set_drop_target_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.underMouse():
            self._set_drop_target_style(False)
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        payload = self._selected_payload()
        if (
            self.drop_enabled
            and payload
            and event.button() == Qt.LeftButton
        ):
            source, cards = payload
            self.cards_dropped.emit(source, cards)
            self._set_drop_target_style(False)
            event.accept()
            return
        super().mouseReleaseEvent(event)

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
