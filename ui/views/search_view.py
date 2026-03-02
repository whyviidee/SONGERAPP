"""Vista de pesquisa — aceita URLs Spotify E texto livre."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal, Qt, QThread, QUrl
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from core.config import Config
from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, BG_MAIN
from core.app_state import AppState
from ui.widgets.album_header import AlbumHeader
from ui.widgets.track_list import TrackList

# Paleta extra
ACCENT = "#1db954"
BG_ELEVATED = "#1e1e1e"
BG_HOVER = "#2a2a2a"
BORDER_DIM = "#333333"
BORDER_ACCENT = "#1db95450"


# ------------------------------------------------------------------
# Workers
# ------------------------------------------------------------------

class LoadWorker(QThread):
    """Carrega tracks de um URL Spotify — detecta tipo automaticamente."""
    tracks_loaded = pyqtSignal(list, str, str, str, list)  # tracks, name, cover_url, url_type, albums
    error = pyqtSignal(str)

    def __init__(self, url: str, config: Config):
        super().__init__()
        self.url = url
        self.config = config

    def run(self):
        try:
            from core.spotify import SpotifyClient
            sp = SpotifyClient(
                self.config.get("spotify", "client_id", default=""),
                self.config.get("spotify", "client_secret", default=""),
            )
            if not sp.connect():
                self.error.emit("Spotify não está ligado. Vai a Definições e faz login.")
                return

            kind, id_ = sp.parse_link(self.url)
            albums: list = []

            if kind == "artist":
                tracks, name = sp.get_artist_top_tracks(id_)
                cover = tracks[0].get("cover_url", "") if tracks else ""
                albums = sp.get_artist_albums(id_)
            elif kind == "track":
                tracks, name, _ = sp.get_track_with_album(id_)
                cover = tracks[0].get("cover_url", "") if tracks else ""
            else:
                tracks, name = sp.get_tracks(self.url)
                cover = tracks[0].get("cover_url", "") if tracks else ""

            self.tracks_loaded.emit(tracks, name, cover, kind or "", albums)
        except Exception as e:
            self.error.emit(str(e))


class SearchWorker(QThread):
    """Pesquisa texto no Spotify."""
    results_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, query: str, config: Config):
        super().__init__()
        self.query = query
        self.config = config

    def run(self):
        try:
            from core.spotify import SpotifyClient
            sp = SpotifyClient(
                self.config.get("spotify", "client_id", default=""),
                self.config.get("spotify", "client_secret", default=""),
            )
            if not sp.connect():
                self.error.emit("Spotify não está ligado.")
                return
            results = sp.search(self.query)
            self.results_ready.emit(results)
        except Exception as e:
            self.error.emit(str(e))


# ------------------------------------------------------------------
# Result cards (para search results)
# ------------------------------------------------------------------

class ResultCard(QFrame):
    clicked = pyqtSignal(str)  # emite URL

    def __init__(self, title: str, subtitle: str, url: str, icon_letter: str = "",
                 icon_color: str = ACCENT, cover_url: str = "", circle: bool = True, parent=None):
        super().__init__(parent)
        self.url = url
        self._icon_color = icon_color
        self._circle = circle
        self._net = None
        self.setFixedHeight(60)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("result_card")
        self.setStyleSheet(f"""
            QFrame#result_card {{
                background: {BG_ELEVATED};
                border-radius: 10px;
                border: 1px solid {BORDER_DIM};
            }}
            QFrame#result_card:hover {{
                background: {BG_HOVER};
                border: 1px solid {ACCENT}88;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 14, 8)
        layout.setSpacing(10)

        # Avatar (letra como placeholder, substituído por imagem se cover_url)
        radius = "18px" if circle else "6px"
        self._avatar = QLabel(icon_letter.upper()[:1] if icon_letter else "")
        self._avatar.setFixedSize(36, 36)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setStyleSheet(f"""
            background: {icon_color}22;
            color: {icon_color};
            border-radius: {radius};
            font-size: 14px;
            font-weight: bold;
            border: 1px solid {icon_color}44;
        """)
        self._avatar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout.addWidget(self._avatar)

        if cover_url:
            self._load_cover(cover_url)

        info = QVBoxLayout()
        info.setSpacing(2)
        t = QLabel(title)
        t.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
        t.setStyleSheet(f"color: {TEXT}; background: transparent;")
        t.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        s = QLabel(subtitle)
        s.setStyleSheet(f"color: {TEXT_SEC}; font-size: 10px; background: transparent;")
        s.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        info.addWidget(t)
        info.addWidget(s)

        arrow = QLabel("›")
        arrow.setFixedWidth(18)
        arrow.setStyleSheet(f"color: {ACCENT}; font-size: 18px; font-weight: bold; background: transparent;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout.addLayout(info, stretch=1)
        layout.addWidget(arrow)

    def _load_cover(self, url: str):
        self._net = QNetworkAccessManager(self)
        reply = self._net.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._on_cover(reply))

    def _on_cover(self, reply: QNetworkReply):
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            px = QPixmap()
            px.loadFromData(data)
            if not px.isNull():
                px = px.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
                if self._circle:
                    rounded = QPixmap(36, 36)
                    rounded.fill(Qt.GlobalColor.transparent)
                    painter = QPainter(rounded)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    path = QPainterPath()
                    path.addEllipse(0, 0, 36, 36)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, px)
                    painter.end()
                    px = rounded
                self._avatar.setPixmap(px)
                radius = "18px" if self._circle else "6px"
                self._avatar.setStyleSheet(f"border-radius: {radius}; border: 1px solid {self._icon_color}44;")
        reply.deleteLater()

    def mousePressEvent(self, _event):
        if self.url:
            self.clicked.emit(self.url)


class AlbumCard(QFrame):
    """Card compacto para discografia (artista)."""
    clicked = pyqtSignal(str)

    def __init__(self, name: str, year: str, album_type: str, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self.setFixedHeight(52)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("album_card")
        self.setStyleSheet(f"""
            QFrame#album_card {{
                background: {BG_ELEVATED};
                border-radius: 8px;
                border: 1px solid {BORDER_DIM};
            }}
            QFrame#album_card:hover {{
                background: {BG_HOVER};
                border: 1px solid {ACCENT}66;
            }}
        """)

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 6, 12, 6)
        row.setSpacing(10)

        # Ícone tipo
        type_colors = {"album": ("#1db954", "LP"), "single": ("#e8a030", "SG"), "compilation": ("#c060d0", "CP")}
        color, badge = type_colors.get(album_type, ("#888", "?"))
        badge_lbl = QLabel(badge)
        badge_lbl.setFixedSize(32, 32)
        badge_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_lbl.setStyleSheet(f"""
            background: {color}22;
            color: {color};
            border-radius: 6px;
            font-size: 9px;
            font-weight: bold;
            border: 1px solid {color}44;
        """)
        badge_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        info = QVBoxLayout()
        info.setSpacing(1)
        n = QLabel(name)
        n.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        n.setStyleSheet(f"color: {TEXT}; background: transparent;")
        n.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        y = QLabel(year)
        y.setStyleSheet(f"color: {TEXT_DIM}; font-size: 10px; background: transparent;")
        y.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        info.addWidget(n)
        info.addWidget(y)

        arrow = QLabel("›")
        arrow.setFixedWidth(16)
        arrow.setStyleSheet(f"color: {ACCENT}; font-size: 16px; font-weight: bold; background: transparent;")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        row.addWidget(badge_lbl)
        row.addLayout(info, stretch=1)
        row.addWidget(arrow)

    def mousePressEvent(self, event):
        if self.url:
            self.clicked.emit(self.url)


# ------------------------------------------------------------------
# Search View
# ------------------------------------------------------------------

class SearchView(QWidget):
    download_track = pyqtSignal(dict, str, str)  # track, fmt, source
    download_all = pyqtSignal(list, str, str)     # tracks, fmt, source
    play_track = pyqtSignal(dict, str)            # track, path

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config
        self._tracks: list[dict] = []
        self._current_url: str = ""
        self._current_name: str = ""
        self._worker = None
        self._history: list[dict] = []       # estado anterior para botão voltar
        self._last_results: dict = {}         # últimos resultados de texto
        self._in_text_results: bool = False   # está a mostrar resultados de pesquisa
        self.setObjectName("searchView")
        self.setStyleSheet(f"QWidget#searchView {{ background: {BG_MAIN}; }}")
        self._build()
        AppState.instance().spotify_status_changed.connect(self._on_spotify_status)
        if not self._config.get("spotify", "client_id", default=""):
            self._onboarding_banner.show()

    def _build(self):
        from PyQt6.QtWidgets import QProgressBar

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 10)
        layout.setSpacing(14)

        # ── Search bar glamour ─────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self._back_btn = QPushButton("‹ Voltar")
        self._back_btn.setFixedHeight(44)
        self._back_btn.setFixedWidth(90)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ELEVATED};
                color: {TEXT_SEC};
                border: 1px solid {BORDER_DIM};
                border-radius: 22px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
            }}
        """)
        self._back_btn.clicked.connect(self._on_back)
        self._back_btn.hide()
        search_row.addWidget(self._back_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Pesquisar artista, álbum ou colar link do Spotify...")
        self._input.setFixedHeight(44)
        self._input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_ELEVATED};
                color: {TEXT};
                border: 1px solid {BORDER_DIM};
                border-radius: 22px;
                padding: 0 18px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
                background: #242424;
            }}
        """)
        self._input.returnPressed.connect(self._on_search)

        self._search_btn = QPushButton("Pesquisar")
        self._search_btn.setFixedHeight(44)
        self._search_btn.setFixedWidth(120)
        self._search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #000;
                border: none;
                border-radius: 22px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: #22c95e; }}
            QPushButton:pressed {{ background: #179945; }}
            QPushButton:disabled {{ background: #333; color: #666; }}
        """)
        self._search_btn.clicked.connect(self._on_search)

        search_row.addWidget(self._input, stretch=1)
        search_row.addWidget(self._search_btn)
        layout.addLayout(search_row)

        # ── Banner onboarding ──────────────────────────────────────
        self._onboarding_banner = QFrame()
        self._onboarding_banner.setObjectName("onboarding_banner")
        self._onboarding_banner.setStyleSheet("""
            QFrame#onboarding_banner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2a1a00, stop:1 #1a1000);
                border: 1px solid #664400;
                border-radius: 10px;
            }
        """)
        self._onboarding_banner.setFixedHeight(46)
        banner_layout = QHBoxLayout(self._onboarding_banner)
        banner_layout.setContentsMargins(16, 0, 12, 0)

        banner_lbl = QLabel("Spotify não configurado — faz login nas Definições")
        banner_lbl.setStyleSheet("color: #ffaa33; font-size: 12px; background: transparent;")

        banner_btn = QPushButton("Configurar →")
        banner_btn.setFixedHeight(28)
        banner_btn.setFixedWidth(100)
        banner_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        banner_btn.setStyleSheet("""
            QPushButton {
                background: #664400;
                color: #ffaa33;
                border: 1px solid #886600;
                border-radius: 14px;
                padding: 0 10px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background: #885500; }
        """)
        banner_btn.clicked.connect(self._on_open_settings)

        banner_layout.addWidget(banner_lbl, stretch=1)
        banner_layout.addWidget(banner_btn)
        layout.addWidget(self._onboarding_banner)
        self._onboarding_banner.hide()

        # ── Loading bar ────────────────────────────────────────────
        self._loading_bar = QProgressBar()
        self._loading_bar.setMinimum(0)
        self._loading_bar.setMaximum(0)
        self._loading_bar.setFixedHeight(2)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setStyleSheet(f"""
            QProgressBar {{ background: transparent; border: none; }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {ACCENT}, stop:1 #22d46a);
                border-radius: 1px;
            }}
        """)
        self._loading_bar.hide()
        layout.addWidget(self._loading_bar)

        # ── Album header ───────────────────────────────────────────
        self._header = AlbumHeader()
        self._header.download_all_clicked.connect(self._on_download_all)
        layout.addWidget(self._header)

        # ── Search results (texto) ─────────────────────────────────
        self._results_widget = QWidget()
        self._results_widget.setStyleSheet("background: transparent;")
        self._results_layout = QVBoxLayout(self._results_widget)
        self._results_layout.setContentsMargins(0, 0, 4, 0)
        self._results_layout.setSpacing(5)

        self._results_scroll = QScrollArea()
        self._results_scroll.setWidgetResizable(True)
        self._results_scroll.setWidget(self._results_widget)
        self._results_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._results_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1a1a1a; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #444; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #1db954; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        self._results_scroll.hide()

        # ── Track list ─────────────────────────────────────────────
        self._track_list = TrackList()
        self._track_list.download_clicked.connect(self._on_track_download)
        self._track_list.play_clicked.connect(self.play_track)

        layout.addWidget(self._results_scroll)
        layout.addWidget(self._track_list, stretch=1)

        # ── Discografia (artistas) ─────────────────────────────────
        self._albums_section = QWidget()
        self._albums_section.setStyleSheet("background: transparent;")
        self._albums_section.hide()
        albums_layout = QVBoxLayout(self._albums_section)
        albums_layout.setContentsMargins(0, 4, 0, 0)
        albums_layout.setSpacing(8)

        disc_header = QHBoxLayout()
        disc_lbl = QLabel("DISCOGRAFIA")
        disc_lbl.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 3px;
            background: transparent;
        """)
        disc_header.addWidget(disc_lbl)
        disc_header.addStretch()
        albums_layout.addLayout(disc_header)

        albums_scroll = QScrollArea()
        albums_scroll.setFixedHeight(200)
        albums_scroll.setWidgetResizable(True)
        albums_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        albums_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1a1a1a; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #444; border-radius: 3px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #1db954; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        self._albums_container = QWidget()
        self._albums_container.setStyleSheet("background: transparent;")
        self._albums_list_layout = QVBoxLayout(self._albums_container)
        self._albums_list_layout.setContentsMargins(0, 0, 4, 0)
        self._albums_list_layout.setSpacing(5)
        self._albums_list_layout.addStretch()
        albums_scroll.setWidget(self._albums_container)
        albums_layout.addWidget(albums_scroll)

        layout.addWidget(self._albums_section)

        # ── Status bar ─────────────────────────────────────────────
        self._status = QLabel("")
        self._status.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; background: transparent; padding-left: 4px;")
        layout.addWidget(self._status)

    def _on_spotify_status(self, connected: bool, _username: str):
        if connected:
            self._onboarding_banner.hide()
        elif not self._config.get("spotify", "client_id", default=""):
            self._onboarding_banner.show()

    def _on_open_settings(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, '_open_settings'):
                parent._open_settings()
                return
            parent = parent.parent()

    def _on_search(self):
        text = self._input.text().strip()
        if not text:
            return

        if not self._config.get("spotify", "client_id", default=""):
            self._status.setText("⚠ Vai a Definições → Spotify e faz login.")
            return

        self._search_btn.setEnabled(False)
        self._search_btn.setText("...")

        if "spotify.com/" in text or "spotify:" in text:
            self._load_url(text)
        else:
            self._search_text(text)

    def _load_url(self, url: str):
        # Guardar estado se estivermos a mostrar resultados de pesquisa de texto
        if self._in_text_results and self._last_results:
            self._history.append({
                "query": self._input.text(),
                "results": self._last_results,
            })
            self._back_btn.show()

        self._in_text_results = False
        self._current_url = url
        self._status.setText("A carregar...")
        self._results_scroll.hide()
        self.layout().setStretchFactor(self._results_scroll, 0)
        self._track_list.show()

        self._loading_bar.show()
        self._worker = LoadWorker(url, self._config)
        self._worker.tracks_loaded.connect(self._on_tracks_loaded)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _search_text(self, query: str):
        self._status.setText(f"A pesquisar '{query}'...")
        self._header.hide()
        self._track_list.clear()
        self._results_scroll.show()
        self.layout().setStretchFactor(self._results_scroll, 1)

        self._loading_bar.show()
        self._worker = SearchWorker(query, self._config)
        self._worker.results_ready.connect(self._on_search_results)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_tracks_loaded(self, tracks: list, name: str, cover_url: str, url_type: str, albums: list):
        self._tracks = tracks
        self._current_name = name
        count = len(tracks)

        artist = tracks[0].get("album_artist", "") if tracks else ""
        header_title = f"{name} — Top Tracks" if url_type == "artist" else name
        self._header.set_info(header_title, artist, cover_url, track_count=count)
        self._track_list.set_tracks(tracks)
        self._track_list.show()
        self._results_scroll.hide()

        if url_type == "artist" and albums:
            from PyQt6.QtCore import QTimer
            self._track_list.setMaximumHeight(260)
            self._albums_section.show()
            QTimer.singleShot(0, lambda: self._populate_albums(albums))
        else:
            self._track_list.setMaximumHeight(16777215)
            self._albums_section.hide()

        self._loading_bar.hide()
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Pesquisar")
        status = f"{count} tracks"
        if url_type == "artist" and albums:
            status += f" • {len(albums)} álbuns"
        self._status.setText(status)

    def _populate_albums(self, albums: list):
        # Limpar cards anteriores (manter o stretch no final)
        while self._albums_list_layout.count() > 1:
            item = self._albums_list_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        for a in albums:
            card = AlbumCard(
                name=a.get("name", ""),
                year=a.get("year", ""),
                album_type=a.get("album_type", "album"),
                url=a.get("url", ""),
            )
            card.clicked.connect(self._load_url)
            self._albums_list_layout.insertWidget(self._albums_list_layout.count() - 1, card)

    def _on_search_results(self, results: dict):
        from PyQt6.QtCore import QTimer
        self._loading_bar.hide()
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Pesquisar")
        # Deferir criação de widgets para o próximo tick — evita crash Qt6 macOS ARM64
        # (QPalette::resolve crashava quando QNetworkAccessManager threads estavam activos)
        QTimer.singleShot(0, lambda: self._fill_search_results(results))

    def _fill_search_results(self, results: dict):
        self._last_results = results
        self._in_text_results = True

        # Limpar resultados anteriores
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        tracks = results.get("tracks", [])
        albums = results.get("albums", [])
        artists = results.get("artists", [])

        def _section_label(text: str, color: str = ACCENT) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: 700; letter-spacing: 3px; background: transparent; padding: 4px 0 2px 0;")
            return lbl

        if artists:
            self._results_layout.addWidget(_section_label("ARTISTAS", "#e040fb"))
            for ar in artists[:5]:
                genres = ", ".join(ar.get("genres", []))
                card = ResultCard(ar["name"], genres or "Artista", ar.get("url", ""),
                                  icon_letter=ar["name"], icon_color="#e040fb",
                                  cover_url=ar.get("cover_url", ""), circle=True)
                card.clicked.connect(self._load_url)
                self._results_layout.addWidget(card)
            self._results_layout.addSpacing(6)

        if albums:
            self._results_layout.addWidget(_section_label("ALBUMS", "#e8a030"))
            for a in albums[:5]:
                card = ResultCard(a["name"], f"{a['artist']} • {a.get('year', '')}", a.get("url", ""),
                                  icon_letter=a["name"], icon_color="#e8a030",
                                  cover_url=a.get("cover_url", ""), circle=False)
                card.clicked.connect(self._load_url)
                self._results_layout.addWidget(card)
            self._results_layout.addSpacing(6)

        if tracks:
            self._results_layout.addWidget(_section_label("TRACKS", ACCENT))
            self._tracks = tracks
            self._header.hide()
            self._track_list.set_tracks(tracks)
            self._track_list.show()

        self._results_layout.addStretch()
        total = len(tracks) + len(albums) + len(artists)
        self._status.setText(f"{total} resultados encontrados.")

    def _on_back(self):
        if not self._history:
            return
        state = self._history.pop()
        self._input.setText(state["query"])
        self._header.hide()
        self._albums_section.hide()
        self._track_list.setMaximumHeight(16777215)
        self._results_scroll.show()
        self.layout().setStretchFactor(self._results_scroll, 1)
        self._fill_search_results(state["results"])
        if not self._history:
            self._back_btn.hide()

    def _on_error(self, msg: str):
        self._loading_bar.hide()
        self._search_btn.setEnabled(True)
        self._search_btn.setText("Pesquisar")
        self._status.setText(f"Erro: {msg}")

    def _on_track_download(self, track: dict):
        fmt = self._header.get_format() if self._header.isVisible() else "mp3_320"
        source = self._header.get_source() if self._header.isVisible() else "hybrid"
        self.download_track.emit(track, fmt, source)

    def _on_download_all(self, fmt: str, source: str):
        if self._tracks:
            self.download_all.emit(self._tracks, fmt, source)

    def load_from_url(self, url: str):
        """Chamado externamente (ex: de playlists view)."""
        self._input.setText(url)
        self._load_url(url)

    def get_tracks(self) -> list[dict]:
        return self._tracks

    def get_current_info(self) -> tuple[str, str]:
        return self._current_url, self._current_name
