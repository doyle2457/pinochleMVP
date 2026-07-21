"""Color definitions for the Trickwise table display themes."""


THEMES = {
    "Light": {
        "window": "#f0f0f0",
        "surface": "transparent",
        "text": "#000000",
        "border": "#555555",
        "card_border": "#000000",
        "badge_background": "#ffffff",
        "badge_text": "#000000",
        "muted": "#9e9e9e",
        "hover": "#dddddd",
        # Python syntax-inspired action colors (keyword, type, function).
        "selected": "#af00db",
        "newly_drawn": "#267f99",
        "active_target": "#795e26",
        "target_background": "rgba(121, 94, 38, 45)",
        "idle_target_background": "rgba(255, 255, 255, 18)",
        "app_stylesheet": "",
    },
    "Dark": {
        "window": "#212121",
        "surface": "#2f2f2f",
        "text": "#ececec",
        "border": "#565869",
        "card_border": "#565869",
        "badge_background": "#2f2f2f",
        "badge_text": "#ececec",
        "muted": "#8e8ea0",
        "hover": "#3e3f4b",
        # Codex-dark Python syntax-inspired action colors.
        "selected": "#c586c0",
        "newly_drawn": "#4ec9b0",
        "active_target": "#dcdcaa",
        "target_background": "rgba(220, 220, 170, 45)",
        "idle_target_background": "rgba(255, 255, 255, 12)",
        "app_stylesheet": """
            QMainWindow, QDialog, QWidget {
                background-color: #212121;
                color: #ececec;
            }
            QMenu, QListWidget, QLineEdit {
                background-color: #2f2f2f;
                color: #ececec;
                border: 1px solid #565869;
            }
            QMenu::item:selected, QListWidget::item:selected {
                background-color: #3e3f4b;
            }
            QPushButton, QToolButton {
                background-color: #2f2f2f;
                color: #ececec;
                border: 1px solid #565869;
            }
            QStatusBar {
                background-color: #2f2f2f;
                color: #ececec;
            }
        """,
    },
}

DEFAULT_THEME = "Light"
