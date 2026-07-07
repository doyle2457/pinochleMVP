# pinochleMVP/layout_proportional.py


def proportional_position(table_w, table_h, x_frac, y_frac):
    """Return (x, y) based on fractional coordinates."""
    return int(table_w * x_frac), int(table_h * y_frac)


def proportional_card_rect(table_w, table_h, x_frac, y_frac, w_frac, h_frac):
    """Return QRect for a card based on fractional geometry."""
    from PyQt5.QtCore import QRect

    x = int(table_w * x_frac)
    y = int(table_h * y_frac)
    w = int(table_w * w_frac)
    h = int(table_h * h_frac)
    return QRect(x, y, w, h)
