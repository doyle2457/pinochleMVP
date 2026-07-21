from pathlib import Path

from PyQt5.QtCore import QSettings, QTimer, Qt
from PyQt5.QtWidgets import (
    QActionGroup, QApplication, QDialog, QDialogButtonBox, QHBoxLayout,
    QInputDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton,
    QToolButton, QVBoxLayout,
)

from card_panel import (
    CARD_H,
    CARD_W,
    PANEL_PADDING,
    TRICK_TARGET_MIN_WIDTH,
    CardPanel,
)
from display_themes import DEFAULT_THEME, THEMES
from game import Game, Player, TurnStage
from saved_games import SavedGameStore
from selectable_label import SelectableLabel
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, save_store=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.settings = QSettings("Trickwise", "Trickwise Pinochle")
        self._base_app_stylesheet = QApplication.instance().styleSheet()
        self.game = Game()
        self.save_store = save_store or SavedGameStore()

        self.cpHand1 = CardPanel(self.game, self, "hand1")
        self.cpMeld1 = CardPanel(self.game, self, "meld1")
        self.cpWon1 = CardPanel(self.game, self, "won1")
        self.cpHint1 = CardPanel(self.game, self, "hint1")
        self.cpTrick1 = CardPanel(self.game, self, "trick1")
        self.cpHand2 = CardPanel(self.game, self, "hand2")
        self.cpMeld2 = CardPanel(self.game, self, "meld2")
        self.cpWon2 = CardPanel(self.game, self, "won2")
        self.cpHint2 = CardPanel(self.game, self, "hint2")
        self.cpTrick2 = CardPanel(self.game, self, "trick2")
        self.cpStock = CardPanel(self.game, self, "stock")
        self.cpTrump = CardPanel(self.game, self, "trump")
        self.action_message = ""
        self.hint_score_events = {Player.ONE: [], Player.TWO: []}
        self.newly_drawn = {Player.ONE: set(), Player.TWO: set()}
        # A meld may combine selected cards from the player's hand and cards
        # already displayed in that player's meld area.
        self.cpHand1.selection_peers = [self.cpMeld1]
        self.cpMeld1.selection_peers = [self.cpHand1]
        self.cpHand2.selection_peers = [self.cpMeld2]
        self.cpMeld2.selection_peers = [self.cpHand2]

        central = self.ui.centralwidget
        main_layout = QVBoxLayout(central)
        self.main_layout = main_layout

        self.score_pad = QLabel(self)
        self.score_pad.setStyleSheet("font-weight: bold; padding: 4px; border: 1px solid #555;")
        main_layout.addWidget(self.score_pad)

        row_hand2 = QHBoxLayout()
        row_hand2.addWidget(self.cpWon2, stretch=5)
        row_hand2.addWidget(self.cpHand2, stretch=45)
        main_layout.addLayout(row_hand2, stretch=10)

        row_meld2 = QHBoxLayout()
        row_meld2.addWidget(self.cpMeld2, stretch=65)
        main_layout.addLayout(row_meld2, stretch=10)

        row_hint2 = QHBoxLayout()
        self.hint2 = QLabel(self)
        row_hint2.addWidget(self.hint2, stretch=65)
        main_layout.addLayout(row_hint2, stretch=8)

        row_trick = QHBoxLayout()
        row_trick.addWidget(self.cpStock, stretch=5)
        row_trick.addWidget(self.cpTrump, stretch=5)
        # Stock and trump have card-sized minimum widths, so the trick area
        # needs a little less leading space to align with the visual midpoint
        # of the hand panels.
        row_trick.addStretch(30)
        row_trick.addWidget(self.cpTrick1, stretch=5)
        row_trick.addWidget(self.cpTrick2, stretch=5)
        row_trick.addStretch(50)
        self.row_trick = row_trick
        main_layout.addLayout(row_trick, stretch=10)

        row_hint1 = QHBoxLayout()
        self.hint1 = QLabel(self)
        row_hint1.addWidget(self.hint1, stretch=65)
        main_layout.addLayout(row_hint1, stretch=8)

        score_font = self.score_pad.font()
        score_palette = self.score_pad.palette()
        hint_font = self.score_pad.font()
        hint_font.setPointSize(max(12, hint_font.pointSize() + 3))
        hint_font.setBold(True)
        self.score_pad.setFont(hint_font)
        self.table_label_font = hint_font
        for hint in (self.hint1, self.hint2):
            hint.setFont(hint_font)
            hint.setWordWrap(True)
            hint.setPalette(score_palette)
        for text_widget in (self.statusBar(),):
            text_widget.setFont(score_font)
            text_widget.setPalette(score_palette)

        row_meld1 = QHBoxLayout()
        row_meld1.addWidget(self.cpMeld1, stretch=65)
        main_layout.addLayout(row_meld1, stretch=10)

        row_hand1 = QHBoxLayout()
        row_hand1.addWidget(self.cpWon1, stretch=5)
        row_hand1.addWidget(self.cpHand1, stretch=45)
        main_layout.addLayout(row_hand1, stretch=10)

        self.cpHand1.card_clicked.connect(self.on_card_clicked_hand1)
        self.cpHand2.card_clicked.connect(self.on_card_clicked_hand2)
        self.cpStock.card_clicked.connect(self.on_last_draw_card_clicked)
        self.cpTrump.card_clicked.connect(self.on_last_draw_card_clicked)
        for target, panel in {
            "meld1": self.cpMeld1, "meld2": self.cpMeld2,
            "trick1": self.cpTrick1, "trick2": self.cpTrick2,
            "trump": self.cpTrump,
            "won1": self.cpWon1, "won2": self.cpWon2,
        }.items():
            panel.cards_dropped.connect(lambda source, cards, name=target: self.on_cards_dropped(name, source, cards))
        self._setup_game_menu()
        self.start_new_game()
        QTimer.singleShot(0, self._resize_card_panels)

    def _setup_game_menu(self):
        """Connect menu actions declared in the Qt Designer UI."""
        self.ui.actionNewGame.triggered.connect(self.start_new_game)
        self.ui.actionSaveGameState.triggered.connect(self.save_game_state)
        self.ui.actionResumeSavedGame.triggered.connect(self.resume_saved_game)
        self.ui.actionManageSavedGames.triggered.connect(self.manage_saved_games)

        # The ordinary menu bar does not route mouse events reliably here, so
        # expose the same menu as a prominent control in the table itself.
        self.ui.menubar.hide()
        self.game_menu_button = QToolButton(self.ui.centralwidget)
        self.game_menu_button.setText("Game Options")
        self.game_menu_button.setObjectName("gameMenuButton")
        self.game_menu_button.setAccessibleName("Game menu")
        self.game_menu_button.setFont(self.table_label_font)
        # Keep the popup separate from the table control. Parenting the QMenu
        # to the button can make its first action paint beneath the button on
        # some platforms before the menu has actually been requested.
        self.ui.menuQtMainWindow.hide()
        self.ui.menuQtMainWindow.setFont(self.table_label_font)
        self.game_menu_button.clicked.connect(self._show_game_menu)
        self.theme_menu = self.ui.menuQtMainWindow.addMenu("Themes")
        self.theme_menu.setFont(self.table_label_font)
        self.theme_action_group = QActionGroup(self)
        self.theme_action_group.setExclusive(True)
        self.theme_actions = {}
        for theme_name in THEMES:
            action = self.theme_menu.addAction(theme_name)
            action.setCheckable(True)
            action.triggered.connect(
                lambda checked, name=theme_name: checked and self.apply_theme(name)
            )
            self.theme_action_group.addAction(action)
            self.theme_actions[theme_name] = action
        self.row_trick.addWidget(
            self.game_menu_button, 0, Qt.AlignRight | Qt.AlignVCenter
        )
        saved_theme = self.settings.value("display_theme", DEFAULT_THEME, type=str)
        self.apply_theme(
            saved_theme if saved_theme in THEMES else DEFAULT_THEME,
            persist=False,
        )
        QTimer.singleShot(0, self._align_game_menu_to_hand_slot)

    def apply_theme(self, theme_name, persist=True):
        """Apply and optionally remember a named display theme."""
        theme = THEMES[theme_name]
        app_stylesheet = theme["app_stylesheet"] or self._base_app_stylesheet
        QApplication.instance().setStyleSheet(app_stylesheet)
        self.current_theme_name = theme_name
        self.theme_actions[theme_name].setChecked(True)
        SelectableLabel.set_theme(theme)
        for panel in (
            self.cpHand1, self.cpMeld1, self.cpWon1, self.cpTrick1,
            self.cpHand2, self.cpMeld2, self.cpWon2, self.cpTrick2,
            self.cpStock, self.cpTrump,
        ):
            panel.set_theme(theme)
        self.score_pad.setStyleSheet(
            f"font-weight: bold; padding: 4px; border: 1px solid {theme['border']}; "
            f"background-color: {theme['surface']}; color: {theme['text']};"
        )
        self.game_menu_button.setStyleSheet(
            "QToolButton { border: 1px solid transparent; padding: 4px 12px; "
            f"text-align: left; color: {theme['text']}; }}"
            "QToolButton:hover, QToolButton:pressed { "
            f"border-color: {theme['border']}; background: {theme['hover']}; }}"
        )
        if persist:
            self.settings.setValue("display_theme", theme_name)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "row_trick") and hasattr(self, "game_menu_button"):
            QTimer.singleShot(0, self._resize_card_panels)
            QTimer.singleShot(0, self._align_game_menu_to_hand_slot)

    def _resize_card_panels(self):
        """Scale every card row to the available table height.

        Five card rows share roughly three quarters of the central widget;
        the remaining space belongs to hints, scores, margins, and the status
        bar. The upper bound avoids comically large cards on external monitors.
        """
        if not hasattr(self, "cpHand1"):
            return
        available_height = max(1, self.ui.centralwidget.height())
        margins = self.main_layout.contentsMargins()
        spacing = self.main_layout.spacing()

        def label_height(label):
            wrapped_height = label.heightForWidth(max(1, label.width()))
            return max(label.sizeHint().height(), wrapped_height if wrapped_height > 0 else 0)

        reserved_height = (
            margins.top()
            + margins.bottom()
            + spacing * max(0, self.main_layout.count() - 1)
            + self.score_pad.sizeHint().height()
            + label_height(self.hint1)
            + label_height(self.hint2)
        )
        vertical_card_height = max(
            48,
            min(320, (available_height - reserved_height) // 5 - PANEL_PADDING),
        )
        hand_fit_heights = []
        for hand in (self.cpHand1, self.cpHand2):
            spacing = hand.layout.spacing()
            available_width = max(1, hand.width() - spacing * 11)
            fitted_width = max(1, available_width // 12)
            hand_fit_heights.append(round(fitted_width * CARD_H / CARD_W))
        card_height = min(vertical_card_height, *hand_fit_heights)
        card_width = round(card_height * CARD_W / CARD_H)
        panels = (
            self.cpHand1, self.cpMeld1, self.cpWon1, self.cpTrick1,
            self.cpHand2, self.cpMeld2, self.cpWon2, self.cpTrick2,
            self.cpStock, self.cpTrump,
        )
        for panel in panels:
            panel.set_card_height(card_height)
        for panel in (
            self.cpWon1, self.cpWon2, self.cpStock, self.cpTrump,
        ):
            panel.setMinimumWidth(card_width + 6)
        for panel in (self.cpTrick1, self.cpTrick2):
            panel.setMinimumWidth(max(card_width + 6, TRICK_TARGET_MIN_WIDTH))
        QTimer.singleShot(0, self._align_game_menu_to_hand_slot)

    def _align_game_menu_to_hand_slot(self):
        """Place the menu anchor at the right edge of hand-card slot 12."""
        slot_count = 12
        spacing = self.cpHand1.layout.spacing()
        available_width = max(1, self.cpHand1.width() - spacing * (slot_count - 1))
        preferred_width = round(self.cpHand1._preferred_card_height * CARD_W / CARD_H)
        card_width = min(preferred_width, max(1, available_width // slot_count))
        slot_right = (
            self.cpHand1.geometry().left()
            + card_width * slot_count
            + spacing * (slot_count - 1)
            - 1
        )
        margins = self.row_trick.contentsMargins()
        unconstrained_right = (
            self.ui.centralwidget.contentsRect().right()
            - self.main_layout.contentsMargins().right()
        )
        right_margin = max(0, unconstrained_right - slot_right)
        if margins.right() != right_margin:
            self.row_trick.setContentsMargins(
                margins.left(), margins.top(), right_margin, margins.bottom()
            )

    def _show_game_menu(self):
        """Open the Game Options menu with its right edge on the button edge."""
        menu = self.ui.menuQtMainWindow
        popup_position = self.game_menu_button.mapToGlobal(
            self.game_menu_button.rect().bottomRight()
        )
        popup_position.setX(popup_position.x() - menu.sizeHint().width() + 1)
        popup_position.setY(popup_position.y() + 1)
        menu.popup(popup_position)

    def save_game_state(self):
        name, accepted = QInputDialog.getText(self, "Save Game State", "Saved game name:")
        if not accepted:
            return
        try:
            existing = {item["name"] for item in self.save_store.list()}
            if name.strip() in existing and QMessageBox.question(
                self, "Replace Saved Game", f'Replace the existing saved game "{name.strip()}"?'
            ) != QMessageBox.Yes:
                return
            self.save_store.save(name, self.game)
            self.action_message = f'Game saved as "{name.strip()}".'
            self.statusBar().showMessage(self.action_message)
            self.refresh_ui()
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.critical(self, "Unable to Save", str(error))

    def resume_saved_game(self):
        saves = self.save_store.list()
        if not saves:
            QMessageBox.information(self, "Resume Saved Game", "There are no saved games yet.")
            return
        names = [item["name"] for item in saves]
        name, accepted = QInputDialog.getItem(
            self, "Resume Saved Game", "Select a saved game:", names, 0, False
        )
        if accepted:
            self._load_saved_game(name)

    def _load_saved_game(self, name):
        try:
            self.game = self.save_store.load(name)
            for panel in (
                self.cpHand1, self.cpMeld1, self.cpWon1, self.cpHint1, self.cpTrick1,
                self.cpHand2, self.cpMeld2, self.cpWon2, self.cpHint2, self.cpTrick2,
                self.cpStock, self.cpTrump,
            ):
                panel.game = self.game
            self.newly_drawn = {Player.ONE: set(), Player.TWO: set()}
            self.hint_score_events = {Player.ONE: [], Player.TWO: []}
            self.action_message = f'Resumed "{name}".'
            self.statusBar().showMessage(self.action_message)
            self.refresh_ui()
        except (OSError, ValueError, KeyError, TypeError) as error:
            QMessageBox.critical(self, "Unable to Resume", str(error))

    def manage_saved_games(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Saved Games")
        layout = QVBoxLayout(dialog)
        saved_list = QListWidget(dialog)
        for item in self.save_store.list():
            saved_list.addItem(item["name"])
        layout.addWidget(saved_list)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, parent=dialog)
        resume = QPushButton("Resume", dialog)
        delete = QPushButton("Delete", dialog)
        buttons.addButton(resume, QDialogButtonBox.ActionRole)
        buttons.addButton(delete, QDialogButtonBox.DestructiveRole)
        buttons.rejected.connect(dialog.reject)
        resume.clicked.connect(lambda: self._resume_from_manager(dialog, saved_list))
        delete.clicked.connect(lambda: self._delete_from_manager(saved_list))
        layout.addWidget(buttons)
        dialog.exec_()

    def _resume_from_manager(self, dialog, saved_list):
        if saved_list.currentItem() is not None:
            name = saved_list.currentItem().text()
            dialog.accept()
            self._load_saved_game(name)

    def _delete_from_manager(self, saved_list):
        item = saved_list.currentItem()
        if item is None:
            return
        name = item.text()
        if QMessageBox.question(
            self, "Delete Saved Game", f'Permanently delete "{name}"?'
        ) != QMessageBox.Yes:
            return
        try:
            self.save_store.delete(name)
            saved_list.takeItem(saved_list.row(item))
        except OSError as error:
            QMessageBox.critical(self, "Unable to Delete", str(error))

    def start_new_game(self):
        self.game.create_new_game()
        self.newly_drawn = {Player.ONE: set(), Player.TWO: set()}
        self.hint_score_events = {Player.ONE: [], Player.TWO: []}
        self.action_message = "New game started."
        self.statusBar().showMessage(self.action_message)
        self.refresh_ui()

    def refresh_ui(self):
        """Render controller state; game actions remain the single source of truth."""
        self.newly_drawn[Player.ONE].intersection_update(self.game.hand1)
        self.newly_drawn[Player.TWO].intersection_update(self.game.hand2)
        self.cpHand1.set_cards(self.game.hand1, self.newly_drawn[Player.ONE])
        self.cpHand2.set_cards(self.game.hand2, self.newly_drawn[Player.TWO])
        self.cpMeld1.set_cards(self.game.meld1)
        self.cpMeld2.set_cards(self.game.meld2)
        self.cpTrick1.set_cards([card_id for player, card_id in self.game.trick if player.value == 1])
        self.cpTrick2.set_cards([card_id for player, card_id in self.game.trick if player.value == 2])
        card_back = Path(self.game.deck.image_dir) / "back_Red.png"
        selectable_stock_card = (
            self.game.stock[0]
            if self.game.turn_stage is TurnStage.LAST_DRAW_CHOICE and len(self.game.stock) == 1
            else None
        )
        self.cpStock.set_card_back(
            str(card_back), len(self.game.stock), selectable_card_id=selectable_stock_card
        )
        self.cpWon1.set_card_back(str(card_back), len(self.game.won1))
        self.cpWon2.set_card_back(str(card_back), len(self.game.won2))
        if self.game.trump:
            self.cpTrump.set_cards(self.game.trump)
        else:
            self.cpTrump.clear()
        self.score_pad.setText(
            f"Phase: {self.game.phase.value} | Player 1 round {self.game.round_meld_scores[1]} + "
            f"{self.game.round_counter_scores[1]}, total {self.game.game_scores[1]} | "
            f"Player 2 round {self.game.round_meld_scores[2]} + {self.game.round_counter_scores[2]}, "
            f"total {self.game.game_scores[2]}"
        )
        self.hint1.setText(self._hint_for(1))
        self.hint2.setText(self._hint_for(2))

    def _hint_for(self, player_number):
        player = Player(player_number)
        actions = self.game.available_actions(player)
        if self.game.turn_stage is TurnStage.LEAD:
            guidance = "Lead to the trick." if player is self.game.leader else "Waiting."
        elif self.game.turn_stage is TurnStage.RESPONSE:
            guidance = (
                "Respond to the trick." if player is self.game.responder else "Waiting."
            )
        elif self.game.turn_stage is TurnStage.LAST_DRAW_CHOICE:
            guidance = (
                "Choose the final draw." if player is self.game.leader else "Waiting."
            )
        else:
            guidance = "Waiting."

        options = []
        if "swap_dix" in actions:
            options.append("Dix swap available.")
        if "declare_meld" in actions:
            options.append("Meld if you can.")
            melds = self.game.scoreable_melds(player)
            if melds:
                descriptions = ", ".join(
                    f"{meld_type.value.replace('_', ' ').title()} — {suit}"
                    for meld_type, suit in melds
                )
                options.append(f"Current melds: {descriptions}.")
        if "play_to_trick" in actions:
            near_melds = self.game.near_melds(player)
            if near_melds:
                descriptions = "; ".join(
                    f"{near_meld.meld_type.value.replace('_', ' ').title()} — "
                    f"{near_meld.suit_label}, missing {near_meld.missing_rank} of "
                    f"{near_meld.missing_suit} (Likely to fill: "
                    f"{near_meld.probability:.1%}; weighted value: "
                    f"{near_meld.weighted_points:.1f} points)"
                    for near_meld in near_melds
                )
                options.append(f"Near melds: {descriptions}.")
        return " ".join((guidance, *options, *self.hint_score_events[player]))

    def on_cards_dropped(self, target, source, card_ids):
        source_player = {"hand1": Player.ONE, "meld1": Player.ONE, "hand2": Player.TWO, "meld2": Player.TWO}.get(source)
        target_player = {"trick1": Player.ONE, "meld1": Player.ONE, "trick2": Player.TWO, "meld2": Player.TWO}.get(target)
        scores_before = dict(self.game.round_meld_scores)
        result = None
        if target == "trump":
            if source not in {"hand1", "hand2"} or source_player is None:
                self.action_message = "Only a Dix from a player's hand can be exchanged."
            elif len(card_ids) != 1:
                self.action_message = "Drag exactly one Dix to the trump card."
            else:
                result = self.game.swap_dix(source_player, card_ids[0])
                self.action_message = result.message
        elif source_player is None or target_player is None or source_player is not target_player:
            self.action_message = "Cards must stay with their owner's play area."
        elif target.startswith("trick"):
            if len(card_ids) != 1:
                self.action_message = "Drag exactly one card to the trick."
            else:
                hands_before = {
                    Player.ONE: set(self.game.hand1),
                    Player.TWO: set(self.game.hand2),
                }
                result = self.game.play_to_trick(source_player, card_ids[0])
                self.action_message = result.message
                if result.success:
                    self.newly_drawn[Player.ONE].update(set(self.game.hand1) - hands_before[Player.ONE])
                    self.newly_drawn[Player.TWO].update(set(self.game.hand2) - hands_before[Player.TWO])
        elif target.startswith("meld"):
            options = self.game.meld_options(source_player, card_ids)
            if len(options) != 1:
                self.action_message = "Selected cards do not identify exactly one valid meld."
            else:
                result = self.game.declare_meld(source_player, options[0], card_ids)
                self.action_message = result.message
        else:
            self.action_message = "Won cards are moved automatically when a trick resolves."
        if result is not None and result.success and source_player is not None:
            points = self.game.round_meld_scores[source_player] - scores_before[source_player]
            if points:
                reason = "Dix swap" if target == "trump" else "meld"
                self.hint_score_events[source_player].append(
                    f"{source_player.display_name} scored {points} points from a {reason}."
                )
            if target.startswith("trick") and not self.game.trick:
                self.hint_score_events = {Player.ONE: [], Player.TWO: []}
        self.statusBar().showMessage(self.action_message)
        self.refresh_ui()

    def on_card_clicked_hand1(self, card_index, hand_position):
        self.newly_drawn[Player.ONE].discard(card_index)

    def on_card_clicked_hand2(self, card_index, hand_position):
        self.newly_drawn[Player.TWO].discard(card_index)

    def on_last_draw_card_clicked(self, card_index, hand_position):
        """Give the final trick winner their chosen stock/trump card."""
        if self.game.turn_stage is not TurnStage.LAST_DRAW_CHOICE:
            return
        player = self.game.leader
        hands_before = {
            Player.ONE: set(self.game.hand1),
            Player.TWO: set(self.game.hand2),
        }
        result = self.game.choose_last_draw(player, card_index)
        self.action_message = result.message
        if result.success:
            self.newly_drawn[Player.ONE].update(set(self.game.hand1) - hands_before[Player.ONE])
            self.newly_drawn[Player.TWO].update(set(self.game.hand2) - hands_before[Player.TWO])
        self.statusBar().showMessage(self.action_message)
        self.refresh_ui()
