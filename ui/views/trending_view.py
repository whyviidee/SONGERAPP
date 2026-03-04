"""Trending Tracks — view escondida (Ctrl+Shift+T).

Lê os .md de GIGS/TRENDING-TRACKS/ e permite buscar qualquer track.
"""

from __future__ import annotations

import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from ui.theme import (
    BG_CARD, BG_HOVER, GREEN, TEXT, TEXT_SEC, TEXT_DIM, BORDER, BG_MAIN,
)

# Caminho para os ficheiros trending (relativo ao trending_view.py)
# trending_view.py → views → ui → SONGER → music-tools → PROJECTOS → CLAUDECODEHOUSE
_TRENDING_DIR = Path(__file__).parents[2] / "tools" / "trending"

_CATEGORY_LABELS = {
    "portugal-top50":        "🇵🇹  Portugal Top 50",
    "funk-brasil":           "🇧🇷  Funk Brasil",
    "reggaeton":             "🎤  Reggaeton",
    "house":                 "🎛️  House Music",
    "amapiano":              "🥁  Amapiano",
    "afro-house-electronic": "⚡  Afro House — Electrónico",
    "afro-house-african":    "🌍  Afro House — Africano",
    "underground-remixes":   "🔊  Underground Remixes",
}

# regex para linha de track no .md
# - ARTIST — TITLE  \n  [Spotify/SoundCloud](URL)
_TRACK_RE = re.compile(
    r'^- (.+?) — (.+?)\s*\n\s*\[(?:Spotify|SoundCloud)\]\((https?://[^\)]+)\)',
    re.MULTILINE,
)


def _parse_md(path: Path) -> list[dict]:
    """Extrai lista de {artist, title, url} de um ficheiro .md."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    tracks = []
    for m in _TRACK_RE.finditer(text):
        tracks.append({
            "artist": m.group(1).strip(),
            "title":  m.group(2).strip(),
            "url":    m.group(3).strip(),
        })
    return tracks


class _TrackRow(QFrame):
    search_clicked = pyqtSignal(str)  # emite URL ou query texto

    def __init__(self, index: int, track: dict, parent=None):
        super().__init__(parent)
        self._track = track
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border-bottom: 1px solid {BORDER};
            }}
            QFrame:hover {{
                background: {BG_HOVER};
            }}
        """)
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(10)

        # Número
        num = QLabel(f"{index}.")
        num.setFixedWidth(28)
        num.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; border: none; background: transparent;")
        num.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Artista — Título
        label_text = f"<b>{self._escape(track['artist'])}</b> — {self._escape(track['title'])}"
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {TEXT}; font-size: 12px; border: none; background: transparent;")
        label.setTextFormat(Qt.TextFormat.RichText)

        # Botão buscar
        btn = QPushButton("↗ Buscar")
        btn.setObjectName("secondary")
        btn.setFixedSize(74, 26)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._on_search)

        layout.addWidget(num)
        layout.addWidget(label, stretch=1)
        layout.addWidget(btn)

    def _escape(self, s: str) -> str:
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _on_search(self):
        url = self._track["url"]
        # Se for Spotify, passa o URL directamente; se não, passa "artist title" como query
        if "spotify.com" in url:
            self.search_clicked.emit(url)
        else:
            self.search_clicked.emit(f"{self._track['artist']} {self._track['title']}")


class TrendingView(QWidget):
    open_url = pyqtSignal(str)  # URL Spotify ou query texto → main_window trata

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {BG_MAIN};")
        self._current_key: str = ""
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)

        title = QLabel("⚡ Trending")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        hint = QLabel("Ctrl+Shift+T  ·  só para ti")
        hint.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        hint.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        hdr.addWidget(title)
        hdr.addStretch()
        hdr.addWidget(hint)
        layout.addLayout(hdr)
        layout.addSpacing(16)

        # ── Selector de categoria ──────────────────────────────────────
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        cat_lbl = QLabel("Categoria:")
        cat_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")

        self._combo = QComboBox()
        self._combo.setFixedWidth(260)
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1.5px solid {BORDER};
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
            }}
            QComboBox:hover {{ border-color: {GREEN}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: #2a2a2a; color: {TEXT};
                border: 1px solid #444;
                selection-background-color: {GREEN};
                selection-color: #000;
            }}
        """)

        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")

        row.addWidget(cat_lbl)
        row.addWidget(self._combo)
        row.addWidget(self._count_lbl)
        row.addStretch()
        layout.addLayout(row)
        layout.addSpacing(12)

        # ── Lista de tracks ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._list_container = QWidget()
        self._list_container.setStyleSheet(f"background: {BG_CARD}; border-radius: 8px;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(0)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, stretch=1)

        # ── Popular categorias ─────────────────────────────────────────
        self._load_categories()
        self._combo.currentIndexChanged.connect(self._on_category_changed)

        # Mostrar primeira categoria se existir
        if self._combo.count() > 0:
            self._load_tracks(self._combo.currentData())

    def _load_categories(self):
        """Descobre os .md disponíveis e popula o combo."""
        if not _TRENDING_DIR.exists():
            self._combo.addItem("⚠ Pasta não encontrada", "")
            return

        found = False
        for key, label in _CATEGORY_LABELS.items():
            path = _TRENDING_DIR / f"{key}.md"
            if path.exists():
                self._combo.addItem(label, key)
                found = True

        if not found:
            self._combo.addItem("⚠ Sem ficheiros .md", "")

    def _on_category_changed(self, _index: int):
        key = self._combo.currentData()
        if key:
            self._load_tracks(key)

    def _load_tracks(self, key: str):
        """Lê o .md e actualiza a lista."""
        # Limpar lista actual
        while self._list_layout.count() > 1:  # preserva o stretch no fim
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        path = _TRENDING_DIR / f"{key}.md"
        tracks = _parse_md(path)

        if not tracks:
            empty = QLabel("Sem tracks ou ficheiro não encontrado.")
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 20px; background: transparent;")
            self._list_layout.insertWidget(0, empty)
            self._count_lbl.setText("")
            return

        self._count_lbl.setText(f"{len(tracks)} tracks")

        for i, track in enumerate(tracks, 1):
            row = _TrackRow(i, track)
            row.search_clicked.connect(self.open_url.emit)
            self._list_layout.insertWidget(i - 1, row)

    def refresh(self):
        """Re-lê o ficheiro da categoria actual."""
        key = self._combo.currentData()
        if key:
            self._load_tracks(key)
