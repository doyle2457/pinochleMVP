# deck.py
from __future__ import annotations

import random
from typing import List

from card import Card


class Deck:
    """
    Deck builder for Pinochle-style decks.
    Supports:
        - 1 sequence  (24 cards)  → "half deck"
        - 2 sequences (48 cards)  → standard pinochle deck
        - 4 sequences (96 cards)  → double pinochle deck

    Cards of identical suit+rank are kept adjacent.
    """

    def __init__(self, image_dir: str = "images\\cards", sequences: int = 2):
        self.image_dir = image_dir
        self.sequences = max(1, int(sequences))  # 1, 2, or 4
        self.cards: dict[int, Card] = {}  # index → Card
        self.indices: List[int] = []  # list of indices 1..N

    # ---------------------------------------------------------
    # BUILD THE DECK
    # ---------------------------------------------------------
    def build_deck(self) -> Dict[int, Card]:
        """
        Build the deck dictionary with adjacent duplicates.
        Index order example for sequences=2:
            hearts_A_1
            hearts_A_2
            hearts_10_1
            hearts_10_2
            ...
        """
        self.cards.clear()
        self.indices.clear()

        index: int = 1

        for suit in SUITS:
            for rank in RANKS:

                # Build the image filename
                filename = os.path.join(self.image_dir, f"{suit}_{rank}.png")

                # Add N copies of this card (adjacent)
                for copy_num in range(self.sequences):
                    self.cards[index] = Card(
                        suit=suit,
                        rank=rank,
                        filename=filename,
                        copy=copy_num + 1,  # 1..N
                        index=index,
                    )
                    self.indices.append(index)
                    index += 1

        return self.cards

    # ---------------------------------------------------------
    # SHUFFLE
    # ---------------------------------------------------------
    def shuffle(self) -> List[int]:
        """Shuffle the list of card indices."""
        random.shuffle(self.indices)
        return self.indices

    # ---------------------------------------------------------
    # DEAL
    # ---------------------------------------------------------
    def deal(self, n: int) -> List[int]:
        """
        Deal n cards by index.
        Removes dealt cards from the deck.
        Note: this modifies the deck's indices list.
        Not what I expected when I wrote the method name,
        need to understand better but it works for now.
        """
        hand: List[int] = self.indices[:n]
        del self.indices[:n]
        return hand
