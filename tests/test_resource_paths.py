import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from deck import Deck
from resource_paths import card_image_dir


class ResourcePathTests(unittest.TestCase):
    def test_source_card_directory_exists_and_contains_all_faces(self):
        directory = card_image_dir()
        self.assertTrue(directory.is_absolute())
        self.assertTrue((directory / "back_Red.png").is_file())
        self.assertEqual(24, len([path for path in directory.glob("*.png") if "back_" not in path.name]))

    def test_deck_uses_absolute_existing_image_paths(self):
        deck = Deck()
        deck.build_deck()
        self.assertEqual(48, len(deck.cards))
        self.assertTrue(all(Path(card.filename).is_absolute() for card in deck.cards.values()))
        self.assertTrue(all(Path(card.filename).is_file() for card in deck.cards.values()))

    def test_installed_share_directory_is_used_when_source_assets_are_absent(self):
        with TemporaryDirectory() as directory:
            prefix = Path(directory)
            installed = prefix / "share" / "trickwise-pinochle" / "images" / "cards"
            installed.mkdir(parents=True)
            with patch("resource_paths.__file__", str(prefix / "missing" / "resource_paths.py")), patch.object(
                sys, "prefix", str(prefix)
            ):
                self.assertEqual(installed, card_image_dir())


if __name__ == "__main__":
    unittest.main()
