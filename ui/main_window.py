"""SONGER v2 — Main Window com sidebar + views + bottom bar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QMessageBox, QApplication,
)
from PyQt6.QtCore import pyqtSignal, QObject
from PyQt6.QtGui import QCursor

from core.config import Config
from core.downloader import Downloader, DownloadResult
from core.logger import get_logger
from core.app_state import AppState
from ui.theme import STYLE, BG_MAIN
from ui.widgets.sidebar import Sidebar
from ui.widgets.bottom_bar import BottomBar
from ui.views.home_view import HomeView
from ui.views.search_view import SearchView
from ui.views.playlists_view import PlaylistsView
from ui.views.queue_view import QueueView
from ui.views.library_view import LibraryView
from ui.views.history_view import HistoryView
from ui.views.trending_view import TrendingView

log = get_logger("ui")


class DownloadSignals(QObject):
    progress = pyqtSignal(str, float)
    done = pyqtSignal(str, bool, str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._config = Config()
        self._downloader: Downloader | None = None
        self._signals = DownloadSignals()
        self._done_count = 0
        self._fail_count = 0
        self._pending_dl = 0
        self._total_dl = 0

        self.setWindowTitle("SONGER")
        self.setMinimumSize(900, 620)
        self.resize(1050, 720)
        self.setStyleSheet(STYLE)

        # Centrar no ecrã onde está o cursor
        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.x() + (geo.width() - 1050) // 2,
                geo.y() + (geo.height() - 720) // 2,
            )

        self._build_ui()
        self._connect_signals()
        self._app_state = AppState.instance()
        self._check_spotify_on_startup()
        self._check_soulseek_on_startup()
        self._home_view.refresh()
        log.info("SONGER v2 inicializado")

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("mainRoot")
        root.setStyleSheet(f"QWidget#mainRoot {{ background-color: {BG_MAIN}; }}")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Top area: sidebar + content
        top = QWidget()
        top.setObjectName("topArea")
        top.setStyleSheet("QWidget#topArea { background: transparent; }")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._on_page_changed)

        # Stacked content
        self._stack = QStackedWidget()
        self._stack.setObjectName("mainStack")
        self._stack.setStyleSheet(f"QStackedWidget#mainStack {{ background: {BG_MAIN}; }}")

        self._home_view = HomeView(self._config)
        self._search_view = SearchView(self._config)
        self._playlists_view = PlaylistsView(self._config)
        self._queue_view = QueueView()
        self._library_view = LibraryView(self._config)
        self._history_view = HistoryView()
        self._trending_view = TrendingView()

        self._stack.addWidget(self._home_view)         # 0
        self._stack.addWidget(self._search_view)       # 1
        self._stack.addWidget(self._playlists_view)    # 2
        self._stack.addWidget(self._queue_view)        # 3
        self._stack.addWidget(self._library_view)      # 4
        self._stack.addWidget(self._history_view)      # 5
        self._stack.addWidget(self._trending_view)     # 6

        top_layout.addWidget(self._sidebar)
        top_layout.addWidget(self._stack, stretch=1)

        main_layout.addWidget(top, stretch=1)

        # Bottom bar
        self._bottom_bar = BottomBar()
        self._bottom_bar.open_folder_clicked.connect(self._open_folder)
        main_layout.addWidget(self._bottom_bar)

        # Default page
        self._sidebar.set_active("home")

    def _connect_signals(self):
        # Signals de download
        self._signals.progress.connect(self._on_progress)
        self._signals.done.connect(self._on_done)

        # Search view
        self._search_view.download_track.connect(self._download_single)
        self._search_view.download_all.connect(self._download_all)
        self._search_view.play_track.connect(self._on_play_track)

        # Home view navigation
        self._home_view.navigate.connect(self._on_page_changed)
        self._home_view.open_url.connect(self._open_playlist_url)

        # Playlists → search
        self._playlists_view.open_playlist.connect(self._open_playlist_url)

        # History → search
        self._history_view.reload_url.connect(self._open_playlist_url)

        # Library play
        self._library_view.play_file.connect(self._on_play_file)

        # Trending → search
        self._trending_view.open_url.connect(self._open_playlist_url)

        # Cancel signals
        self._queue_view.cancel_track.connect(self._on_cancel_track)
        self._queue_view.cancel_all.connect(self._on_cancel_all)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_page_changed(self, key: str):
        page_map = {
            "home": 0,
            "search": 1,
            "playlists": 2,
            "queue": 3,
            "library": 4,
            "history": 5,
            "trending": 6,
        }

        if key == "settings":
            self._open_settings()
            return

        if key == "about":
            self._open_about()
            return

        idx = page_map.get(key, 0)
        self._stack.setCurrentIndex(idx)

        # Auto-refresh quando entra na view
        if key == "home":
            self._home_view.refresh()
        elif key == "playlists":
            self._playlists_view.refresh()
        elif key == "library":
            self._library_view.refresh()
        elif key == "history":
            self._history_view.refresh()
        elif key == "trending":
            self._trending_view.refresh()

    def _check_spotify_on_startup(self):
        """Verifica estado Spotify em background ao arrancar."""
        from PyQt6.QtCore import QThread

        class _ConnectWorker(QThread):
            def __init__(self, config):
                super().__init__()
                self._config = config

            def run(self):
                try:
                    from core.spotify import SpotifyClient
                    sp = SpotifyClient(
                        self._config.get("spotify", "client_id", default=""),
                        self._config.get("spotify", "client_secret", default=""),
                    )
                    sp.connect()  # emite AppState internamente
                except Exception:
                    AppState.instance().set_spotify_connected(False)

        if not self._config.get("spotify", "client_id", default=""):
            AppState.instance().set_spotify_connected(False)
            return

        self._startup_worker = _ConnectWorker(self._config)
        self._startup_worker.start()

    def _check_soulseek_on_startup(self):
        """Verifica estado Soulseek em background ao arrancar."""
        if not self._config.get("soulseek", "enabled", default=False):
            AppState.instance().set_soulseek_connected(False)
            return

        from PyQt6.QtCore import QThread

        class _SlskWorker(QThread):
            def __init__(self, config):
                super().__init__()
                self._config = config

            def run(self):
                try:
                    from core.soulseek import SoulseekClient
                    slsk = SoulseekClient(
                        url=self._config.get("soulseek", "slskd_url", default="http://localhost:5030"),
                        api_key=self._config.get("soulseek", "slskd_api_key", default=""),
                        username=self._config.get("soulseek", "username", default=""),
                        password=self._config.get("soulseek", "password", default=""),
                    )
                    slsk.connect()
                    AppState.instance().set_soulseek_connected(slsk.is_connected())
                except Exception:
                    AppState.instance().set_soulseek_connected(False)

        self._slsk_startup_worker = _SlskWorker(self._config)
        self._slsk_startup_worker.start()

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(self._config, self)
        dlg.exec()

    def _open_about(self):
        from ui.about_dialog import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    def _open_playlist_url(self, url: str):
        """Navega para search e carrega o URL."""
        self._sidebar.set_active("search")
        self._stack.setCurrentIndex(1)
        self._search_view.load_from_url(url)

    def _open_folder(self):
        folder = Path(self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER")))
        folder.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            os.system(f'open "{folder}"')
        else:
            os.system(f'xdg-open "{folder}"')

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    def _ensure_downloader(self):
        if self._downloader is None:
            self._downloader = Downloader(self._config)
            self._downloader.setup()

    def _download_single(self, track: dict, fmt: str, source: str):
        self._ensure_downloader()
        tid = track.get("id", "")

        # Reset row
        row = self._search_view._track_list.get_row(tid)
        if row:
            row.reset()
            row.set_progress(0)

        self._pending_dl += 1
        self._total_dl += 1
        self._queue_view.add_item(tid, track)
        self._submit(track, fmt, source)

    def _download_all(self, tracks: list, fmt: str, source: str):
        self._ensure_downloader()
        self._done_count = 0
        self._fail_count = 0
        self._pending_dl = len(tracks)
        self._total_dl = len(tracks)

        log.info(f"Download All: {len(tracks)} tracks | fmt={fmt} | source={source}")

        for track in tracks:
            tid = track.get("id", "")
            row = self._search_view._track_list.get_row(tid)
            if row:
                row.reset()
            self._queue_view.add_item(tid, track)
            self._submit(track, fmt, source)

    def _submit(self, track: dict, fmt: str, source: str):
        tid = track.get("id", "")

        def progress_cb(pct: float):
            self._signals.progress.emit(tid, pct)

        def done_cb(result: DownloadResult):
            self._signals.done.emit(tid, result.success, result.path or result.error)

        self._downloader.submit(track, fmt, source, progress_cb, done_cb)

    def _on_progress(self, tid: str, pct: float):
        row = self._search_view._track_list.get_row(tid)
        if row:
            row.set_progress(pct)
        item = self._queue_view.get_item(tid)
        if item:
            item.set_progress(pct)

    def _on_done(self, tid: str, success: bool, detail: str):
        row = self._search_view._track_list.get_row(tid)
        item = self._queue_view.get_item(tid)

        if success:
            if row:
                row.set_done(detail)
            if item:
                item.set_done(detail)
            self._done_count += 1
        else:
            if row:
                row.set_failed(detail)
            if item:
                item.set_failed(detail)
            self._fail_count += 1

        if self._pending_dl > 0:
            self._pending_dl -= 1

        self._bottom_bar.update_stats(
            self._done_count, self._fail_count,
            self._pending_dl, self._total_dl
        )

        # Se acabaram todos, guardar no histórico e notificar
        if self._pending_dl == 0 and self._total_dl > 0:
            url, name = self._search_view.get_current_info()
            if name:
                fmt = self._header_format()
                self._history_view.add_entry(
                    url, name, self._total_dl,
                    self._done_count, self._fail_count, fmt
                )
            self._notify_batch_done(self._done_count, self._fail_count)

    def _notify_batch_done(self, done: int, fail: int):
        try:
            from winotify import Notification, audio
            msg = f"{done} track{'s' if done != 1 else ''} concluída{'s' if done != 1 else ''}"
            if fail:
                msg += f"  ({fail} falhada{'s' if fail != 1 else ''})"
            toast = Notification(app_id="SONGER", title="Download concluído", msg=msg, duration="short")
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception:
            pass  # winotify não disponível — silencioso

    def _on_cancel_track(self, track_id: str):
        if self._downloader:
            self._downloader.cancel_track(track_id)
        item = self._queue_view.get_item(track_id)
        if item:
            item.set_cancelled()
        if self._pending_dl > 0:
            self._pending_dl -= 1
        self._bottom_bar.update_stats(
            self._done_count, self._fail_count,
            self._pending_dl, self._total_dl
        )

    def _on_cancel_all(self):
        if self._downloader:
            self._downloader.cancel_all_pending()
        for item in self._queue_view._items.values():
            if not item._done and not item._failed:
                item.set_cancelled()
        self._pending_dl = 0
        self._bottom_bar.update_stats(
            self._done_count, self._fail_count, 0, self._total_dl
        )

    def _on_play_track(self, track: dict, path: str):
        self._bottom_bar.play_track(
            path,
            track.get("title", ""),
            track.get("artist", ""),
        )

    def _on_play_file(self, path: str, name: str, artist: str):
        self._bottom_bar.play_track(path, name, artist)

    def _header_format(self) -> str:
        try:
            if self._search_view._header.isVisible():
                return self._search_view._header.get_format()
        except Exception:
            pass
        return "mp3_320"

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def keyPressEvent(self, event):
        from PyQt6.QtCore import Qt
        if (event.key() == Qt.Key.Key_T
                and event.modifiers() == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)):
            self._stack.setCurrentIndex(6)
            self._trending_view.refresh()
            return
        super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # Close
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._bottom_bar.stop()
        if self._downloader:
            self._downloader.shutdown()
        log.info("App encerrada")
        event.accept()
