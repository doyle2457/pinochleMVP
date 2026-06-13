# game.py
from __future__ import annotations

from typing import List

from deck import Deck


class Game:
    """
    Game controller for a two‑handed Pinochle game.

    Responsibilities:
        - Build and shuffle the deck
        - Deal 12 cards to each player (24 total)
        - Maintain state lists for later phases:
            meld, tricks, stock, trump, won cards, etc.
    """

    def __init__(self, sequences: int = 2) -> None:
        # Deck configuration (1, 2, or 4 sequences)
        self.sequences: int = sequences

        # Player hands (list of card indices)
        self.hand1: List[int] = []
        self.hand2: List[int] = []

        # Future game state lists
        self.meld1: List[int] = []
        self.meld2: List[int] = []
        self.trick: List[int] = []
        self.stock: List[int] = []
        self.trump_designator: List[int] = []
        self.won1: List[int] = []
        self.won2: List[int] = []

        # Deck object
        self.deck: Deck = Deck(sequences=self.sequences)

    # ---------------------------------------------------------
    # CREATE NEW GAME
    # ---------------------------------------------------------
    def create_new_game(self) -> None:
        """
        Create a new game:
            - Build the deck dictionary
            - Shuffle the card indices
            - Deal 12 cards to each player
        """
        # Build deck (dict[int, Card])
        self.deck.build_deck()

        # Shuffle indices (list[int])
        shuffled: List[int] = self.deck.shuffle()

        # Deal 12 cards to each hand
        self.hand1 = shuffled[:12]
        self.hand2 = shuffled[12:24]

        # Remove dealt cards from deck.indices
        del self.deck.indices[:24]
        print_hands()

    #   self.print_hands() looked good at this point,
    #   but we'll call it from the UI later when we have card images to show.

    # ---------------------------------------------------------
    # DEBUG / INSPECTION HELPERS
    # ---------------------------------------------------------
    def print_hands(self) -> None:
        """Print both hands with card details."""
        print("\nPlayer 1 Hand:")
        for idx in self.hand1:
            print(f"  {idx}: {self.deck.cards[idx].suit} {self.deck.cards[idx].rank}")

        print("\nPlayer 2 Hand:")
        for idx in self.hand2:
            print(f"  {idx}: {self.deck.cards[idx]}")
