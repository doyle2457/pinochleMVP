"""
This module is responsible for setting the game options including
the game table style settings, the player profiles, and game rules.

The Options class is used to manage these settings
and initialize the necessary components for the application.

It will be implemented in stages, starting with the game table style settings.

Author: Doyle C Dikes.
Date: 2026-05-21
"""

import json
from pathlib import Path
from typing import Any

from PyQt5.QtWidgets import QApplication


class Options:
    def __init__(self):
        self.table_style = "plain"  # default style, can ultimately be changed by the ui options feature.
        self.player_profiles = [
            {"name": "Jack's", "type": "human"},
            {"name": "AiRulesBased", "type": "AiRulesBased"},
        ]
        self.meld_values = {
            "run_trump": 15,
            "royal_marriage": 4,
            "marriage": 2,
            "pinochle": 4,
            "double_pinochle": 30,
            "four_aces": 10,
            "four_kings": 9,
            "four_queens": 8,
            "four_jacks": 6,
            "dix": 1,
            # The meld score class needs to provide for multiples of the same meld,
            # e.g., if a player has two runs in trump, he should be able to score both runs.
            # multiple times for dix swap if a player has multiple dixes and can swap them for
            # the face-up card repeatedly.
            # There is a common rule in Pinochle where the player can swap the dix (9 of trump) for the
            # face-up card after winning the bid. My variation allows the swap when it is their
            # turn to play to the trick, not required to have won the previous trick. This allows the non-dealer
            # on playing to the first trick to do the swap. However, the player cannot immediately meld the dix since
            # he has not won a trick, which is required to play one meld. The swapped card goes to the player's,
            # hand not the meld area.
            # Note that if a player had both dixes, he could swap dix for dix repeatedly.
            # This adds an interesting strategic element to the game, one wants to be the non-dealer and have first
            # play at the initial trump card. .
        }
        self.round_values = {
            "last_trick": 1,
            "dix_swap": 1,  # This is a bonus point awarded to the player who successfully swaps the dix (9 of trump) for the face-up card after winning the bid. This rule adds an extra strategic element to the game, as players may aim to perform the dix swap to earn this bonus point.
        }
        self.cards_per_player = 12
        self.allow_dix_swap = True
        #  self.last_card_bonus = True     This rule is not standard in Pinochle and may be omitted in some variations.
        self.last_trick_bonus = True
        self.deck_count = 1
        self.use_half_deck = False

    def load_settings(self, config_path: str | Path | None = None) -> None:
        if config_path:
            settings_path = Path(config_path)
        else:
            settings_path = (
                Path(__file__).resolve().parent.parent / "game_settings.json"
            )

        if not settings_path.exists():
            return

        try:
            with settings_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError) as exc:
            print(f"Failed to load options from {settings_path}: {exc}")
            return

        self._load_from_dict(data)

    def _load_from_dict(self, data: dict[str, Any]) -> None:
        self.table_style = data.get("table_style", self.table_style)
        self.player_profiles = data.get("player_profiles", self.player_profiles)
        self.meld_values = data.get("meld_values", self.meld_values)
        self.cards_per_player = data.get("cards_per_player", self.cards_per_player)
        self.allow_dix_swap = data.get("allow_dix_swap", self.allow_dix_swap)
        #  self.last_card_bonus = data.get("last_card_bonus", self.last_card_bonus) uncomment if you want to include this rule in your game settings
        self.last_trick_bonus = data.get("last_trick_bonus", self.last_trick_bonus)
        self.deck_count = data.get("deck_count", self.deck_count)
        self.use_half_deck = data.get("use_half_deck", self.use_half_deck)

    def save_settings(self, config_path: str | Path | None = None) -> None:
        if config_path:
            settings_path = Path(config_path)
        else:
            settings_path = (
                Path(__file__).resolve().parent.parent / "game_settings.json"
            )

        try:
            with settings_path.open("w", encoding="utf-8") as handle:
                json.dump(self.__dict__, handle, indent=4)
        except OSError as exc:
            print(f"Failed to save options to {settings_path}: {exc}")
