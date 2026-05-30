import os
import random
from .card import Card

SUITS = ["hearts", "spades", "diamonds", "clubs"]
RANKS = ["A", "10", "K", "Q", "J", "9"]


class Deck:
    def __init__(self, image_dir="images/cards", deck_count=1, use_half_deck=False):
        self.cards = []
        self.deck_count = max(1, int(deck_count))
        self.use_half_deck = bool(use_half_deck)
        self.load_cards(image_dir)

    def load_cards(self, image_dir):
        copies = 1 if self.use_half_deck else 2
        for _ in range(self.deck_count):
            for suit in SUITS:
                for rank in RANKS:
                    filename = f"{image_dir}/{suit}_{rank}.png"
                    if os.path.exists(filename):
                        for _ in range(copies):
                            self.cards.append(Card(suit, rank, filename))

    def shuffle(self, rng):
        shuffled_cards = random.randint(1, 48)
        rng.shuffle(self.cards)

    def deal(self, n):
        hand = self.cards[:n]
        del self.cards[:n]
        return hand
