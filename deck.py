# deck.py
from __future__ import annotations

import random
from typing import List

from card import Card


class Deck:
    def __init__(self) -> None:
        ranks = ["A", "10", "K", "Q", "J", "9"]
        suits = ["S", "H", "D", "C"]

        # Pinochle deck = double deck of 24 cards
        self.cards: List[Card] = [
            Card(s, r) for s in suits for r in ranks for _ in range(2)
        ]

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def deal(self, n: int) -> List[Card]:
        hand = self.cards[:n]
        del self.cards[:n]
        return hand
