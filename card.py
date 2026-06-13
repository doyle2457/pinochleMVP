# card.py
from typing import Optional


class Card:
    """
    Simple data container for a Pinochle card.
    """

    def __init__(
        self,
        suit: str,
        rank: str,
        filename: str,
        copy: int = 1,
        index: Optional[int] = None,
    ):
        self.suit = suit
        self.rank = rank
        self.filename = filename
        self.copy = copy  # 1..N (sequence number)
        self.index = index  # global deck index
        print(f"Card __init__, self.copy = {self.copy}, self.index = {self.index}")

    def __repr__(self):
        return f"{self.rank} of {self.suit} (copy {self.copy})"
