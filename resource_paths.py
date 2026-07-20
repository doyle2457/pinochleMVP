"""Locate bundled application resources on every supported platform."""

from __future__ import annotations

import sys
from pathlib import Path


APP_NAME = "trickwise-pinochle"


def card_image_dir() -> Path:
    """Return the installed card-image directory.

    Editable/source installs keep images beside this module. Regular wheel
    installs place them under the active Python environment's ``share`` tree.
    """
    candidates = (
        Path(__file__).resolve().parent / "images" / "cards",
        Path(sys.prefix) / "share" / APP_NAME / "images" / "cards",
    )
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    locations = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Card images were not found. Checked: {locations}")
