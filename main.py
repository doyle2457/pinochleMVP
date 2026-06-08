# main.py
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from card_panel import CardPanel
from game import Game
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Load UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        print("Type:", type(self.ui.cpHand1))

        # Create game controller
        self.game: Game = Game(sequences=2)

        # Start a new game immediately (or attach to a button)
        self.start_new_game()

        # Create card panel for Player 1
        self.hand_panel = self.ui.cpHand1

        # Connect click signal
        self.hand_panel.card_clicked.connect(self.on_card_clicked)

    def on_card_clicked(self, index: int):
        card = self.game.get_card(index)
        print(f"Clicked card index: {index}, card: {card}")

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self) -> None:
        """Create a new game and update the GUI."""
        self.game.create_new_game()

        # Example: show card indices in textQtBrowser (replace with actual card images later)
        # self.ui.cpHand1.setText(str(self.game.hand1))

    #  self.ui.lblHand2.setText(str(self.game.hand2))

    # Later: replace with card images in QLabels or QFrames


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
