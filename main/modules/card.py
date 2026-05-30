class Card:
    def __init__(self, suit, rank, filename):
        self.suit = suit
        self.rank = rank
        self.filename = filename  # e.g., "images/cards/hearts_A.png"

    def __repr__(self):
        return f"{self.rank} of {self.suit}"
