"""Vista Library — mostra música já descarregada."""

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy, QLineEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.config import Config
from core.library import scan_library, get_library_stats
from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, BG_MAIN


class LibraryView(QWidget):
    play_file = pyqtSignal(str, str, str)  # path, name, artist

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self._all_groups: dict[str, list] = {}
        self.setObjectName("libraryView")
        self.setStyleSheet(f"QWidget#libraryView {{ background: {BG_MAIN}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Biblioteca")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self._stats_lbl = QLabel("")
        self._stats_lbl.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent;")

        refresh_btn = QPushButton("Atualizar")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self.refresh)

        open_btn = QPushButton("📁  Abrir pasta")
        open_btn.setObjectName("secondary")
        open_btn.setFixedHeight(32)
        open_btn.clicked.connect(self._open_folder)

        header.addWidget(title)
        header.addWidget(self._stats_lbl)
        header.addStretch()
        header.addWidget(open_btn)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Filtro
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filtrar por artista ou nome...")
        self._filter.setFixedHeight(34)
        self._filter.setStyleSheet(f"""
            QLineEdit {{
                background: #1e1e1e;
                border: 1px solid #333;
                border-radius: 6px;
                color: {TEXT};
                padding: 0 10px;
                font-size: 12px;
            }}
            QLineEdit:focus {{ border: 1px solid {GREEN}; }}
        """)
        self._filter.textChanged.connect(self._apply_filter)
        layout.addWidget(self._filter)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        self._list_widget = QWidget()
        self._list_widget.setObjectName("libraryList")
        self._list_widget.setStyleSheet(f"QWidget#libraryList {{ background: {BG_MAIN}; }}")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, stretch=1)

    def refresh(self):
        base = self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER"))

        # Stats
        stats = get_library_stats(base)
        self._stats_lbl.setText(
            f"{stats['total_files']} ficheiros  •  "
            f"{stats['total_artists']} artistas  •  "
            f"{stats['total_size_mb']:.0f} MB"
        )

        # Scan e agrupar por artista
        files = scan_library(base)
        self._all_groups = {}
        for f in files:
            key = f["artist"] or "Outros"
            self._all_groups.setdefault(key, []).append(f)

        self._apply_filter(self._filter.text())

    def _apply_filter(self, text: str):
        q = text.strip().lower()

        # Limpar lista
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for artist, artist_files in sorted(self._all_groups.items()):
            # Filtrar ficheiros que batem com o query
            if q:
                filtered = [f for f in artist_files if q in f["name"].lower() or q in artist.lower()]
            else:
                filtered = artist_files

            if not filtered:
                continue

            lbl = QLabel(f"  {artist}  ({len(filtered)})")
            lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {GREEN}; padding-top: 6px; background: transparent;")
            self._list_layout.insertWidget(self._list_layout.count() - 1, lbl)

            for f in filtered:
                row = self._make_row(f)
                self._list_layout.insertWidget(self._list_layout.count() - 1, row)

    def _make_row(self, f: dict) -> QFrame:
        w = QFrame()
        w.setFixedHeight(36)
        w.setObjectName("lib_row")
        w.setStyleSheet(f"""
            QFrame#lib_row {{
                background: transparent;
                border-radius: 4px;
            }}
            QFrame#lib_row:hover {{
                background: #2e2e2e;
            }}
        """)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(24, 2, 12, 2)
        layout.setSpacing(8)

        name = QLabel(f["name"])
        name.setStyleSheet(f"color: {TEXT}; font-size: 12px; background: transparent;")
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        ext = QLabel(f["ext"].upper())
        ext.setFixedWidth(40)
        ext.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        ext.setAlignment(Qt.AlignmentFlag.AlignCenter)

        size = QLabel(f"{f['size_mb']} MB")
        size.setFixedWidth(50)
        size.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        size.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        play_btn = QPushButton("▶")
        play_btn.setFixedSize(28, 28)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {GREEN};
                border: 1px solid {GREEN};
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
                padding: 0;
                padding-left: 2px;
            }}
            QPushButton:hover {{ background: {GREEN}; color: #000; }}
        """)
        play_btn.setToolTip("Reproduzir")
        path = f.get("path", "")
        artist = f.get("artist", "")
        fname = f.get("name", "")
        play_btn.clicked.connect(lambda checked=False, p=path, n=fname, a=artist: self.play_file.emit(p, n, a))

        layout.addWidget(name, stretch=1)
        layout.addWidget(ext)
        layout.addWidget(size)
        layout.addWidget(play_btn)

        # Duplo clique na row também faz play
        w.mouseDoubleClickEvent = lambda ev, p=path, n=fname, a=artist: self.play_file.emit(p, n, a)

        return w

    def _open_folder(self):
        folder = self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER"))
        Path(folder).mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')
