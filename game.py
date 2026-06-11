# game.py
from __future__ import annotations

from typing import List

from PyQt5.QtCore import QObject, pyqtSignal

from card import Card
from deck import Deck


class Game(QObject):
    hand_updated = pyqtSignal(list)  # Emits List[Card]

    def __init__(self) -> None:
        super().__init__()
        self.deck = Deck()
        self.player_hand: List[Card] = []

    def start_new_game(self) -> None:
        self.deck.shuffle()
        self.player_hand = self.deck.deal(12)
        self.hand_updated.emit(self.player_hand)

    def play_card(self, card: Card) -> None:
        if card in self.player_hand:
            self.player_hand.remove(card)
            self.hand_updated.emit(self.player_hand)
