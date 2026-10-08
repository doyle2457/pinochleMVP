# Trickwise Pinochle

Trickwise Pinochle is a two-player desktop Pinochle game with drag-and-drop
and select-then-click
play, light and dark themes, scoring, saved games, and contextual hints for
turn actions, current melds, and near melds.

Created for OpenAI Build Week, the project explores how an interactive card
game can explain the state of play without interrupting it. The hint system
changes as cards move through a turn, identifies available melds, and evaluates
near melds from the cards that have already been exposed.

## Highlights

- Two-player Pinochle with legal-play enforcement and scoring
- Drag-and-drop or select-then-click play with enlarged, glowing drop targets
- Persistent trump-suit display throughout the strict Trick Phase
- Turn-aware guidance for leading, responding, waiting, melding, and Dix swaps
- Current-meld and near-meld analysis
- Light and dark display themes
- System-font selection with persistence and reset
- Saved games
- Built-in discrepancy reports for recording, prioritizing, and tracking issues
- Responsive layouts for Windows and Linux displays

## How Codex and GPT-5.6 were used

Codex and GPT-5.6 helped transform an existing experimental PyQt5 interface
into a complete, playable two-player Pinochle game during OpenAI Build Week.

They were used to:

- Expand and correct the two-player Pinochle rules engine
- Implement drag-and-drop card play and visible drop targets
- Add meld recognition, scoring, and Dix exchanges
- Develop contextual hints for leading, waiting, responding, and melding
- Analyze current melds and near melds using exposed-card information
- Implement saved games
- Add light and dark display themes
- Make the interface responsive on Windows and Linux
- Diagnose layout and cross-platform packaging problems
- Create and run automated tests for rules and edge cases
- Clean, document, package, and publish the project

Codex did more than generate isolated code. It helped revise the architecture,
reason about complicated game states, test changes iteratively, and refine the
interface from observations made while playing the game. The final release
passes 67 automated tests.

## Discrepancy reports

Choose **Game Options → Discrepancy Reports...** to create a numbered
discrepancy report (DR), assign its priority and disposition status, document
the observed and expected behavior, propose a solution, and record the eventual
resolution.

Disposition decisions are also clickable and include contextual help for
**Fix Planned**, **Deferred**, **Cannot Reproduce**, **Duplicate**,
**Working as Designed**, and **More Information Needed**.

Reports are stored under the current user's home directory:

```text
~/.pinochleMVP/discrepancy_reports
```

Every DR is saved as an editable JSON record and a matching Markdown file. The
Markdown copy can be opened directly or given to Codex/GPT for analysis,
planning, implementation, and verification.

Use **Choose Folder** in the DR manager to redirect future reports to a shared
or synchronized directory. For example, reports created on a Linux laptop can
be written to a mounted Windows share so Codex on the Windows desktop can read
and disposition the same Markdown files.

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

## Project information

- Repository: <https://github.com/doyle2457/pinochleMVP>
- Creator: Doyle C. Dikes (`doyle2457`)
- Hackathon: OpenAI Build Week

This repository currently has no open-source license. Its source is public for
demonstration and evaluation, but no permission to copy, modify, or distribute
it is granted unless a license is added later.
