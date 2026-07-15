from pathlib import Path

from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout

from card_panel import CardPanel
from game import Game
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.game = Game()

        self.cpHand1 = CardPanel(self.game, self)
        self.cpMeld1 = CardPanel(self.game, self)
        self.cpWon1 = CardPanel(self.game, self)
        self.cpHint1 = CardPanel(self.game, self)
        self.cpTrick1 = CardPanel(self.game, self)
        self.cpHand2 = CardPanel(self.game, self)
        self.cpMeld2 = CardPanel(self.game, self)
        self.cpWon2 = CardPanel(self.game, self)
        self.cpHint2 = CardPanel(self.game, self)
        self.cpTrick2 = CardPanel(self.game, self)
        self.cpStock = CardPanel(self.game, self)
        self.cpTrump = CardPanel(self.game, self)

        central = self.ui.centralwidget
        main_layout = QVBoxLayout(central)

        row_hand2 = QHBoxLayout()
        row_hand2.addWidget(self.cpWon2, stretch=5)
        row_hand2.addWidget(self.cpHand2, stretch=45)
        main_layout.addLayout(row_hand2, stretch=10)

        row_meld2 = QHBoxLayout()
        row_meld2.addWidget(self.cpMeld2, stretch=65)
        main_layout.addLayout(row_meld2, stretch=8)

        row_hint2 = QHBoxLayout()
        row_hint2.addWidget(self.cpHint2, stretch=65)
        main_layout.addLayout(row_hint2, stretch=8)

        row_trick = QHBoxLayout()
        row_trick.addWidget(self.cpStock, stretch=5)
        row_trick.addWidget(self.cpTrump, stretch=5)
        row_trick.addStretch(55)
        row_trick.addWidget(self.cpTrick1, stretch=5)
        row_trick.addWidget(self.cpTrick2, stretch=5)
        main_layout.addLayout(row_trick, stretch=10)

        row_hint1 = QHBoxLayout()
        row_hint1.addWidget(self.cpHint1, stretch=65)
        main_layout.addLayout(row_hint1, stretch=8)

        row_meld1 = QHBoxLayout()
        row_meld1.addWidget(self.cpMeld1, stretch=65)
        main_layout.addLayout(row_meld1, stretch=8)

        row_hand1 = QHBoxLayout()
        row_hand1.addWidget(self.cpWon1, stretch=5)
        row_hand1.addWidget(self.cpHand1, stretch=45)
        main_layout.addLayout(row_hand1, stretch=10)

        self.cpHand1.card_clicked.connect(self.on_card_clicked_hand1)
        self.cpHand2.card_clicked.connect(self.on_card_clicked_hand2)
        self.start_new_game()

    def start_new_game(self):
        hand1, hand2, trump = self.game.create_new_game()
        self.cpHand1.set_cards(hand1)
        self.cpHand2.set_cards(hand2)
        self.cpTrump.set_cards(trump)
        card_back = Path(self.game.deck.image_dir) / "back_Red.png"
        self.cpStock.set_card_back(str(card_back))
        self.cpWon1.set_card_back(str(card_back))
        self.cpWon2.set_card_back(str(card_back))

    def on_card_clicked_hand1(self, card_index, hand_position):
        print(f"Card clicked in Player 1's hand: deck_id={card_index}, position={hand_position}")
        card = self.game.deck.cards[card_index]
        print(f"Clicked card: {card}, filename={card.filename}")

    def on_card_clicked_hand2(self, card_index, hand_position):
        print(f"Card clicked in Player 2's hand: deck_id={card_index}, position={hand_position}")
        print(f"Card selected: {self.cpHand2.labels[hand_position].selected}")
        card = self.game.deck.cards[card_index]
        print(f"Clicked card: {card}, filename={card.filename}")
