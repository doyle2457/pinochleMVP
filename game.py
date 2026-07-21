"""Rules engine for a two-player Pinochle game.

The controller is deliberately independent of PyQt.  UI code should call its
actions, inspect the public state, and refresh its panels after a successful
``ActionResult``.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from enum import Enum, IntEnum
from itertools import combinations
from typing import Iterable, Optional

from deck import Deck


class Player(IntEnum):
    ONE = 1
    TWO = 2

    @property
    def display_name(self) -> str:
        """Return the player name shown by the table UI."""
        return f"Player {self.value}"

    @property
    def other(self) -> "Player":
        return Player.TWO if self is Player.ONE else Player.ONE


class RoundPhase(str, Enum):
    MELD_PHASE = "meld_phase"
    TRICK_PHASE = "trick_phase"
    ROUND_COMPLETE = "round_complete"
    GAME_COMPLETE = "game_complete"


class TurnStage(str, Enum):
    LEAD = "lead"
    RESPONSE = "response"
    LAST_DRAW_CHOICE = "last_draw_choice"
    ROUND_COMPLETE = "round_complete"


class MeldType(str, Enum):
    RUN = "run"
    MARRIAGE = "marriage"
    ROYAL_MARRIAGE = "royal_marriage"
    ACES_AROUND = "aces_around"
    KINGS_AROUND = "kings_around"
    QUEENS_AROUND = "queens_around"
    JACKS_AROUND = "jacks_around"
    PINOCHLE = "pinochle"
    DOUBLE_PINOCHLE = "double_pinochle"
    DIX = "dix"


MELD_POINTS = {
    MeldType.RUN: 150,
    MeldType.MARRIAGE: 20,
    MeldType.ROYAL_MARRIAGE: 40,
    MeldType.ACES_AROUND: 100,
    MeldType.KINGS_AROUND: 80,
    MeldType.QUEENS_AROUND: 60,
    MeldType.JACKS_AROUND: 40,
    MeldType.PINOCHLE: 40,
    MeldType.DOUBLE_PINOCHLE: 300,
    MeldType.DIX: 10,
}
RANK_STRENGTH = {"9": 0, "J": 1, "Q": 2, "K": 3, "10": 4, "A": 5}
COUNTER_RANKS = {"A", "10", "K"}


@dataclass(frozen=True)
class ActionResult:
    success: bool
    code: str = "ok"
    message: str = ""


@dataclass
class MeldRecord:
    player: Player
    meld_type: MeldType
    card_ids: tuple[int, ...]
    points: int


@dataclass(frozen=True)
class NearMeld:
    """A four/five-card meld that is short exactly one card."""

    meld_type: MeldType
    suit_label: str
    missing_suit: str
    missing_rank: str
    exposed_copies: int
    available_copies: int
    probability: float
    weighted_points: float


class Game:
    """Stateful controller for a complete, two-player Pinochle game."""

    def __init__(self, sequences: int = 2, seed: Optional[int] = None) -> None:
        if sequences != 2:
            raise ValueError("Two-player Pinochle requires the standard 48-card deck.")
        self.sequences = sequences
        self.rng = random.Random(seed)
        self.deck = Deck(sequences=sequences)
        self.dealer: Optional[Player] = None
        self.phase = RoundPhase.ROUND_COMPLETE
        self.turn_stage = TurnStage.ROUND_COMPLETE
        self.leader: Optional[Player] = None
        self.responder: Optional[Player] = None
        self.previous_trick_winner: Optional[Player] = None
        self.eligible_melder: Optional[Player] = None
        self._player_started: set[Player] = set()
        self._meld_declared_this_turn = False
        self._trump_card: Optional[int] = None
        self._active_melds: list[MeldRecord] = []
        self.broken_melds: set[tuple[Player, MeldType, tuple[int, ...]]] = set()
        self.game_scores = {Player.ONE: 0, Player.TWO: 0}
        self.round_meld_scores = {Player.ONE: 0, Player.TWO: 0}
        self.round_counter_scores = {Player.ONE: 0, Player.TWO: 0}
        self.shared_winners: tuple[Player, ...] = ()
        self._reset_zones()

    # Compatibility aliases retained for the current UI.
    @property
    def hands(self) -> dict[Player, list[int]]:
        return {Player.ONE: self.hand1, Player.TWO: self.hand2}

    @property
    def melds(self) -> dict[Player, list[int]]:
        return {Player.ONE: self.meld1, Player.TWO: self.meld2}

    @property
    def won(self) -> dict[Player, list[int]]:
        return {Player.ONE: self.won1, Player.TWO: self.won2}

    @property
    def trump(self) -> list[int]:
        return [] if self._trump_card is None else [self._trump_card]

    @property
    def active_melds(self) -> tuple[MeldRecord, ...]:
        return tuple(self._active_melds)

    def card_zone(self, card_id: int) -> str:
        """Return the single current location of a card, for UI and tests."""
        if card_id in self.hand1:
            return "hand1"
        if card_id in self.hand2:
            return "hand2"
        if card_id in self.meld1:
            return "meld1"
        if card_id in self.meld2:
            return "meld2"
        if any(played_id == card_id for _, played_id in self.trick):
            return "trick"
        if card_id in self.won1:
            return "won1"
        if card_id in self.won2:
            return "won2"
        if card_id in self.stock:
            return "stock"
        if card_id == self._trump_card:
            return "trump"
        raise ValueError(f"Card {card_id} is not in a game zone.")

    def validate_invariants(self) -> bool:
        """Check that every deck card appears exactly once across all zones."""
        zones = [self.hand1, self.hand2, self.meld1, self.meld2, self.stock, self.won1, self.won2]
        card_ids = [card_id for zone in zones for card_id in zone]
        card_ids.extend(card_id for _, card_id in self.trick)
        if self._trump_card is not None:
            card_ids.append(self._trump_card)
        return len(card_ids) == len(set(card_ids)) == len(self.deck.cards)

    def _reset_zones(self) -> None:
        self.hand1: list[int] = []
        self.hand2: list[int] = []
        self.meld1: list[int] = []
        self.meld2: list[int] = []
        self.trick: list[tuple[Player, int]] = []
        self.stock: list[int] = []
        self.won1: list[int] = []
        self.won2: list[int] = []

    def start_game(self) -> ActionResult:
        """Reset cumulative scores and deal the first round with random dealer."""
        self.game_scores = {Player.ONE: 0, Player.TWO: 0}
        self.shared_winners = ()
        self.dealer = self.rng.choice((Player.ONE, Player.TWO))
        return self._deal_round()

    def start_round(self) -> ActionResult:
        """Deal the next round, alternating the dealer after the first round."""
        if self.dealer is None:
            return self.start_game()
        if self.phase not in {RoundPhase.ROUND_COMPLETE, RoundPhase.GAME_COMPLETE}:
            return self._error("round_in_progress", "Finish the current round before dealing again.")
        if self.phase is RoundPhase.GAME_COMPLETE:
            return self._error("game_complete", "Start a new game to deal after game completion.")
        self.dealer = self.dealer.other
        return self._deal_round()

    def create_new_game(self) -> tuple[list[int], list[int], list[int]]:
        """Backward-compatible UI entry point for a fresh game."""
        self.start_game()
        return self.hand1, self.hand2, self.trump

    def to_dict(self) -> dict:
        """Return a JSON-compatible snapshot of every piece of game state."""
        player = lambda value: None if value is None else value.value
        scores = lambda values: {str(key.value): value for key, value in values.items()}
        return {
            "format_version": 1,
            "sequences": self.sequences,
            "rng_state": self.rng.getstate(),
            "dealer": player(self.dealer),
            "phase": self.phase.value,
            "turn_stage": self.turn_stage.value,
            "leader": player(self.leader),
            "responder": player(self.responder),
            "previous_trick_winner": player(self.previous_trick_winner),
            "eligible_melder": player(self.eligible_melder),
            "player_started": [value.value for value in sorted(self._player_started)],
            "meld_declared_this_turn": self._meld_declared_this_turn,
            "trump_card": self._trump_card,
            "active_melds": [
                {"player": record.player.value, "meld_type": record.meld_type.value,
                 "card_ids": list(record.card_ids), "points": record.points}
                for record in self._active_melds
            ],
            "broken_melds": [
                {"player": owner.value, "meld_type": meld_type.value, "card_ids": list(card_ids)}
                for owner, meld_type, card_ids in self.broken_melds
            ],
            "game_scores": scores(self.game_scores),
            "round_meld_scores": scores(self.round_meld_scores),
            "round_counter_scores": scores(self.round_counter_scores),
            "shared_winners": [value.value for value in self.shared_winners],
            "zones": {
                "hand1": self.hand1, "hand2": self.hand2,
                "meld1": self.meld1, "meld2": self.meld2,
                "trick": [[owner.value, card_id] for owner, card_id in self.trick],
                "stock": self.stock, "won1": self.won1, "won2": self.won2,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        """Recreate a game from a snapshot, rejecting corrupt/incompatible data."""
        if data.get("format_version") != 1:
            raise ValueError("Unsupported saved-game format.")
        game = cls(sequences=int(data["sequences"]))
        game.deck.build_deck()
        as_player = lambda value: None if value is None else Player(int(value))
        as_scores = lambda values: {Player.ONE: int(values["1"]), Player.TWO: int(values["2"])}
        def as_tuple(value):
            return tuple(as_tuple(item) for item in value) if isinstance(value, list) else value

        game.rng.setstate(as_tuple(data["rng_state"]))
        game.dealer = as_player(data["dealer"])
        game.phase = RoundPhase(data["phase"])
        game.turn_stage = TurnStage(data["turn_stage"])
        game.leader = as_player(data["leader"])
        game.responder = as_player(data["responder"])
        game.previous_trick_winner = as_player(data["previous_trick_winner"])
        game.eligible_melder = as_player(data["eligible_melder"])
        game._player_started = {Player(int(value)) for value in data["player_started"]}
        game._meld_declared_this_turn = bool(data["meld_declared_this_turn"])
        game._trump_card = data["trump_card"]
        game._active_melds = [
            MeldRecord(Player(int(item["player"])), MeldType(item["meld_type"]),
                       tuple(int(card_id) for card_id in item["card_ids"]), int(item["points"]))
            for item in data["active_melds"]
        ]
        game.broken_melds = {
            (Player(int(item["player"])), MeldType(item["meld_type"]),
             tuple(int(card_id) for card_id in item["card_ids"]))
            for item in data["broken_melds"]
        }
        game.game_scores = as_scores(data["game_scores"])
        game.round_meld_scores = as_scores(data["round_meld_scores"])
        game.round_counter_scores = as_scores(data["round_counter_scores"])
        game.shared_winners = tuple(Player(int(value)) for value in data["shared_winners"])
        zones = data["zones"]
        for name in ("hand1", "hand2", "meld1", "meld2", "stock", "won1", "won2"):
            setattr(game, name, [int(card_id) for card_id in zones[name]])
        game.trick = [(Player(int(owner)), int(card_id)) for owner, card_id in zones["trick"]]
        if not game.validate_invariants():
            raise ValueError("Saved game has invalid or duplicate card locations.")
        all_ids = set(range(1, len(game.deck.cards) + 1))
        located_ids = set(game.hand1 + game.hand2 + game.meld1 + game.meld2 + game.stock + game.won1 + game.won2)
        located_ids.update(card_id for _, card_id in game.trick)
        if game._trump_card is not None:
            located_ids.add(game._trump_card)
        if located_ids != all_ids:
            raise ValueError("Saved game references invalid card IDs.")
        game.deck.indices = list(game.stock)
        return game

    def _deal_round(self) -> ActionResult:
        self.deck.build_deck()
        self.rng.shuffle(self.deck.indices)
        self._reset_zones()
        self._active_melds.clear()
        self.broken_melds.clear()
        self.round_meld_scores = {Player.ONE: 0, Player.TWO: 0}
        self.round_counter_scores = {Player.ONE: 0, Player.TWO: 0}
        self.hand1 = self.deck.deal(12)
        self.hand2 = self.deck.deal(12)
        self._trump_card = self.deck.deal(1)[0]
        self.stock = list(self.deck.indices)
        self.hand1.sort()
        self.hand2.sort()
        self.phase = RoundPhase.MELD_PHASE
        self.leader = self.dealer.other
        self.responder = self.leader.other
        self.previous_trick_winner = None
        self.eligible_melder = None
        self.turn_stage = TurnStage.LEAD
        self._player_started.clear()
        self._meld_declared_this_turn = False
        return ActionResult(
            True, message=f"Round started; {self.leader.display_name} leads."
        )

    def available_actions(self, player: Player) -> tuple[str, ...]:
        if self.phase in {RoundPhase.ROUND_COMPLETE, RoundPhase.GAME_COMPLETE}:
            return ()
        actions: list[str] = []
        if self._can_swap_dix(player):
            actions.append("swap_dix")
        if self._can_declare_meld(player):
            actions.append("declare_meld")
        if self._is_current_player(player):
            actions.append("play_to_trick")
        if self.turn_stage is TurnStage.LAST_DRAW_CHOICE and player is self.leader:
            actions.append("choose_last_draw")
        return tuple(actions)

    def legal_cards(self, player: Player) -> tuple[int, ...]:
        """Return cards that may legally be played to the current trick."""
        if not self._is_current_player(player):
            return ()
        cards = list(self.hands[player]) + list(self.melds[player])
        if self.phase is RoundPhase.MELD_PHASE or self.turn_stage is TurnStage.LEAD:
            return tuple(cards)
        lead_card = self.trick[0][1]
        led_suit = self._card(lead_card).suit
        suited = [card_id for card_id in cards if self._card(card_id).suit == led_suit]
        if suited:
            winners = [card_id for card_id in suited if self._beats(card_id, lead_card, led_suit)]
            return tuple(winners or suited)
        trumps = [card_id for card_id in cards if self._card(card_id).suit == self.trump_suit]
        if trumps:
            winners = [card_id for card_id in trumps if self._beats(card_id, lead_card, led_suit)]
            return tuple(winners or trumps)
        return tuple(cards)

    def meld_options(self, player: Player, card_ids: Iterable[int]) -> tuple[MeldType, ...]:
        """Return every meld type formed by these cards in the current round."""
        ids = tuple(card_ids)
        return tuple(
            meld_type for meld_type in MeldType
            if meld_type is not MeldType.DIX and self._validate_meld(meld_type, ids)[0]
        )

    def scoreable_melds(self, player: Player) -> tuple[tuple[MeldType, str], ...]:
        """Return distinct meld types and suit labels the player can score now."""
        if not self._can_declare_meld(player):
            return ()
        hand = set(self.hands[player])
        owned = tuple(self.hands[player] + self.melds[player])
        scored_signatures = {
            self._meld_signature(record.meld_type, record.card_ids)
            for record in self._active_melds
            if record.player is player
        } | {
            self._meld_signature(meld_type, card_ids)
            for meld_player, meld_type, card_ids in self.broken_melds
            if meld_player is player
        }
        found = {}
        for size in (2, 4, 5):
            for card_ids in combinations(owned, size):
                if not hand.intersection(card_ids):
                    continue
                for meld_type in self.meld_options(player, card_ids):
                    signature = self._meld_signature(meld_type, card_ids)
                    if signature in scored_signatures:
                        continue
                    suits = {self._card(card_id).suit for card_id in card_ids}
                    if meld_type in {MeldType.PINOCHLE, MeldType.DOUBLE_PINOCHLE}:
                        suit_label = "Diamonds/Spades"
                    elif meld_type in {
                        MeldType.ACES_AROUND,
                        MeldType.KINGS_AROUND,
                        MeldType.QUEENS_AROUND,
                        MeldType.JACKS_AROUND,
                    }:
                        suit_label = "All suits"
                    else:
                        suit_label = next(iter(suits)).title()
                    found.setdefault((meld_type, suit_label), card_ids)
        return tuple(found)

    def near_melds(self, player: Player) -> tuple[NearMeld, ...]:
        """Return near melds using the requested exposed-card probability heuristic.

        The heuristic is ``available copies / (2 * unknown cards)``, where
        unknown cards are the stock plus the other player's concealed hand.
        It is useful as a relative hint score, but it is not an exact draw
        probability because draw order and the stock/opponent-hand split are
        not modeled.
        """
        if self.phase is not RoundPhase.MELD_PHASE:
            return ()
        owned_faces = Counter(
            (self._card(card_id).suit, self._card(card_id).rank)
            for card_id in self.hands[player] + self.melds[player]
        )
        suits = ("hearts", "spades", "diamonds", "clubs")
        patterns = []
        if self.trump_suit is not None:
            patterns.append((
                MeldType.RUN,
                self.trump_suit.title(),
                Counter((self.trump_suit, rank) for rank in ("A", "10", "K", "Q", "J")),
            ))
        for meld_type, rank in (
            (MeldType.ACES_AROUND, "A"),
            (MeldType.KINGS_AROUND, "K"),
            (MeldType.QUEENS_AROUND, "Q"),
            (MeldType.JACKS_AROUND, "J"),
        ):
            patterns.append((
                meld_type,
                "All suits",
                Counter((suit, rank) for suit in suits),
            ))
        patterns.append((
            MeldType.DOUBLE_PINOCHLE,
            "Diamonds/Spades",
            Counter({("diamonds", "J"): 2, ("spades", "Q"): 2}),
        ))

        already_scored = {
            record.meld_type
            for record in self._active_melds
            if record.player is player
        } | {
            meld_type
            for meld_player, meld_type, _ in self.broken_melds
            if meld_player is player
        }
        exposed_ids = (
            self.won1
            + self.won2
            + self.melds[player.other]
            + self.trump
            + [card_id for _, card_id in self.trick]
        )
        unknown_cards = len(self.stock) + len(self.hands[player.other])
        near = []
        for meld_type, suit_label, requirements in patterns:
            if meld_type in already_scored:
                continue
            missing = list((requirements - owned_faces).elements())
            if len(missing) != 1:
                continue
            missing_suit, missing_rank = missing[0]
            exposed_copies = sum(
                1
                for card_id in exposed_ids
                if (self._card(card_id).suit, self._card(card_id).rank)
                == (missing_suit, missing_rank)
            )
            known_owned_copies = owned_faces[(missing_suit, missing_rank)]
            available_copies = max(
                0, self.sequences - known_owned_copies - exposed_copies
            )
            probability = (
                available_copies / (2 * unknown_cards) if unknown_cards else 0.0
            )
            near.append(NearMeld(
                meld_type=meld_type,
                suit_label=suit_label,
                missing_suit=missing_suit.title(),
                missing_rank=missing_rank,
                exposed_copies=exposed_copies,
                available_copies=available_copies,
                probability=probability,
                weighted_points=probability * MELD_POINTS[meld_type],
            ))
        return tuple(near)

    @property
    def trump_suit(self) -> Optional[str]:
        if self._trump_card is not None:
            return self._card(self._trump_card).suit
        dix = next((meld for meld in self._active_melds if meld.meld_type is MeldType.DIX), None)
        return self._card(dix.card_ids[0]).suit if dix else None

    def swap_dix(self, player: Player, card_id: int) -> ActionResult:
        if not self._can_swap_dix(player):
            return self._error("dix_not_available", "A dix swap is not available now.")
        card = self._card(card_id)
        if card_id not in self.hands[player] or card.rank != "9" or card.suit != self.trump_suit:
            return self._error("invalid_dix", "Choose the nine of the trump suit from your hand.")
        self.hands[player].remove(card_id)
        trump_card = self._trump_card
        self.hands[player].append(trump_card)
        self.hands[player].sort()
        # The Dix replaces the original face-up trump card and remains the
        # final face-up draw; the original trump card goes into the hand.
        self._trump_card = card_id
        self._active_melds.append(MeldRecord(player, MeldType.DIX, (card_id,), MELD_POINTS[MeldType.DIX]))
        self.round_meld_scores[player] += MELD_POINTS[MeldType.DIX]
        self._player_started.add(player)
        return ActionResult(True, message="Dix swapped for the trump card.")

    def declare_meld(self, player: Player, meld_type: MeldType, card_ids: Iterable[int]) -> ActionResult:
        ids = tuple(card_ids)
        if not self._can_declare_meld(player):
            return self._error("meld_not_available", "Only the eligible trick winner may meld before leading.")
        if meld_type is MeldType.DIX:
            return self._error("dix_requires_swap", "Score Dix by performing a dix swap.")
        if not ids or len(ids) != len(set(ids)):
            return self._error("invalid_cards", "A meld needs unique card IDs.")
        owned = set(self.hands[player]) | set(self.melds[player])
        if not set(ids).issubset(owned):
            return self._error("card_not_owned", "All meld cards must belong to the player.")
        if set(ids).issubset(self.melds[player]):
            return self._error("needs_hand_card", "A new meld must include a card from the hand.")
        valid, actual_type = self._validate_meld(meld_type, ids)
        if not valid:
            return self._error("invalid_meld", "Those cards do not form the declared meld.")
        new_signature = self._meld_signature(actual_type, ids)
        scored_signatures = {
            self._meld_signature(record.meld_type, record.card_ids)
            for record in self._active_melds if record.player is player
        } | {
            self._meld_signature(broken_type, broken_ids)
            for broken_player, broken_type, broken_ids in self.broken_melds
            if broken_player is player
        }
        if new_signature in scored_signatures:
            return self._error(
                "meld_already_scored",
                "That same meld has already been scored using equivalent card copies.",
            )
        points = MELD_POINTS[actual_type]
        for card_id in ids:
            if card_id in self.hands[player]:
                self.hands[player].remove(card_id)
                self.melds[player].append(card_id)
        self._active_melds.append(MeldRecord(player, actual_type, ids, points))
        self.round_meld_scores[player] += points
        self._meld_declared_this_turn = True
        self._player_started.add(player)
        return ActionResult(True, message=f"{actual_type.value} scored for {points} points.")

    def play_to_trick(self, player: Player, card_id: int) -> ActionResult:
        if not self._is_current_player(player):
            return self._error("not_your_turn", "It is not this player's turn to play.")
        if card_id not in self.legal_cards(player):
            return self._error("illegal_card", "That card is not legal for this trick.")
        self._remove_played_card(player, card_id)
        self.trick.append((player, card_id))
        self._player_started.add(player)
        if self.turn_stage is TurnStage.LEAD:
            self.turn_stage = TurnStage.RESPONSE
            return ActionResult(True, message="Lead accepted; waiting for the response.")
        return self._resolve_trick()

    def choose_last_draw(self, player: Player, card_id: int) -> ActionResult:
        if self.turn_stage is not TurnStage.LAST_DRAW_CHOICE or player is not self.leader:
            return self._error("choice_not_available", "Only the final trick winner may choose now.")
        choices = list(self.stock) + self.trump
        if card_id not in choices:
            return self._error("invalid_last_draw", "Choose the remaining stock card or trump card.")
        other = player.other
        choices.remove(card_id)
        self.hands[player].append(card_id)
        if choices:
            self.hands[other].append(choices[0])
        self.stock.clear()
        self._trump_card = None
        self._begin_trick_phase()
        return ActionResult(True, message="Final draw complete; strict trick play begins.")

    def _resolve_trick(self) -> ActionResult:
        lead_player, lead_card = self.trick[0]
        response_player, response_card = self.trick[1]
        winner = response_player if self._beats(response_card, lead_card, self._card(lead_card).suit) else lead_player
        self.won[winner].extend((lead_card, response_card))
        self.trick.clear()
        self.previous_trick_winner = winner
        self.leader = winner
        self.responder = winner.other
        self.eligible_melder = None
        self._player_started.clear()
        self._meld_declared_this_turn = False

        if self.phase is RoundPhase.MELD_PHASE:
            if len(self.stock) >= 2:
                self.hands[winner].append(self.stock.pop(0))
                self.hands[winner.other].append(self.stock.pop(0))
                self.hands[winner].sort()
                self.hands[winner.other].sort()
                self.eligible_melder = winner
                self.turn_stage = TurnStage.LEAD
                return ActionResult(
                    True, message=f"{winner.display_name} won and draws first."
                )
            if len(self.stock) == 1 and self._trump_card is not None:
                self.turn_stage = TurnStage.LAST_DRAW_CHOICE
                return ActionResult(
                    True, message=f"{winner.display_name} chooses the final draw."
                )
            # Defensive fallback for a state with no face-up trump card.
            recipient = min((Player.ONE, Player.TWO), key=lambda p: len(self.hands[p]) + len(self.melds[p]))
            self.hands[recipient].append(self.stock.pop(0))
            self._begin_trick_phase()
            return ActionResult(True, message="Final stock card drawn; strict trick play begins.")

        if not self.hand1 and not self.hand2:
            self._finish_round()
            return ActionResult(True, message="Round complete.")
        self.turn_stage = TurnStage.LEAD
        return ActionResult(
            True, message=f"{winner.display_name} won the trick and leads."
        )

    def _begin_trick_phase(self) -> None:
        for player in (Player.ONE, Player.TWO):
            self.hands[player].extend(self.melds[player])
            self.hands[player].sort()
            self.melds[player].clear()
        self._active_melds.clear()
        self.phase = RoundPhase.TRICK_PHASE
        self.eligible_melder = None
        self.turn_stage = TurnStage.LEAD
        self._player_started.clear()

    def _finish_round(self) -> None:
        for player in (Player.ONE, Player.TWO):
            self.round_counter_scores[player] = sum(
                10 for card_id in self.won[player] if self._card(card_id).rank in COUNTER_RANKS
            )
            self.game_scores[player] += self.round_meld_scores[player] + self.round_counter_scores[player]
        high = max(self.game_scores.values())
        qualifiers = tuple(player for player, score in self.game_scores.items() if score == high and score >= 1000)
        self.shared_winners = qualifiers
        self.phase = RoundPhase.GAME_COMPLETE if qualifiers else RoundPhase.ROUND_COMPLETE
        self.turn_stage = TurnStage.ROUND_COMPLETE

    def _remove_played_card(self, player: Player, card_id: int) -> None:
        if card_id in self.hands[player]:
            self.hands[player].remove(card_id)
            return
        broken_records = [
            record for record in self._active_melds
            if record.player is player and card_id in record.card_ids
        ]
        for record in broken_records:
            self._active_melds.remove(record)
            self.broken_melds.add((player, record.meld_type, tuple(sorted(record.card_ids))))
        if card_id in self.melds[player]:
            self.melds[player].remove(card_id)
        still_melded = {
            meld_card
            for record in self._active_melds if record.player is player
            for meld_card in record.card_ids
        }
        for meld_card in list(self.melds[player]):
            if meld_card not in still_melded:
                self.melds[player].remove(meld_card)
                self.hands[player].append(meld_card)
        self.hands[player].sort()

    def _can_swap_dix(self, player: Player) -> bool:
        return (
            self.phase is RoundPhase.MELD_PHASE
            and self._trump_card is not None
            and self._is_current_player(player)
            and player not in self._player_started
            and any(
                self._card(card_id).rank == "9"
                and self._card(card_id).suit == self.trump_suit
                for card_id in self.hands[player]
            )
        )

    def _can_declare_meld(self, player: Player) -> bool:
        return (
            self.phase is RoundPhase.MELD_PHASE
            and self.turn_stage is TurnStage.LEAD
            and player is self.leader
            and player is self.eligible_melder
            and not self._meld_declared_this_turn
        )

    def _is_current_player(self, player: Player) -> bool:
        return (
            (self.turn_stage is TurnStage.LEAD and player is self.leader)
            or (self.turn_stage is TurnStage.RESPONSE and player is self.responder)
        )

    def _validate_meld(self, requested: MeldType, ids: tuple[int, ...]) -> tuple[bool, MeldType]:
        cards = [self._card(card_id) for card_id in ids]
        suits = {card.suit for card in cards}
        ranks = [card.rank for card in cards]
        if requested is MeldType.RUN:
            return (len(ids) == 5 and suits == {self.trump_suit} and set(ranks) == {"A", "10", "K", "Q", "J"}, requested)
        if requested in {MeldType.MARRIAGE, MeldType.ROYAL_MARRIAGE}:
            if len(ids) != 2 or len(suits) != 1 or set(ranks) != {"K", "Q"}:
                return False, requested
            actual = MeldType.ROYAL_MARRIAGE if next(iter(suits)) == self.trump_suit else MeldType.MARRIAGE
            return (requested is actual, actual)
        around = {
            MeldType.ACES_AROUND: "A", MeldType.KINGS_AROUND: "K",
            MeldType.QUEENS_AROUND: "Q", MeldType.JACKS_AROUND: "J",
        }
        if requested in around:
            return (len(ids) == 4 and ranks.count(around[requested]) == 4 and len(suits) == 4, requested)
        if requested is MeldType.PINOCHLE:
            return (len(ids) == 2 and {(card.suit, card.rank) for card in cards} == {("diamonds", "J"), ("spades", "Q")}, requested)
        if requested is MeldType.DOUBLE_PINOCHLE:
            pairs = [(card.suit, card.rank) for card in cards]
            return (len(ids) == 4 and pairs.count(("diamonds", "J")) == 2 and pairs.count(("spades", "Q")) == 2, requested)
        return False, requested

    def _beats(self, candidate_id: int, current_id: int, led_suit: str) -> bool:
        candidate = self._card(candidate_id)
        current = self._card(current_id)
        trump = self.trump_suit
        if candidate.suit == trump and current.suit != trump:
            return True
        if candidate.suit != current.suit:
            return False
        return RANK_STRENGTH[candidate.rank] > RANK_STRENGTH[current.rank]

    def _card(self, card_id: int):
        return self.deck.cards[card_id]

    def _meld_signature(self, meld_type: MeldType, card_ids: Iterable[int]):
        """Identify a meld by type and card faces, ignoring duplicate-copy IDs."""
        faces = tuple(sorted((self._card(card_id).suit, self._card(card_id).rank) for card_id in card_ids))
        return meld_type, faces

    @staticmethod
    def _error(code: str, message: str) -> ActionResult:
        return ActionResult(False, code, message)
