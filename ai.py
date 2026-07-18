"""Extension point for computer-controlled Pinochle players."""

from __future__ import annotations

from typing import Protocol

from game import ActionResult, Game, Player


class PlayerStrategy(Protocol):
    """Choose one legal controller action for a player.

    Implementations must call ``Game`` public action methods and may not mutate
    controller state directly.
    """

    def take_turn(self, game: Game, player: Player) -> ActionResult: ...
