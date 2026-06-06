class Table:
    """
    Python class corresponding to the PyQt5 UI table.

    This class is the highest level object of visible objects on the game table.
    It contains all the objects of the game table, such as the cards, the players, etc.

    The initial MVP componet in Hand1 which cntains the cards of Player 1.
    The cards of Player 2 will be in Hand2, which will be a child of Table.

     All the visible objects of the table are lists that correspond
     to the label objects in the PyQt5 UI.

     Attributes:
         attribute1 (type): Description of attribute1.
         attribute2 (type): Description of attribute2.

     Methods:
         method_name: Optional section. Usually omitted because methods
             have their own docstrings.

     Examples:
         Example usage can go here:

         >>> obj = ClassName(value)
         >>> obj.do_something()
    """
list: hand1, hand2, deck, discard_pile, player1_score, player2_score


class Table:
    def __init__(self):
        self.label = []

    def __repr__(self):
        return f"{self.__class__.__name__}(label={self.label[1:10]})"


def main():
    table = Table()
    print(table)
