from __future__ import annotations

from PyQt5.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget

from card_panel import CardPanel
from game import Game


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.game = Game()
        self.card_panel = CardPanel(self.game)

        btn_new = QPushButton("New Game")
        btn_new.clicked.connect(self.game.start_new_game)

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self) -> None:
        """Create a new game and update the GUI."""
        self.game.create_new_game()

        # Later: update card panel with actual card images
        # self.hand_panel.update_cards(self.game.hand1)
        # self.hand_panel.set_cards(
        print("need to implement card panel update with game hand1")

        self.setCentralWidget(central)
