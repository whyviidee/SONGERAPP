"""Home Page — dashboard rápido com quick actions + histórico recente."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont

from core.config import Config
from core.app_state import AppState
from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, BG_MAIN, BG_CARD


class _QuickCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon: str, label: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setObjectName("quickCard")
        self.setFixedHeight(80)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QFrame#quickCard {{
                background: {BG_CARD};
                border-radius: 10px;
                border: 1px solid #2a2a2a;
            }}
            QFrame#quickCard:hover {{
                background: #252525;
                border: 1px solid {GREEN};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(2)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont("Segoe UI", 20))
        icon_lbl.setStyleSheet("background: transparent;")
        top.addWidget(icon_lbl)
        top.addStretch()

        label_lbl = QLabel(label)
        label_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        label_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")

        layout.addLayout(top)
        layout.addWidget(label_lbl)
        layout.addWidget(sub_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit()


class HomeView(QWidget):
    navigate = pyqtSignal(str)   # key: search, playlists, queue, library, history
    open_url = pyqtSignal(str)   # abre URL na search view

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self.setObjectName("homeView")
        self.setStyleSheet(f"QWidget#homeView {{ background: {BG_MAIN}; }}")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        content = QWidget()
        content.setObjectName("homeContent")
        content.setStyleSheet(f"QWidget#homeContent {{ background: {BG_MAIN}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(24)

        # --- Greeting ---
        self._greeting = QLabel("Olá!")
        self._greeting.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._greeting.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self._sub = QLabel("O que queres ouvir hoje?")
        self._sub.setStyleSheet(f"color: {TEXT_SEC}; font-size: 14px; background: transparent;")

        layout.addWidget(self._greeting)
        layout.addWidget(self._sub)

        # --- Quick actions ---
        qa_lbl = QLabel("Acções rápidas")
        qa_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        qa_lbl.setStyleSheet(f"color: {TEXT_DIM}; letter-spacing: 1px; background: transparent;")
        layout.addWidget(qa_lbl)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        cards = [
            ("🔍", "Pesquisar", "Buscar música ou playlist", "search"),
            ("🎵", "Playlists", "As tuas playlists", "playlists"),
            ("📥", "Downloads", "Ver fila de downloads", "queue"),
            ("📚", "Biblioteca", "Música descarregada", "library"),
        ]

        for icon, label, sub, key in cards:
            card = _QuickCard(icon, label, sub)
            card.clicked.connect(lambda k=key: self.navigate.emit(k))
            cards_layout.addWidget(card)

        layout.addLayout(cards_layout)

        # --- Stats ---
        self._stats_frame = QFrame()
        self._stats_frame.setObjectName("statsFrame")
        self._stats_frame.setStyleSheet(f"""
            QFrame#statsFrame {{
                background: {BG_CARD};
                border-radius: 10px;
                border: 1px solid #2a2a2a;
            }}
        """)
        stats_layout = QHBoxLayout(self._stats_frame)
        stats_layout.setContentsMargins(20, 14, 20, 14)
        stats_layout.setSpacing(0)

        self._stat_files = self._make_stat("0", "ficheiros")
        self._stat_artists = self._make_stat("0", "artistas")
        self._stat_size = self._make_stat("0 MB", "ocupado")

        stats_layout.addLayout(self._stat_files)
        stats_layout.addStretch()
        stats_layout.addLayout(self._stat_artists)
        stats_layout.addStretch()
        stats_layout.addLayout(self._stat_size)

        layout.addWidget(self._stats_frame)

        # --- Histórico recente ---
        hist_header = QHBoxLayout()
        hist_lbl = QLabel("Recente")
        hist_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        hist_lbl.setStyleSheet(f"color: {TEXT_DIM}; letter-spacing: 1px; background: transparent;")
        clear_btn = QPushButton("Limpar")
        clear_btn.setObjectName("secondary")
        clear_btn.setFixedHeight(26)
        clear_btn.setFixedWidth(70)
        clear_btn.clicked.connect(self._clear_recents)
        hist_header.addWidget(hist_lbl)
        hist_header.addStretch()
        hist_header.addWidget(clear_btn)
        layout.addLayout(hist_header)

        self._hist_container = QWidget()
        self._hist_container.setStyleSheet("background: transparent;")
        self._hist_layout = QVBoxLayout(self._hist_container)
        self._hist_layout.setContentsMargins(0, 0, 0, 0)
        self._hist_layout.setSpacing(4)
        layout.addWidget(self._hist_container)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _make_stat(self, value: str, label: str) -> QVBoxLayout:
        v = QVBoxLayout()
        v.setSpacing(2)
        val = QLabel(value)
        val.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        val.setStyleSheet(f"color: {GREEN}; background: transparent;")
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(val)
        v.addWidget(lbl)
        # store ref by label
        setattr(self, f"_sv_{label.replace(' ', '_')}", val)
        return v

    def refresh(self):
        """Actualiza greeting, stats e histórico recente."""
        state = AppState.instance()
        username = state.get_spotify_username()
        if username:
            self._greeting.setText(f"Olá, {username}!")
        else:
            self._greeting.setText("Olá!")

        # Library stats
        try:
            from core.library import get_library_stats
            base = self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER"))
            stats = get_library_stats(base)
            self._sv_ficheiros.setText(str(stats["total_files"]))
            self._sv_artistas.setText(str(stats["total_artists"]))
            self._sv_ocupado.setText(f"{stats['total_size_mb']:.0f} MB")
        except Exception:
            pass

        # Histórico recente — últimas 5 entradas
        while self._hist_layout.count():
            item = self._hist_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        try:
            from core.history import DownloadHistory
            hist = DownloadHistory()
            entries = hist.get_all()[:5]
            if entries:
                for e in entries:
                    row = self._make_hist_row(e)
                    self._hist_layout.addWidget(row)
            else:
                empty = QLabel("Sem histórico ainda. Começa por pesquisar música!")
                empty.setStyleSheet(f"color: {TEXT_DIM}; font-size: 13px; background: transparent;")
                self._hist_layout.addWidget(empty)
        except Exception:
            pass

    def _make_hist_row(self, e: dict) -> QFrame:
        w = QFrame()
        w.setFixedHeight(46)
        w.setObjectName("histRow")
        w.setStyleSheet(f"""
            QFrame#histRow {{
                background: {BG_CARD};
                border-radius: 8px;
                border: 1px solid #222;
            }}
            QFrame#histRow:hover {{
                background: #252525;
                border: 1px solid {GREEN};
            }}
        """)
        w.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(w)
        layout.setContentsMargins(14, 4, 14, 4)
        layout.setSpacing(10)

        icon = QLabel("🎵")
        icon.setStyleSheet("background: transparent; font-size: 16px;")

        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(e.get("name", ""))
        name.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        name.setStyleSheet(f"color: {TEXT}; background: transparent;")
        detail = QLabel(f"{e.get('done_count', 0)}/{e.get('tracks_count', 0)} tracks  •  {e.get('format', '')}  •  {e.get('date', '')[:10]}")
        detail.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        info.addWidget(name)
        info.addWidget(detail)

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
        url = e.get("url", "")
        play_btn.clicked.connect(lambda checked=False, u=url: self.open_url.emit(u))
        play_btn.setToolTip("Recarregar na pesquisa")

        layout.addWidget(icon)
        layout.addLayout(info, stretch=1)
        layout.addWidget(play_btn)

        # Clicar na row também abre
        w.mousePressEvent = lambda ev, u=url: self.open_url.emit(u) if u else None

        return w

    def _clear_recents(self):
        try:
            from core.history import DownloadHistory
            DownloadHistory().clear()
        except Exception:
            pass
        self.refresh()
