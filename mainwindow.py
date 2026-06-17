# mainwindow.py

import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from card_panel import CardPanel
from game import Game
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ---------------------------------------------------------
        # Load UI
        # ---------------------------------------------------------
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # ---------------------------------------------------------
        # Create Game object
        # ---------------------------------------------------------
        self.game = Game()

        # ---------------------------------------------------------
        # Replace placeholder cpHand1 with real CardPanel
        # ---------------------------------------------------------
        placeholder = self.ui.cpHand1
        geom = placeholder.geometry()
        placeholder.setParent(None)

        self.cpHand1 = CardPanel(self.game, self)
        self.cpHand1.setGeometry(geom)
        self.cpHand1.show()

        # ---------------------------------------------------------
        # Connect signals
        # ---------------------------------------------------------
        self.cpHand1.card_clicked.connect(self.on_card_clicked)

        # ---------------------------------------------------------
        # Start a new game
        # ---------------------------------------------------------
        self.start_new_game()

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self):
        """Deal new hands and update the card panel."""
        hand1, hand2 = self.game.create_new_game()
        self.cpHand1.set_cards(hand1)

    # ---------------------------------------------------------
    # CARD CLICK HANDLER
    # ---------------------------------------------------------
    def on_card_clicked(self, index):
        """Called when a card in Player 1's hand is clicked."""
        card_index = self.cpHand1.cards[index]
        card = self.game.deck.cards[card_index]
        print(f"Clicked card: {card}, image={card.image_path}")
