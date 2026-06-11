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

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(btn_new)
        layout.addWidget(self.card_panel)

        self.setCentralWidget(central)
