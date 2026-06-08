# card_panel.py
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QWidget

CARD_W = 100
CARD_H = 150


class CardPanel(QWidget):
    card_clicked = pyqtSignal(int)  # index of clicked card

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cards = []  # list of card IDs (e.g., 23, 24, 22)
        self.labels = []  # QLabel objects

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

    # ---------------------------------------------------------
    # Load card images into the panel
    # ---------------------------------------------------------
    def set_cards(self, card_list):
        self.clear()
        self.cards = card_list

        for index, card_id in enumerate(card_list):
            lbl = QLabel()
            lbl.setFixedSize(CARD_W, CARD_H)
            lbl.setScaledContents(True)

            pix = QPixmap(f"cards/{card_id}.png")
            lbl.setPixmap(pix)

            lbl.mousePressEvent = lambda e, i=index: self.card_clicked.emit(i)

            self.labels.append(lbl)
            self.layout.addWidget(lbl)

    # ---------------------------------------------------------
    # Remove all cards
    # ---------------------------------------------------------
    def clear(self):
        for lbl in self.labels:
            self.layout.removeWidget(lbl)
            lbl.deleteLater()
        self.labels = []
        self.cards = []
