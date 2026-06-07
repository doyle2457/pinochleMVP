# main.py
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from game import Game
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Load UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Create game controller
        self.game: Game = Game(sequences=2)

        # Start a new game immediately (or attach to a button)
        self.start_new_game()

    # ---------------------------------------------------------
    # GAME INTEGRATION
    # ---------------------------------------------------------
    def start_new_game(self) -> None:
        """Create a new game and update the GUI."""
        self.game.create_new_game()

        # Example: show card indices in labels
        self.ui.lblHand1.setText(str(self.game.hand1))

    #  self.ui.lblHand2.setText(str(self.game.hand2))

    # Later: replace with card images in QLabels or QFrames


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
