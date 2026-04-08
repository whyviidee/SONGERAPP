from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

from .config import Config
from .metadata import embed_metadata
from .logger import get_logger

log = get_logger("downloader")


class DownloadResult:
    def __init__(self, track: dict, success: bool, path: str = "", error: str = ""):
        self.track = track
        self.success = success
        self.path = path
        self.error = error


class Downloader:
    """
    Orchestrates downloads via YouTube and/or Soulseek.
    All downloads run in a thread pool so the UI stays responsive.
    """

    def __init__(self, config: Config):
        self._config = config
        self._yt = None
        self._slsk = None
        self._ytdlp = None
        max_workers = config.get("download", "max_concurrent", default=2)
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        self._cancelled: set[str] = set()
        self._cancel_lock = threading.Lock()
        log.info(f"Downloader criado — max_workers={max_workers}")

    def setup(self):
        """Initialize backends. Call once after config is loaded."""
        log.info("Downloader.setup() — a inicializar backends")
        try:
            from .youtube import YouTubeClient
            self._yt = YouTubeClient()
            log.info("YouTubeClient OK")
        except Exception as e:
            log.error(f"Falha ao criar YouTubeClient: {e}", exc_info=True)

        if self._config.get("soulseek", "enabled"):
            try:
                from .soulseek import SoulseekClient
                self._slsk = SoulseekClient(
                    url=self._config.get("soulseek", "slskd_url", default="http://localhost:5030"),
                    api_key=self._config.get("soulseek", "slskd_api_key", default=""),
                    username=self._config.get("soulseek", "username", default=""),
                    password=self._config.get("soulseek", "password", default=""),
                )
                self._slsk.connect()
                log.info("SoulseekClient conectado")
            except Exception as e:
                log.warning(f"Soulseek indisponível: {e}")
                self._slsk = None

    def submit(
        self,
        track: dict,
        fmt: str,
        source: str,
        progress_cb: Callable[[float], None] | None = None,
        done_cb: Callable[[DownloadResult], None] | None = None,
    ):
        """Submit a download to the thread pool. Non-blocking."""
        output_path = self._output_path(track)
        log.debug(f"Submit: '{track.get('artist')} - {track.get('title')}' | fmt={fmt} | source={source} | dest={output_path}")
        self._pool.submit(self._worker, track, fmt, source, output_path, progress_cb, done_cb)

    def shutdown(self):
        log.info("Downloader shutdown")
        self._pool.shutdown(wait=False, cancel_futures=True)

    def cancel_track(self, track_id: str) -> None:
        with self._cancel_lock:
            self._cancelled.add(track_id)
        log.info(f"Track cancelada: {track_id}")

    def cancel_all_pending(self) -> None:
        log.info("Cancelar todos os downloads pendentes")
        self._pool.shutdown(wait=False, cancel_futures=True)
        max_workers = self._config.get("download", "max_concurrent", default=2)
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        with self._cancel_lock:
            self._cancelled.clear()

    def is_cancelled(self, track_id: str) -> bool:
        with self._cancel_lock:
            return track_id in self._cancelled

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _find_existing(self, track: dict, output_path: Path) -> Path | None:
        """Retorna caminho se já existe ficheiro áudio para esta track."""
        title = _safe_dir(track.get("title", ""))[:40]
        if not title or not output_path.exists():
            return None
        for ext in ("mp3", "flac", "opus", "m4a", "ogg", "wav"):
            for f in output_path.glob(f"*{title}*.{ext}"):
                return f
        return None

    def _worker(self, track, fmt, source, output_path, progress_cb, done_cb):
        title = f"{track.get('artist', '?')} - {track.get('title', '?')}"
        track_id = track.get("id", "")
        log.info(f"Worker iniciado: '{title}' | source={source} | fmt={fmt}")

        if self.is_cancelled(track_id):
            log.info(f"Track já cancelada antes de começar: {title}")
            if done_cb:
                done_cb(DownloadResult(track, False, error="Cancelado"))
            return

        # Verificar duplicado
        existing = self._find_existing(track, output_path)
        if existing:
            log.info(f"Duplicado encontrado, a saltar: {existing}")
            if progress_cb:
                progress_cb(100.0)
            if done_cb:
                done_cb(DownloadResult(track, True, str(existing)))
            return

        output_path.mkdir(parents=True, exist_ok=True)
        result_path = None
        error = ""

        try:
            if source == "youtube":
                result_path = self._dl_yt(track, output_path, fmt, progress_cb)

            elif source == "direct":
                result_path = self._dl_direct(track, output_path, fmt, progress_cb)

            elif source == "soulseek":
                if self._slsk and self._slsk.is_connected():
                    result_path = self._dl_slsk(track, output_path, fmt, progress_cb)
                else:
                    error = "Soulseek não está disponível"
                    log.warning(f"Soulseek indisponível para '{title}'")

            else:  # hybrid — Soulseek first, YouTube fallback
                if self._slsk and self._slsk.is_connected():
                    log.info(f"Hybrid: a tentar Soulseek para '{title}'")
                    try:
                        result_path = self._dl_slsk(track, output_path, fmt, progress_cb)
                    except Exception as e:
                        log.warning(f"Soulseek falhou para '{title}': {e}")

                if not result_path:
                    log.info(f"Hybrid: a tentar YouTube para '{title}'")
                    if progress_cb:
                        progress_cb(0.0)
                    result_path = self._dl_yt(track, output_path, fmt, progress_cb)

        except Exception as e:
            error = str(e)
            log.error(f"Erro no worker de '{title}': {e}", exc_info=True)

        if result_path and result_path.exists():
            if self.is_cancelled(track_id):
                log.info(f"Track cancelada após download, antes de metadata: {title}")
                result_path.unlink(missing_ok=True)
                if done_cb:
                    done_cb(DownloadResult(track, False, error="Cancelado"))
                return

            log.info(f"Download OK: '{title}' → {result_path}")
            try:
                embed_metadata(result_path, track)
                log.debug(f"Metadata embutida: {result_path}")
            except Exception as e:
                log.warning(f"Falha ao embutir metadata em '{title}': {e}")

            if done_cb:
                done_cb(DownloadResult(track, True, str(result_path)))
        else:
            final_error = error or "Ficheiro não encontrado após download"
            log.error(f"Download FALHADO: '{title}' — {final_error}")
            if done_cb:
                done_cb(DownloadResult(track, False, error=final_error))

    def _dl_yt(self, track, output_path, fmt, progress_cb):
        if not self._yt:
            raise RuntimeError("YouTubeClient não inicializado")
        return self._yt.download(track, output_path, fmt, progress_cb)

    def _dl_slsk(self, track, output_path, fmt, progress_cb):
        return self._slsk.download(track, output_path, fmt, progress_cb)

    def _dl_direct(self, track, output_path, fmt, progress_cb):
        if self._ytdlp is None:
            from .ytdlp import YtDlpClient
            self._ytdlp = YtDlpClient()
        return self._ytdlp.download(track, output_path, fmt, progress_cb)

    def _output_path(self, track: dict) -> Path:
        base = Path(self._config.get("download", "path", default=str(Path.home() / "Music" / "SONGER")))
        organize = self._config.get("download", "organize", default=True)

        if organize:
            artist = _safe_dir(track.get("album_artist") or track.get("artist", "Unknown"))
            album = _safe_dir(track.get("album", "Unknown Album"))
            return base / artist / album

        return base


def _safe_dir(name: str) -> str:
    import re
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip()[:100]
