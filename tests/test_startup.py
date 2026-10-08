import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtCore import QSettings, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QCheckBox

from game import Player, RoundPhase, TurnStage
from mainwindow import MainWindow
from card_panel import TRICK_TARGET_MIN_WIDTH
from discrepancy_dialog import DiscrepancyReportEditor, DiscrepancyReportManager
from discrepancy_reports import DiscrepancyReportStore


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

    def test_all_three_card_rows_render_at_the_same_size(self):
        window = MainWindow()
        window.resize(1600, 1000)
        window.show()
        self.app.processEvents()
        window._resize_card_panels()
        window.game.trick = [(Player.ONE, window.game.hand1[0])]
        window.refresh_ui()
        self.app.processEvents()
        sizes = {
            (panel.labels[0].width(), panel.labels[0].height())
            for panel in (
                window.cpHand2,
                window.cpStock,
                window.cpTrump,
                window.cpTrick1,
                window.cpHand1,
            )
        }
        self.assertEqual(1, len(sizes))
        window.close()

    def test_card_size_remains_shared_after_cards_move_between_panels(self):
        window = MainWindow()
        window.resize(1600, 1000)
        window.show()
        self.app.processEvents()
        window._resize_card_panels()

        meld_card = window.game.hand1.pop()
        window.game.meld1.append(meld_card)
        trick_card = window.game.hand2.pop()
        window.game.trick = [(Player.TWO, trick_card)]
        window.game.stock.pop()
        window.refresh_ui()
        self.app.processEvents()

        card_panels = (
            window.cpWon2,
            window.cpHand2,
            window.cpStock,
            window.cpTrump,
            window.cpTrick2,
            window.cpMeld1,
            window.cpWon1,
            window.cpHand1,
        )
        sizes = {
            (panel.labels[0].width(), panel.labels[0].height())
            for panel in card_panels
        }
        self.assertEqual(1, len(sizes))
        window.close()

    def test_left_column_and_player_content_boundaries_are_aligned(self):
        window = MainWindow()
        window.resize(1600, 1000)
        window.show()
        self.app.processEvents()
        window._resize_card_panels()
        self.app.processEvents()

        def left(widget):
            return widget.mapTo(window.ui.centralwidget, widget.rect().topLeft()).x()

        pile_lefts = {
            left(window.cpWon2),
            left(window.cpStock),
            left(window.cpWon1),
        }
        content_lefts = {
            left(window.cpHand2),
            left(window.cpMeld2),
            left(window.hint2),
            left(window.hint1),
            left(window.cpMeld1),
            left(window.cpHand1),
        }
        self.assertEqual(1, len(pile_lefts))
        self.assertEqual(1, len(content_lefts))
        self.assertGreater(next(iter(content_lefts)), next(iter(pile_lefts)))
        self.assertEqual(
            {window.cpStock.width()},
            {window.cpWon1.width(), window.cpWon2.width()},
        )
        window.close()

    def test_hint_panels_are_three_wrapped_lines_high(self):
        window = MainWindow()
        expected_height = window.hint1.fontMetrics().lineSpacing() * 3 + 6
        self.assertTrue(window.hint1.wordWrap())
        self.assertTrue(window.hint2.wordWrap())
        self.assertEqual(expected_height, window.hint1.height())
        self.assertEqual(expected_height, window.hint2.height())
        window.close()

    def test_trick_drop_targets_are_wide_enough_for_their_instructions(self):
        window = MainWindow()
        window._resize_card_panels()
        for panel in (window.cpTrick1, window.cpTrick2):
            self.assertGreaterEqual(panel.minimumWidth(), TRICK_TARGET_MIN_WIDTH)
            self.assertGreaterEqual(panel.width(), panel._drop_hint.sizeHint().width())
        window.close()

    def test_played_trick_cards_are_centered_in_their_drop_zones(self):
        window = MainWindow()
        for panel in (window.cpTrick1, window.cpTrick2):
            self.assertTrue(panel.layout.alignment() & Qt.AlignHCenter)
        window.close()

    def test_game_options_menus_use_large_bold_table_font(self):
        window = MainWindow()
        for menu in (window.ui.menuQtMainWindow, window.theme_menu):
            self.assertGreaterEqual(menu.font().pointSize(), 12)
            self.assertTrue(menu.font().bold())
        window.close()

    def test_font_options_apply_and_persist_across_interface_text(self):
        with TemporaryDirectory() as directory:
            settings_path = Path(directory) / "settings.ini"
            settings = QSettings(str(settings_path), QSettings.IniFormat)
            window = MainWindow(settings=settings)
            chosen = QFont("Courier New", 14)
            chosen.setItalic(True)
            chosen.setBold(False)
            window.apply_ui_font(chosen)

            for widget in (
                window.score_pad,
                window.hint1,
                window.hint2,
                window.statusBar(),
                window.game_menu_button,
                window.ui.menuQtMainWindow,
                window.theme_menu,
                window.font_menu,
                window.cpTrick1._drop_hint,
                window.cpStock._badges[0],
            ):
                self.assertEqual(14, widget.font().pointSize())
                self.assertTrue(widget.font().italic())
                self.assertFalse(widget.font().bold())
            window.close()

            restored = MainWindow(
                settings=QSettings(str(settings_path), QSettings.IniFormat)
            )
            self.assertEqual(14, restored.current_ui_font.pointSize())
            self.assertTrue(restored.current_ui_font.italic())
            restored.close()

    def test_font_options_reset_and_limit_extreme_sizes(self):
        with TemporaryDirectory() as directory:
            settings = QSettings(
                str(Path(directory) / "settings.ini"), QSettings.IniFormat
            )
            window = MainWindow(settings=settings)
            oversized = QFont("Arial", 72)
            window.apply_ui_font(oversized)
            self.assertEqual(
                window.MAX_UI_FONT_SIZE,
                window.current_ui_font.pointSize(),
            )
            self.assertTrue(settings.contains("ui_font"))
            window.reset_ui_font()
            self.assertFalse(settings.contains("ui_font"))
            self.assertEqual(
                max(
                    window.MIN_UI_FONT_SIZE,
                    QApplication.instance().font().pointSize(),
                ),
                window.current_ui_font.pointSize(),
            )
            window.close()

    def test_game_options_include_discrepancy_report_manager(self):
        with TemporaryDirectory() as directory:
            window = MainWindow(report_store=DiscrepancyReportStore(directory))
            self.assertEqual(
                "Discrepancy Reports...", window.discrepancy_report_action.text()
            )
            self.assertEqual(Path(directory), window.report_store.directory)
            window.close()

    def test_discrepancy_editor_saves_exclusive_status_box_selection(self):
        with TemporaryDirectory() as directory:
            store = DiscrepancyReportStore(directory)
            editor = DiscrepancyReportEditor(store)
            editor.title.setText("Hint names the wrong leader")
            planned = next(
                button
                for button in editor.status_buttons.buttons()
                if button.text() == "Planned"
            )
            planned.setChecked(True)
            editor.save_report()
            self.assertTrue(
                all(
                    isinstance(button, QCheckBox)
                    for button in editor.status_buttons.buttons()
                )
            )
            self.assertEqual(
                ["Planned"],
                [
                    button.text()
                    for button in editor.status_buttons.buttons()
                    if button.isChecked()
                ],
            )
            self.assertEqual("Planned", store.load("DR-0001").status)
            editor.close()

    def test_discrepancy_manager_can_change_report_directory(self):
        with TemporaryDirectory() as first, TemporaryDirectory() as second:
            store = DiscrepancyReportStore(first)
            manager = DiscrepancyReportManager(store)
            manager.set_directory(second)
            self.assertEqual(Path(second), store.directory)
            self.assertEqual(str(Path(second)), manager.folder_label.text())
            manager.close()

    def test_discrepancy_disposition_boxes_supply_contextual_help(self):
        with TemporaryDirectory() as directory:
            editor = DiscrepancyReportEditor(DiscrepancyReportStore(directory))
            working_as_designed = next(
                button
                for button in editor.disposition_category_buttons.buttons()
                if button.text() == "Working as Designed"
            )
            working_as_designed.click()
            self.assertTrue(working_as_designed.isChecked())
            self.assertIn("chosen rules or design", working_as_designed.toolTip())
            self.assertIn("chosen rules or design", editor.disposition_help.text())
            editor.close()

    def test_discrepancy_form_invites_a_proposed_solution(self):
        with TemporaryDirectory() as directory:
            editor = DiscrepancyReportEditor(DiscrepancyReportStore(directory))
            labels = [
                label.text()
                for label in editor.findChildren(type(editor.report_id))
            ]
            self.assertTrue(
                any("proposed solution" in label.lower() for label in labels)
            )
            editor.close()

    def test_phase_is_displayed_in_title_case_and_empty_stock_has_no_card(self):
        window = MainWindow()
        window.game.phase = RoundPhase.TRICK_PHASE
        window.game.stock.clear()
        window.refresh_ui()
        self.assertTrue(window.score_pad.text().startswith("Round: 1 | "))
        self.assertIn("Phase: Trick Phase", window.score_pad.text())
        self.assertEqual([], window.cpStock.labels)
        window.close()

    def test_score_panel_includes_current_status_message(self):
        window = MainWindow()
        self.assertTrue(window.score_pad.text().endswith("| New game started."))
        window.action_message = "Lead accepted; waiting for the response."
        window.statusBar().showMessage(window.action_message)
        window.refresh_ui()
        self.assertTrue(
            window.score_pad.text().endswith(
                "| Lead accepted; waiting for the response."
            )
        )
        self.assertEqual(
            "Lead accepted; waiting for the response.",
            window.statusBar().currentMessage(),
        )
        window.close()

    def test_completed_trick_remains_visible_during_resolution_timer(self):
        window = MainWindow()
        leader = window.game.leader
        lead_card = window.game.legal_cards(leader)[0]
        window.on_cards_dropped(
            f"trick{leader.value}",
            f"hand{leader.value}",
            [lead_card],
        )
        responder = window.game.responder
        response_card = window.game.legal_cards(responder)[0]
        window.on_cards_dropped(
            f"trick{responder.value}",
            f"hand{responder.value}",
            [response_card],
        )

        self.assertEqual(TurnStage.TRICK_RESOLUTION, window.game.turn_stage)
        self.assertTrue(window.trick_resolution_timer.isActive())
        self.assertEqual(3000, window.trick_resolution_timer.interval())
        self.assertEqual(2, len(window.game.trick))
        self.assertEqual(
            2,
            len(window.cpTrick1.labels) + len(window.cpTrick2.labels),
        )
        for panel in (
            window.cpMeld1,
            window.cpMeld2,
            window.cpTrick1,
            window.cpTrick2,
            window.cpTrump,
        ):
            self.assertFalse(panel.drop_enabled)

        window.trick_resolution_timer.stop()
        window._complete_pending_trick_resolution()
        self.assertEqual([], window.game.trick)
        self.assertFalse(window.trick_resolution_timer.isActive())
        self.assertTrue(window.cpTrick1.drop_enabled)
        self.assertTrue(window.cpTrick2.drop_enabled)
        self.assertNotIn("resolving in 3 seconds", window.action_message)
        window.close()

    def test_starting_new_game_cancels_pending_trick_timer(self):
        window = MainWindow()
        window.game.turn_stage = TurnStage.TRICK_RESOLUTION
        window.trick_resolution_timer.start(window.TRICK_RESOLUTION_DELAY_MS)
        self.assertTrue(window.trick_resolution_timer.isActive())
        window.start_new_game()
        self.assertFalse(window.trick_resolution_timer.isActive())
        self.assertEqual(TurnStage.LEAD, window.game.turn_stage)
        window.close()

    def test_completed_round_advances_without_a_trick_result_pause(self):
        window = MainWindow()
        old_dealer = window.game.dealer
        window.game.phase = RoundPhase.ROUND_COMPLETE
        self.assertTrue(window._start_next_round_if_complete())
        self.assertEqual(RoundPhase.MELD_PHASE, window.game.phase)
        self.assertEqual(old_dealer.other, window.game.dealer)
        self.assertFalse(hasattr(window, "trick_result_label"))
        self.assertFalse(hasattr(window, "confirm_trick_action"))
        window.close()

    def test_selected_cards_supply_click_to_drop_payload(self):
        window = MainWindow()
        window.cpHand1.labels[0].selected = True
        source, cards = window.cpTrick1._selected_payload()
        self.assertEqual("hand1", source)
        self.assertEqual([window.cpHand1.cards[0]], cards)
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
