import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from game import Game, MeldRecord, MeldType, Player, RoundPhase, TurnStage
from saved_games import SavedGameStore


class GameRulesTests(unittest.TestCase):
    def setUp(self):
        self.game = Game(seed=17)
        self.game.start_game()

    def test_initial_deal_accounts_for_every_card_once(self):
        self.assertEqual(12, len(self.game.hand1))
        self.assertEqual(12, len(self.game.hand2))
        self.assertEqual(23, len(self.game.stock))
        self.assertEqual(1, len(self.game.trump))
        self.assertTrue(self.game.validate_invariants())
        self.assertEqual(RoundPhase.MELD_PHASE, self.game.phase)

    def test_first_trick_disallows_meld_then_winner_draws_first(self):
        leader = self.game.leader
        self.assertNotIn("declare_meld", self.game.available_actions(leader))
        self.assertTrue(self.game.play_to_trick(leader, self.game.legal_cards(leader)[0]).success)
        responder = self.game.responder
        self.assertTrue(self.game.play_to_trick(responder, self.game.legal_cards(responder)[0]).success)
        self.assertEqual(21, len(self.game.stock))
        self.assertEqual(TurnStage.LEAD, self.game.turn_stage)
        self.assertEqual(self.game.leader, self.game.eligible_melder)
        self.assertTrue(self.game.validate_invariants())

    def test_invalid_action_leaves_state_unchanged(self):
        before = (list(self.game.hand1), list(self.game.hand2), list(self.game.stock), list(self.game.trick))
        result = self.game.play_to_trick(self.game.responder, self.game.hand2[0])
        self.assertFalse(result.success)
        self.assertEqual("not_your_turn", result.code)
        self.assertEqual(before, (self.game.hand1, self.game.hand2, self.game.stock, self.game.trick))

    def test_dix_swap_scores_and_keeps_card_accounting(self):
        player = self.game.leader
        trump_suit = self.game.trump_suit
        dix = next((card_id for card_id in self.game.hands[player]
                    if self.game.deck.cards[card_id].suit == trump_suit
                    and self.game.deck.cards[card_id].rank == "9"), None)
        if dix is None:
            self.skipTest("Seed did not deal the leader a Dix; covered by controlled tests later.")
        original_trump = self.game.trump[0]
        result = self.game.swap_dix(player, dix)
        self.assertTrue(result.success)
        self.assertEqual(10, self.game.round_meld_scores[player])
        self.assertEqual([dix], self.game.trump)
        self.assertNotIn(dix, self.game.melds[player])
        self.assertNotIn(dix, self.game.hands[player])
        self.assertIn(original_trump, self.game.hands[player])
        self.assertTrue(self.game.validate_invariants())

    def test_dix_action_requires_current_player_to_hold_trump_nine(self):
        player = self.game.leader
        dix = next(
            card_id
            for card_id, card in self.game.deck.cards.items()
            if card.rank == "9" and card.suit == self.game.trump_suit
        )
        self.game.hands[player].clear()
        self.assertNotIn("swap_dix", self.game.available_actions(player))
        self.game.hands[player].append(dix)
        self.assertIn("swap_dix", self.game.available_actions(player))

    def test_meld_validator_recognizes_royal_marriage(self):
        self.game.eligible_melder = self.game.leader
        trump_suit = self.game.trump_suit
        king, queen = 5, 7  # hearts K/Q in the standard deck
        if trump_suit != "hearts":
            self.game._trump_card = 1
        self.game.hand1 = [king, queen]
        self.game.hand2 = []
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        result = self.game.declare_meld(Player.ONE, MeldType.ROYAL_MARRIAGE, [king, queen])
        self.assertTrue(result.success)
        self.assertEqual(40, self.game.round_meld_scores[Player.ONE])

    def test_scoreable_melds_identifies_multiple_meld_names_and_suits(self):
        def card_id(suit, rank):
            return next(
                card_id
                for card_id, card in self.game.deck.cards.items()
                if card.suit == suit and card.rank == rank
            )

        self.game._trump_card = card_id("hearts", "A")
        self.game.hand1 = [
            card_id("hearts", "K"),
            card_id("hearts", "Q"),
            card_id("diamonds", "K"),
            card_id("diamonds", "Q"),
            card_id("diamonds", "J"),
            card_id("spades", "Q"),
        ]
        self.game.meld1 = []
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        self.game.eligible_melder = Player.ONE
        self.game.turn_stage = TurnStage.LEAD

        melds = set(self.game.scoreable_melds(Player.ONE))
        self.assertIn((MeldType.ROYAL_MARRIAGE, "Hearts"), melds)
        self.assertIn((MeldType.MARRIAGE, "Diamonds"), melds)
        self.assertIn((MeldType.PINOCHLE, "Diamonds/Spades"), melds)

    def test_near_double_pinochle_uses_exposed_copies_in_likelihood(self):
        def face_ids(suit, rank):
            return [
                card_id
                for card_id, card in self.game.deck.cards.items()
                if card.suit == suit and card.rank == rank
            ]

        diamond_jacks = face_ids("diamonds", "J")
        spade_queens = face_ids("spades", "Q")
        self.game._trump_card = face_ids("hearts", "A")[0]
        self.game.hand1 = [*diamond_jacks, spade_queens[0]]
        self.game.meld1 = []
        self.game.hand2 = [1, 2, 3, 4, 5]
        self.game.stock = list(range(6, 16))
        self.game.won1 = []
        self.game.won2 = []

        near = next(
            meld
            for meld in self.game.near_melds(Player.ONE)
            if meld.meld_type is MeldType.DOUBLE_PINOCHLE
        )
        self.assertEqual(1, near.available_copies)
        self.assertAlmostEqual(1 / 30, near.probability)
        self.assertAlmostEqual(10, near.weighted_points)

        self.game.won2 = [spade_queens[1]]
        near = next(
            meld
            for meld in self.game.near_melds(Player.ONE)
            if meld.meld_type is MeldType.DOUBLE_PINOCHLE
        )
        self.assertEqual(1, near.exposed_copies)
        self.assertEqual(0, near.available_copies)
        self.assertEqual(0, near.probability)

    def _prepare_player_one_meld(self, meld_type, meld_cards, hand_cards):
        self.game._trump_card = 37  # clubs; test melds below are non-trump
        self.game.hand1 = list(hand_cards)
        self.game.meld1 = list(meld_cards)
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        self.game.eligible_melder = Player.ONE
        self.game.phase = RoundPhase.MELD_PHASE
        self.game.turn_stage = TurnStage.LEAD
        self.game._meld_declared_this_turn = False
        self.game._active_melds = [MeldRecord(Player.ONE, meld_type, tuple(meld_cards), 20)]

    def test_queens_around_reuses_queen_from_existing_marriage(self):
        # Diamond K/Q are already melded; the other three queens are in hand.
        self._prepare_player_one_meld(MeldType.MARRIAGE, [29, 31], [7, 19, 43])
        result = self.game.declare_meld(Player.ONE, MeldType.QUEENS_AROUND, [7, 19, 31, 43])
        self.assertTrue(result.success)
        self.assertEqual([], self.game.hand1)
        self.assertTrue({7, 19, 31, 43}.issubset(self.game.meld1))

    def test_pinochle_reuses_spade_queen_from_existing_marriage(self):
        self._prepare_player_one_meld(MeldType.MARRIAGE, [17, 19], [33])
        result = self.game.declare_meld(Player.ONE, MeldType.PINOCHLE, [19, 33])
        self.assertTrue(result.success)
        self.assertIn(33, self.game.meld1)

    def test_cannot_score_same_meld_type_with_reused_card(self):
        self._prepare_player_one_meld(MeldType.MARRIAGE, [29, 31], [32])
        result = self.game.declare_meld(Player.ONE, MeldType.MARRIAGE, [29, 32])
        self.assertFalse(result.success)
        self.assertEqual("meld_already_scored", result.code)

    def test_marriages_in_different_suits_are_distinct_melds(self):
        self._prepare_player_one_meld(MeldType.MARRIAGE, [5, 7], [17, 19])
        result = self.game.declare_meld(Player.ONE, MeldType.MARRIAGE, [17, 19])
        self.assertTrue(result.success)

    def test_cannot_rebuild_kings_around_with_duplicate_king(self):
        self._prepare_player_one_meld(MeldType.KINGS_AROUND, [5, 17, 29, 41], [18])
        result = self.game.declare_meld(Player.ONE, MeldType.KINGS_AROUND, [5, 18, 29, 41])
        self.assertFalse(result.success)
        self.assertEqual("meld_already_scored", result.code)

    def test_strict_phase_requires_follow_suit(self):
        self.game.phase = RoundPhase.TRICK_PHASE
        self.game.turn_stage = TurnStage.RESPONSE
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        self.game._trump_card = 1  # hearts
        self.game.trick = [(Player.ONE, 13)]  # spades ace
        self.game.hand2 = [15, 1]  # spades ten and hearts ace
        self.assertEqual((15,), self.game.legal_cards(Player.TWO))

    def test_rank_tie_keeps_first_card_as_winner(self):
        self.game._trump_card = 1
        self.assertFalse(self.game._beats(2, 1, "hearts"))

    def test_round_dealer_alternates(self):
        dealer = self.game.dealer
        self.game.phase = RoundPhase.ROUND_COMPLETE
        result = self.game.start_round()
        self.assertTrue(result.success)
        self.assertEqual(dealer.other, self.game.dealer)

    def test_final_draw_choice_starts_strict_phase(self):
        self.game.phase = RoundPhase.MELD_PHASE
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        self.game.turn_stage = TurnStage.LAST_DRAW_CHOICE
        self.game.stock = [3]
        self.game._trump_card = 5
        self.game.hand1 = []
        self.game.hand2 = []
        result = self.game.choose_last_draw(Player.ONE, 5)
        self.assertTrue(result.success)
        self.assertEqual(RoundPhase.TRICK_PHASE, self.game.phase)
        self.assertIn(5, self.game.hand1)
        self.assertIn(3, self.game.hand2)

    def test_final_winner_can_choose_last_stock_card(self):
        self.game.phase = RoundPhase.MELD_PHASE
        self.game.leader = Player.ONE
        self.game.responder = Player.TWO
        self.game.turn_stage = TurnStage.LAST_DRAW_CHOICE
        self.game.stock = [3]
        self.game._trump_card = 5
        self.game.hand1 = []
        self.game.hand2 = []
        result = self.game.choose_last_draw(Player.ONE, 3)
        self.assertTrue(result.success)
        self.assertIn(3, self.game.hand1)
        self.assertIn(5, self.game.hand2)
        self.assertEqual(RoundPhase.TRICK_PHASE, self.game.phase)

    def test_counter_scoring_completes_game_at_target(self):
        self.game.game_scores = {Player.ONE: 990, Player.TWO: 800}
        self.game.won1 = [1]  # ace: ten counter points
        self.game.won2 = []
        self.game.round_meld_scores = {Player.ONE: 0, Player.TWO: 0}
        self.game._finish_round()
        self.assertEqual(1000, self.game.game_scores[Player.ONE])
        self.assertEqual(RoundPhase.GAME_COMPLETE, self.game.phase)
        self.assertEqual((Player.ONE,), self.game.shared_winners)

    def test_saved_game_round_trip_preserves_complete_state(self):
        self.game.play_to_trick(self.game.leader, self.game.legal_cards(self.game.leader)[0])
        snapshot = self.game.to_dict()
        restored = Game.from_dict(snapshot)
        self.assertEqual(snapshot, restored.to_dict())
        self.assertTrue(restored.validate_invariants())

    def test_saved_game_store_lists_loads_and_deletes_named_games(self):
        with TemporaryDirectory() as directory:
            store = SavedGameStore(Path(directory))
            store.save("alternate play", self.game)
            self.assertEqual(["alternate play"], [item["name"] for item in store.list()])
            self.assertEqual(self.game.to_dict(), store.load("alternate play").to_dict())
            store.delete("alternate play")
            self.assertEqual([], store.list())

    def test_corrupt_snapshot_with_duplicate_card_is_rejected(self):
        snapshot = self.game.to_dict()
        snapshot["zones"]["hand2"][0] = snapshot["zones"]["hand1"][0]
        with self.assertRaises(ValueError):
            Game.from_dict(snapshot)


if __name__ == "__main__":
    unittest.main()
