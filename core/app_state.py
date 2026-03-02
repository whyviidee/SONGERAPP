from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal


class AppState(QObject):
    """Estado global da app. Singleton. Widgets subscrevem via sinais Qt."""

    spotify_status_changed = pyqtSignal(bool, str)      # (conectado, username)
    soulseek_status_changed = pyqtSignal(bool)          # (conectado)
    download_stats_changed = pyqtSignal(int, int, int)  # (done, fail, pending)

    _instance: AppState | None = None

    def __init__(self):
        super().__init__()
        self._spotify_connected = False
        self._spotify_username = ""
        self._soulseek_connected = False

    @classmethod
    def instance(cls) -> "AppState":
        if cls._instance is None:
            cls._instance = AppState()
        return cls._instance

    def set_spotify_connected(self, connected: bool, username: str = "") -> None:
        self._spotify_connected = connected
        self._spotify_username = username
        self.spotify_status_changed.emit(connected, username)

    def is_spotify_connected(self) -> bool:
        return self._spotify_connected

    def get_spotify_username(self) -> str:
        return self._spotify_username

    def set_soulseek_connected(self, connected: bool) -> None:
        self._soulseek_connected = connected
        self.soulseek_status_changed.emit(connected)

    def is_soulseek_connected(self) -> bool:
        return self._soulseek_connected

    def update_download_stats(self, done: int, fail: int, pending: int) -> None:
        self.download_stats_changed.emit(done, fail, pending)
