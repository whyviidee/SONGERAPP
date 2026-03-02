"""Tema global do SONGER v2 — Dark Spotify-like com alto contraste."""

# Cores base
BG_DARK = "#1a1a1a"
BG_MAIN = "#232323"
BG_CARD = "#2a2a2a"
BG_HOVER = "#333333"
BG_INPUT = "#333333"
BG_SIDEBAR = "#141414"
BG_HEADER = "#181818"
BG_BOTTOMBAR = "#111111"

GREEN = "#1db954"
GREEN_HOVER = "#22d160"
GREEN_DARK = "#1a3d2a"
RED = "#e05050"
TEXT = "#ffffff"
TEXT_SEC = "#b0b0b0"
TEXT_DIM = "#777777"
BORDER = "#3a3a3a"
BORDER_LIGHT = "#505050"

STYLE = """
/* === Base — só QMainWindow/QDialog, NÃO QWidget global === */
QMainWindow, QDialog {
    background-color: """ + BG_MAIN + """;
    color: """ + TEXT + """;
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}
QLabel { color: """ + TEXT + """; }

/* === Scrollbars === */
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical {
    background: #222; width: 7px; border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #555; border-radius: 3px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #888; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* === Input === */
QLineEdit {
    background-color: """ + BG_INPUT + """;
    border: 1.5px solid """ + BORDER + """;
    border-radius: 20px;
    padding: 8px 16px;
    color: """ + TEXT + """;
    font-size: 13px;
    selection-background-color: """ + GREEN + """;
}
QLineEdit:focus {
    border-color: """ + GREEN + """;
    background-color: #383838;
}

/* === Botão primário (verde) === */
QPushButton {
    background-color: """ + GREEN + """;
    color: #000;
    border: none;
    border-radius: 18px;
    padding: 8px 20px;
    font-weight: 700;
    font-size: 13px;
}
QPushButton:hover { background-color: """ + GREEN_HOVER + """; }
QPushButton:pressed { background-color: #189a47; }
QPushButton:disabled { background-color: #3a3a3a; color: #555; }

/* === Botão secundário === */
QPushButton#secondary {
    background-color: #404040;
    color: #eee;
    border: 1.5px solid #606060;
    border-radius: 18px;
    font-weight: 600;
}
QPushButton#secondary:hover { background-color: #555; border-color: #888; color: #fff; }
QPushButton#secondary:pressed { background-color: #666; }

/* === Botão ghost (ícone) === */
QPushButton#ghost {
    background: transparent;
    color: """ + TEXT_SEC + """;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}
QPushButton#ghost:hover { color: """ + GREEN + """; background: #2a2a2a; }

/* === Botão download track === */
QPushButton#dl_btn {
    background-color: """ + GREEN_DARK + """;
    color: """ + GREEN + """;
    border: 1.5px solid """ + GREEN + """;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 700;
    padding: 0;
}
QPushButton#dl_btn:hover { background-color: """ + GREEN + """; color: #000; }

/* === Botão play preview === */
QPushButton#play_btn {
    background: transparent;
    color: """ + TEXT_SEC + """;
    border: none;
    font-size: 16px;
    padding: 0;
}
QPushButton#play_btn:hover { color: """ + GREEN + """; }
QPushButton#play_btn:disabled { color: #444; background: transparent; }

/* === ComboBox === */
QComboBox {
    background-color: #333;
    color: """ + TEXT + """;
    border: 1.5px solid """ + BORDER + """;
    border-radius: 6px;
    padding: 5px 10px;
    font-size: 12px;
    min-width: 90px;
}
QComboBox:hover { border-color: """ + GREEN + """; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox::down-arrow { image: none; border: none; }
QComboBox QAbstractItemView {
    background: #2a2a2a;
    color: """ + TEXT + """;
    border: 1px solid #444;
    selection-background-color: """ + GREEN + """;
    selection-color: #000;
}

/* === Progress bar === */
QProgressBar {
    background-color: #333;
    border: none;
    border-radius: 3px;
    text-align: center;
}
QProgressBar::chunk { background-color: """ + GREEN + """; border-radius: 3px; }

/* === Tooltip === */
QToolTip {
    background-color: #1e1e1e;
    color: #fff;
    border: 1px solid #505050;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 11px;
}

/* === Tabs (settings) === */
QTabWidget::pane { border: 1px solid #444; background: #232323; }
QTabBar::tab {
    background: #2a2a2a; color: #aaa; padding: 8px 18px;
    border: 1px solid #444; border-bottom: none; border-radius: 4px 4px 0 0;
}
QTabBar::tab:selected { background: #333; color: #fff; }
QTabBar::tab:hover { background: #383838; color: #ddd; }

/* === SpinBox === */
QSpinBox {
    background: #333; color: #fff; border: 1px solid #444;
    border-radius: 4px; padding: 4px 8px;
}

/* === CheckBox === */
QCheckBox { color: #ddd; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1.5px solid #666; border-radius: 3px; background: #333; }
QCheckBox::indicator:checked { background: """ + GREEN + """; border-color: """ + GREEN + """; }
"""
