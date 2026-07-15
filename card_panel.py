"""Reusable card-row widget for the Pinochle table."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QWidget

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

    def __init__(self, game, parent=None):
        super().__init__(parent)
        self.game = game
        self.cards = []
        self.labels = []
        self._holders = []
        self._source_pixmaps = []
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(8)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

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
        label.move(0, 0 if label.selected else RAISE_PIXELS)

    def _handle_label_click(self, hand_position, selected):
        self._position_label(self.labels[hand_position])
        self.card_clicked.emit(self.cards[hand_position], hand_position)

    def _add_card(self, source, hand_position=None):
        holder = QWidget(self)
        label = SelectableLabel(holder)
        label.setPixmap(source)
        if hand_position is None:
            label.setEnabled(False)
            label.setCursor(Qt.ArrowCursor)
        else:
            label.clicked.connect(lambda selected, position=hand_position: self._handle_label_click(position, selected))
        self._holders.append(holder)
        self.labels.append(label)
        self._source_pixmaps.append(source)
        self.layout.addWidget(holder)

    def set_cards(self, card_index_list):
        self.clear()
        self.cards = list(card_index_list)
        for hand_position, card_index in enumerate(self.cards):
            self._add_card(QPixmap(self.game.deck.cards[card_index].filename), hand_position)
        self._resize_cards()

    def set_card_back(self, image_path):
        self.clear()
        self._add_card(QPixmap(image_path))
        self._resize_cards()

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.cards.clear()
        self.labels.clear()
        self._holders.clear()
        self._source_pixmaps.clear()
