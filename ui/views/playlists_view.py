"""Vista 'Minhas Playlists' — mostra playlists da conta Spotify."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy, QProgressBar,
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QUrl
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.config import Config
from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, BG_CARD, BG_MAIN


class PlaylistsLoader(QThread):
    loaded = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    def run(self):
        try:
            from core.spotify import SpotifyClient
            sp = SpotifyClient(
                self.config.get("spotify", "client_id", default=""),
                self.config.get("spotify", "client_secret", default=""),
            )
            if not sp.connect():
                self.error.emit("Spotify não ligado.")
                return
            playlists = sp.get_my_playlists()
            self.loaded.emit(playlists)
        except Exception as e:
            self.error.emit(str(e))


class PlaylistCard(QFrame):
    open_clicked = pyqtSignal(str)  # URL

    def __init__(self, playlist: dict, parent=None):
        super().__init__(parent)
        self._playlist = playlist
        self._net = QNetworkAccessManager(self)
        self.setFixedHeight(72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("playlist_card")
        self.setStyleSheet(f"""
            QFrame#playlist_card {{
                background: {BG_CARD};
                border-radius: 8px;
                border: 1px solid transparent;
            }}
            QFrame#playlist_card:hover {{
                background: #363636;
                border: 1px solid #444;
            }}
        """)
        self._build()

        cover_url = playlist.get("cover_url", "")
        if cover_url:
            self._load_cover(cover_url)

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 14, 8)
        layout.setSpacing(12)

        # Cover
        self._cover = QLabel("🎵")
        self._cover.setFixedSize(54, 54)
        self._cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cover.setStyleSheet("background: #333; border-radius: 4px; font-size: 20px;")
        self._cover.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self._cover)

        # Info
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(self._playlist.get("name", ""))
        name.setFont(QFont("Segoe UI", 12, QFont.Weight.Medium))
        name.setStyleSheet(f"color: {TEXT}; background: transparent;")
        name.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        meta_parts = []
        total = self._playlist.get("total_tracks", 0)
        if total:
            meta_parts.append(f"{total} tracks")
        owner = self._playlist.get("owner", "")
        if owner:
            meta_parts.append(owner)
        meta = QLabel("  •  ".join(meta_parts))
        meta.setStyleSheet(f"color: {TEXT_SEC}; font-size: 11px; background: transparent;")
        meta.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        info.addWidget(name)
        info.addWidget(meta)
        layout.addLayout(info, stretch=1)

        # Arrow
        arrow = QLabel("→")
        arrow.setFixedWidth(20)
        arrow.setStyleSheet(f"color: {TEXT_DIM}; font-size: 16px; background: transparent;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(arrow)

    def _load_cover(self, url: str):
        reply = self._net.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_loaded(reply))

    def _on_loaded(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                self._cover.setPixmap(px.scaled(54, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self._cover.setStyleSheet("border-radius: 4px;")
        reply.deleteLater()

    def mousePressEvent(self, _event):
        url = self._playlist.get("url", "")
        if url:
            self.open_clicked.emit(url)


class PlaylistsView(QWidget):
    open_playlist = pyqtSignal(str)  # URL da playlist a abrir na search view

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self._loader = None
        self.setObjectName("playlistsView")
        self.setStyleSheet(f"QWidget#playlistsView {{ background: {BG_MAIN}; }}")
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 8)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Minhas Playlists")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")

        self._refresh_btn = QPushButton("Atualizar")
        self._refresh_btn.setObjectName("secondary")
        self._refresh_btn.setFixedHeight(32)
        self._refresh_btn.clicked.connect(self.refresh)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self._refresh_btn)
        layout.addLayout(header)

        # Status
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent;")
        layout.addWidget(self._status)

        # Loading bar (indeterminate)
        self._loading_bar = QProgressBar()
        self._loading_bar.setMinimum(0)
        self._loading_bar.setMaximum(0)
        self._loading_bar.setFixedHeight(3)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setStyleSheet(f"""
            QProgressBar {{ background: #2a2a2a; border: none; border-radius: 1px; }}
            QProgressBar::chunk {{ background: {GREEN}; border-radius: 1px; }}
        """)
        self._loading_bar.hide()
        layout.addWidget(self._loading_bar)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        self._list_widget = QWidget()
        self._list_widget.setObjectName("playlistsList")
        self._list_widget.setStyleSheet(f"QWidget#playlistsList {{ background: {BG_MAIN}; }}")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        layout.addWidget(scroll, stretch=1)

    def refresh(self):
        if not self._config.get("spotify", "client_id", default=""):
            self._status.setText("⚠ Spotify não configurado.")
            return

        self._status.setText("A carregar playlists...")
        self._refresh_btn.setEnabled(False)
        self._loading_bar.show()

        self._loader = PlaylistsLoader(self._config)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.error.connect(self._on_error)
        self._loader.start()

    def _on_loaded(self, playlists: list):
        # Limpar
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for p in playlists:
            card = PlaylistCard(p)
            card.open_clicked.connect(self.open_playlist.emit)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)

        self._loading_bar.hide()
        self._status.setText(f"{len(playlists)} playlists")
        self._refresh_btn.setEnabled(True)

    def _on_error(self, msg: str):
        self._loading_bar.hide()
        self._status.setText(f"Erro: {msg}")
        self._refresh_btn.setEnabled(True)
