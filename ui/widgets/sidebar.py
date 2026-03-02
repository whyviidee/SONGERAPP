"""Sidebar de navegação estilo Spotify."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPixmap

from ui.theme import BG_SIDEBAR, GREEN, TEXT_DIM, TEXT_SEC


def _asset(name: str) -> Path:
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).parents[2]))
    return base / 'assets' / name


class SidebarButton(QPushButton):
    def __init__(self, icon: str, label: str, key: str, parent=None):
        super().__init__(f"  {icon}  {label}", parent)
        self.key = key
        self._active = False
        self.setFixedHeight(40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("Segoe UI", 12))
        self._update_style()

    def set_active(self, active: bool):
        self._active = active
        self._update_style()

    def _update_style(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: #2a2a2a;
                    color: {GREEN};
                    border: none;
                    border-left: 3px solid {GREEN};
                    border-radius: 0;
                    text-align: left;
                    padding-left: 14px;
                    font-weight: 700;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_SEC};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0;
                    text-align: left;
                    padding-left: 14px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: #222;
                    color: #fff;
                }}
            """)


class Sidebar(QWidget):
    page_changed = pyqtSignal(str)

    PAGES = [
        ("🏠", "Início", "home"),
        ("🔍", "Pesquisar", "search"),
        ("🎵", "Playlists", "playlists"),
        ("📥", "Downloads", "queue"),
        ("📚", "Biblioteca", "library"),
        ("📜", "Histórico", "history"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(180)
        self.setStyleSheet(f"background-color: {BG_SIDEBAR};")
        self._buttons: dict[str, SidebarButton] = {}
        self._current = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 12)
        layout.setSpacing(2)

        # ── Logo ───────────────────────────────────────────────────
        logo_row = QHBoxLayout()
        logo_row.setContentsMargins(16, 0, 16, 0)
        logo_row.setSpacing(8)

        logo_path = _asset("logo.png")
        if logo_path.exists():
            pm = QPixmap(str(logo_path)).scaled(
                28, 28,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            img_lbl = QLabel()
            img_lbl.setPixmap(pm)
            img_lbl.setFixedSize(28, 28)
            img_lbl.setStyleSheet("background: transparent;")
            logo_row.addWidget(img_lbl)

        text_lbl = QLabel("SONGER")
        text_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        text_lbl.setStyleSheet(f"color: {GREEN}; letter-spacing: 3px; background: transparent;")
        logo_row.addWidget(text_lbl)
        logo_row.addStretch()

        logo_container = QWidget()
        logo_container.setFixedHeight(44)
        logo_container.setStyleSheet("background: transparent;")
        logo_container.setLayout(logo_row)
        layout.addWidget(logo_container)

        layout.addSpacing(12)

        # ── Menu label ─────────────────────────────────────────────
        menu_lbl = QLabel("   MENU")
        menu_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; font-weight: 700; letter-spacing: 2px; padding-left: 14px;")
        menu_lbl.setFixedHeight(24)
        layout.addWidget(menu_lbl)
        layout.addSpacing(4)

        # ── Botões ─────────────────────────────────────────────────
        for icon, label, key in self.PAGES:
            btn = SidebarButton(icon, label, key)
            btn.clicked.connect(lambda _, k=key: self._on_click(k))
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # ── Fundo: Settings + Sobre ────────────────────────────────
        settings_btn = SidebarButton("⚙", "Definições", "settings")
        settings_btn.clicked.connect(lambda: self.page_changed.emit("settings"))
        layout.addWidget(settings_btn)

        about_btn = SidebarButton("ℹ", "Sobre", "about")
        about_btn.clicked.connect(lambda: self.page_changed.emit("about"))
        layout.addWidget(about_btn)

    def _on_click(self, key: str):
        self.set_active(key)
        self.page_changed.emit(key)

    def set_active(self, key: str):
        self._current = key
        for k, btn in self._buttons.items():
            btn.set_active(k == key)
