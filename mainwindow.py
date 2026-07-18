from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QInputDialog, QLabel,
    QListWidget, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from card_panel import CardPanel
from game import Game, Player, TurnStage
from saved_games import SavedGameStore
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, save_store=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
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
        main_layout.addLayout(row_meld2, stretch=8)

        row_hint2 = QHBoxLayout()
        self.hint2 = QLabel(self)
        row_hint2.addWidget(self.hint2, stretch=65)
        main_layout.addLayout(row_hint2, stretch=8)

        row_trick = QHBoxLayout()
        row_trick.addWidget(self.cpStock, stretch=5)
        row_trick.addWidget(self.cpTrump, stretch=5)
        # The unequal outer space compensates for stock/trump on the left,
        # keeping the combined trick area centered on the table.
        row_trick.addStretch(35)
        row_trick.addWidget(self.cpTrick1, stretch=5)
        row_trick.addWidget(self.cpTrick2, stretch=5)
        row_trick.addStretch(45)
        main_layout.addLayout(row_trick, stretch=10)

        row_hint1 = QHBoxLayout()
        self.hint1 = QLabel(self)
        row_hint1.addWidget(self.hint1, stretch=65)
        main_layout.addLayout(row_hint1, stretch=8)

        score_font = self.score_pad.font()
        score_palette = self.score_pad.palette()
        for text_widget in (self.hint1, self.hint2, self.statusBar()):
            text_widget.setFont(score_font)
            text_widget.setPalette(score_palette)

        row_meld1 = QHBoxLayout()
        row_meld1.addWidget(self.cpMeld1, stretch=65)
        main_layout.addLayout(row_meld1, stretch=8)

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

    def _setup_game_menu(self):
        """Connect menu actions declared in the Qt Designer UI."""
        self.ui.actionNewGame.triggered.connect(self.start_new_game)
        self.ui.actionSaveGameState.triggered.connect(self.save_game_state)
        self.ui.actionResumeSavedGame.triggered.connect(self.resume_saved_game)
        self.ui.actionManageSavedGames.triggered.connect(self.manage_saved_games)

        # This environment paints QMenuBar contents but does not reliably route
        # mouse events to them. Put the dropdown in the central widget's event
        # region so it behaves like an ordinary, reliably clickable control.
        self.ui.menubar.hide()
        self.game_menu_strip = QWidget(self.ui.centralwidget)
        strip_layout = QHBoxLayout(self.game_menu_strip)
        strip_layout.setContentsMargins(4, 2, 4, 2)
        strip_layout.setSpacing(0)
        self.game_menu_button = QPushButton("Game", self.game_menu_strip)
        self.game_menu_button.setObjectName("gameMenuButton")
        self.game_menu_button.setMenu(self.ui.menuQtMainWindow)
        self.game_menu_button.setAccessibleName("Game menu")
        self.game_menu_button.setStyleSheet(
            "QPushButton { border: 1px solid transparent; padding: 4px 12px; text-align: left; }"
            "QPushButton:hover, QPushButton:pressed { border-color: #888; background: #ddd; }"
        )
        strip_layout.addWidget(self.game_menu_button)
        strip_layout.addStretch(1)
        self.main_layout.insertWidget(0, self.game_menu_strip)

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
        self.action_message = "New game started."
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
            f"Phase: {self.game.phase.value} | P1 round {self.game.round_meld_scores[1]} + "
            f"{self.game.round_counter_scores[1]}, total {self.game.game_scores[1]} | "
            f"P2 round {self.game.round_meld_scores[2]} + {self.game.round_counter_scores[2]}, "
            f"total {self.game.game_scores[2]}"
        )
        self.hint1.setText(self._hint_for(1))
        self.hint2.setText(self._hint_for(2))

    def _hint_for(self, player_number):
        actions = self.game.available_actions(Player(player_number))
        activity = ", ".join(actions) if actions else "waiting"
        return f"Player {player_number}: {activity}. {self.action_message}"

    def on_cards_dropped(self, target, source, card_ids):
        source_player = {"hand1": Player.ONE, "meld1": Player.ONE, "hand2": Player.TWO, "meld2": Player.TWO}.get(source)
        target_player = {"trick1": Player.ONE, "meld1": Player.ONE, "trick2": Player.TWO, "meld2": Player.TWO}.get(target)
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
        self.statusBar().showMessage(self.action_message)
        self.refresh_ui()

    def on_card_clicked_hand1(self, card_index, hand_position):
        self.newly_drawn[Player.ONE].discard(card_index)
        print(f"Card clicked in Player 1's hand: deck_id={card_index}, position={hand_position}")
        card = self.game.deck.cards[card_index]
        print(f"Clicked card: {card}, filename={card.filename}")

    def on_card_clicked_hand2(self, card_index, hand_position):
        self.newly_drawn[Player.TWO].discard(card_index)
        print(f"Card clicked in Player 2's hand: deck_id={card_index}, position={hand_position}")
        print(f"Card selected: {self.cpHand2.labels[hand_position].selected}")
        card = self.game.deck.cards[card_index]
        print(f"Clicked card: {card}, filename={card.filename}")

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
