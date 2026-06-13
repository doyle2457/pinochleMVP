from __future__ import annotations

from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

from card import Card
from game import Game

CARD_W = 100
CARD_H = 150


class CardPanel(QWidget):
    def __init__(self, game: Game, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game = game
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(8)

        self.game.hand_updated.connect(self.update_hand)

    def update_hand(self, cards: List[Card]) -> None:
        # Clear old widgets
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new card widgets
        for card in cards:
            lbl = QLabel()
            pix = QPixmap(f"assets/cards/{card.image_name}")
            lbl.setPixmap(
                pix.scaled(CARD_W, CARD_H, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            lbl.setObjectName(f"card_{card.rank}{card.suit}")

            # Click-to-play
            lbl.mousePressEvent = lambda e, c=card: self.game.play_card(c)

            self.layout.addWidget(lbl)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    # ---------------------------------------------------------
    # Load card images into the panel
    # ---------------------------------------------------------


def set_cards(self, card_list: list[int]) -> None:
    """Replace all cards with a new list of card IDs."""
    self.clear()
    self.cards = card_list

    for index, card_id in enumerate(card_list):
        card = self.parent().game.get_card(card_id)  # get Card object

        suit = card.suit.lower()  # clubs, hearts, etc.
        rank = card.rank  # A, 10, K, Q, J, 9

        filename = f"{suit}_{rank}.png"
        print("filename in set cards", filename)  # DEBUG
        full_path = os.path.join(CARD_DIR, filename)
        print("Loading:", full_path)  # DEBUG

        lbl = QLabel(self)
        lbl.setFixedSize(CARD_W, CARD_H)
        lbl.setScaledContents(True)

        pix = QPixmap(full_path)
        lbl.setPixmap(pix)

        lbl.mousePressEvent = lambda e, i=index: self.card_clicked.emit(i)

        self.labels.append(lbl)
        self.layout.addWidget(lbl)

    # ---------------------------------------------------------
    # Remove all cards
    # ---------------------------------------------------------
    def clear(self) -> None:
        """Remove all card widgets from the panel."""
        for lbl in self.labels:
            self.layout.removeWidget(lbl)
            lbl.deleteLater()

        self.labels = []
        self.cards = []
