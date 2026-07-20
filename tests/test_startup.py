import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5.QtWidgets import QApplication

from mainwindow import MainWindow


class ApplicationStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_starts_outside_project_directory(self):
        original_directory = Path.cwd()
        with TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                window = MainWindow()
                window.start_new_game()
                self.assertEqual("Trickwise Pinochle", window.windowTitle())
                self.assertTrue(all(Path(card.filename).is_file() for card in window.game.deck.cards.values()))
                window.close()
            finally:
                os.chdir(original_directory)


if __name__ == "__main__":
    unittest.main()
