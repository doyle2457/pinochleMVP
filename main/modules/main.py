import sys

from game import start_game
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Example: connect signals or add logic here
        # self.ui.lblHand1.setText("Ready")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    start_game(window)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
