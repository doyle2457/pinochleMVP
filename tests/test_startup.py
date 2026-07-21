import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from game import Player
from mainwindow import MainWindow
from card_panel import TRICK_TARGET_MIN_WIDTH


class ApplicationStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_starts_outside_project_directory(self):
        original_directory = Path.cwd()
        with TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                window = MainWindow()
                window.start_new_game()
                self.assertEqual("Trickwise Pinochle", window.windowTitle())
                self.assertTrue(all(Path(card.filename).is_file() for card in window.game.deck.cards.values()))
                window.close()
            finally:
                os.chdir(original_directory)

    def test_card_panels_scale_with_available_window_height(self):
        window = MainWindow()
        window.ui.centralwidget.resize(1600, 900)
        window.cpHand1.resize(1400, window.cpHand1.height())
        window.cpHand2.resize(1400, window.cpHand2.height())
        window._resize_card_panels()
        compact_height = window.cpHand1._preferred_card_height
        window.ui.centralwidget.resize(3000, 1900)
        window.cpHand1.resize(2700, window.cpHand1.height())
        window.cpHand2.resize(2700, window.cpHand2.height())
        window._resize_card_panels()
        expanded_height = window.cpHand1._preferred_card_height
        panels = (
            window.cpHand1, window.cpMeld1, window.cpWon1, window.cpTrick1,
            window.cpHand2, window.cpMeld2, window.cpWon2, window.cpTrick2,
            window.cpStock, window.cpTrump,
        )
        self.assertGreater(expanded_height, compact_height)
        self.assertEqual({expanded_height}, {panel._preferred_card_height for panel in panels})
        expected_width = round(expanded_height * 100 / 142)
        for panel in (
            window.cpWon1, window.cpWon2, window.cpStock, window.cpTrump,
            window.cpTrick1, window.cpTrick2,
        ):
            self.assertGreaterEqual(panel.minimumWidth(), expected_width)
        window.close()

    def test_scoring_event_appears_only_in_scoring_players_hint(self):
        window = MainWindow()
        event = "Player 1 scored 40 points from a meld."
        window.hint_score_events[Player.ONE].append(event)
        self.assertIn(event, window._hint_for(Player.ONE))
        self.assertNotIn(event, window._hint_for(Player.TWO))
        window.close()

    def test_single_card_panels_do_not_shrink_when_layout_reports_narrow_width(self):
        window = MainWindow()
        expected_height = 240
        for panel in (
            window.cpWon1, window.cpWon2, window.cpStock, window.cpTrump,
            window.cpTrick1, window.cpTrick2,
        ):
            panel.set_card_height(expected_height)
            panel.set_cards([1])
            panel.resize(20, panel.height())
            self.assertEqual(expected_height, panel._card_size()[1])
        window.close()

    def test_trick_drop_targets_are_wide_enough_for_their_instructions(self):
        window = MainWindow()
        window._resize_card_panels()
        for panel in (window.cpTrick1, window.cpTrick2):
            self.assertGreaterEqual(panel.minimumWidth(), TRICK_TARGET_MIN_WIDTH)
            self.assertGreaterEqual(panel.width(), panel._drop_hint.sizeHint().width())
        window.close()

    def test_game_options_menus_use_large_bold_table_font(self):
        window = MainWindow()
        for menu in (window.ui.menuQtMainWindow, window.theme_menu):
            self.assertGreaterEqual(menu.font().pointSize(), 12)
            self.assertTrue(menu.font().bold())
        window.close()

    def test_card_rows_fit_inside_available_central_height(self):
        window = MainWindow()
        window.ui.centralwidget.resize(1600, 800)
        window.cpHand1.resize(1400, window.cpHand1.height())
        window.cpHand2.resize(1400, window.cpHand2.height())
        window._resize_card_panels()
        five_rows = 5 * window.cpHand1.height()
        self.assertLess(five_rows, window.ui.centralwidget.height())
        window.close()

    def test_valid_drop_cursor_is_large_and_visible(self):
        window = MainWindow()
        cursor = window.cpHand1._valid_drop_cursor()
        self.assertFalse(cursor.isNull())
        self.assertEqual((48, 48), (cursor.width(), cursor.height()))
        self.assertFalse(cursor.toImage().pixelColor(24, 24).alpha() == 0)
        window.close()


if __name__ == "__main__":
    unittest.main()
