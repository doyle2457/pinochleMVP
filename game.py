from __future__ import annotations

from typing import List

from deck import Deck


class Game:
    """Controller and state holder for a two-player Pinochle game."""

    def __init__(self, sequences: int = 2) -> None:
        self.sequences = sequences
        self.hand1: List[int] = []
        self.hand2: List[int] = []
        self.meld1: List[int] = []
        self.meld2: List[int] = []
        self.trick: List[int] = []
        self.stock: List[int] = []
        self.trump: List[int] = []
        self.won1: List[int] = []
        self.won2: List[int] = []
        self.deck = Deck(sequences=self.sequences)

    def create_new_game(self) -> tuple[List[int], List[int], List[int]]:
        self.deck.build_deck()
        self.deck.shuffle()
        self.hand1 = self.deck.deal(12)
        self.hand2 = self.deck.deal(12)
        self.trump = self.deck.deal(1)
        self.stock = list(self.deck.indices)
        self.hand1.sort()
        self.hand2.sort()
        return self.hand1, self.hand2, self.trump
