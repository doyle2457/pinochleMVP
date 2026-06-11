from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    suit: str  # "S", "H", "D", "C"
    rank: str  # "A", "10", "K", "Q", "J", "9"

    @property
    def image_name(self) -> str:
        return f"{self.rank}{self.suit}.png"
