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

        # Cast cpHand1 to CardPanel so Pylance knows its real type
        self.hand_panel: CardPanel = cast(CardPanel, self.ui.cpHand1)

        # Connect click signal
        self.hand_panel.card_clicked.connect(self.on_card_clicked)

        # Create game controller
        self.game: Game = Game(sequences=2)

        # Start a new game immediately
        self.start_new_game()

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self) -> None:
        """Create a new game and update the GUI."""
        self.game.create_new_game()

        # Later: update card panel with actual card images
        # self.hand_panel.update_cards(self.game.hand1)

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
