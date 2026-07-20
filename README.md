# Trickwise Pinochle

Trickwise Pinochle is a two-player desktop Pinochle game with drag-and-drop
play, light and dark themes, scoring, saved games, and contextual hints for
turn actions, current melds, and near melds.

## Requirements

- Python 3.10 or newer
- Windows 10/11 or a modern Linux distribution such as Zorin OS

## Install and run

Clone the repository and open a terminal in its directory.

### Zorin OS and other Debian/Ubuntu-based Linux distributions

```bash
sudo apt update
sudo apt install python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
trickwise-pinochle
```

If Qt reports a missing system library, install the common Qt runtime support:

```bash
sudo apt install libxcb-xinerama0 libxcb-cursor0
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
trickwise-pinochle
```

Saved games are stored in `.pinochleMVP/saved_games` under the current user's
home directory on both operating systems.

## Run tests

```bash
python -m pip install -e ".[test]"
python -m pytest
```

The game can also be launched from the checkout with `python main.py` after
installing its dependencies.
