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
