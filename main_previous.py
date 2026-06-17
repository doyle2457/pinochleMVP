# main.py
import sys
from typing import cast

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget

from card_panel import CardPanel
from game import Game
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Strongly typed UI object
        self.ui: Ui_MainWindow = Ui_MainWindow()
        self.ui.setupUi(self)

        # Access card panels from the UI, make them exist and store them as attributes for easier access,
        self.cpHand1 = self.ui.cpHand1
        self.cpHand2 = self.ui.cpHand2

        # Cast cpHand1 to CardPanel so Pylance knows its real typeu
        # self.hand_panel: CardPanel = cast(CardPanel, self.ui.cpHand1)
        self.cpHand1: CardPanel = cast(CardPanel, self.ui.cpHand1)
        self.cpHand2: CardPanel = cast(CardPanel, self.ui.cpHand2)

        # Connect click signal
        self.cpHand1.card_clicked.connect(self.on_card_clicked)
        self.cpHand2.card_clicked.connect(self.on_card_clicked)

        # Create game controller
        self.game: Game = Game(sequences=2)

        # Start a new game immediately
        # Start game and get hands
        self.hand1, self.hand2 = self.start_new_game()

        # Send hands to card panels
        self.cpHand1.set_cards(self.hand1)
        self.cpHand2.set_cards(self.hand2)

    #   self.opponent_panel.set_cards(hand2)

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self) -> tuple[List[int], List[int]]:
        """Create a new game and update the GUI."""
        hand1, hand2 = self.game.create_new_game()

        # Later: update card panel with actual card images
        # self.hand_panel.update_cards(self.game.hand1)
        # self.hand_panel.set_cards(
        print("need to implement card panel update with game hand1")
        return hand1, hand2

    def on_card_clicked(self, index: int) -> None:
        card = self.game.get_card(index)
        print(f"Clicked card index: {index}, card: {card}")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
