import re
from pathlib import Path
import yt_dlp

from core.logger import get_logger

log = get_logger("youtube")

# Format presets
FORMAT_OPTS = {
    "flac": {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "flac"}],
        "ext": "flac",
        "needs_ffmpeg": True,
    },
    "mp3_320": {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
    "mp3_256": {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "256"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
    "mp3_128": {
        "format": "bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
}

# Formato sem conversão (fallback quando não há ffmpeg)
FORMAT_RAW = {
    "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
    "postprocessors": [],
    "ext": None,  # ext determinado no momento
    "needs_ffmpeg": False,
}


class _YtDlpLogger:
    """Redireciona logs do yt-dlp para o nosso logger."""

    def debug(self, msg):
        if msg.startswith("[debug]"):
            log.debug(f"yt-dlp: {msg}")
        else:
            log.info(f"yt-dlp: {msg}")

    def info(self, msg):
        log.info(f"yt-dlp: {msg}")

    def warning(self, msg):
        log.warning(f"yt-dlp: {msg}")

    def error(self, msg):
        log.error(f"yt-dlp: {msg}")


def _ffmpeg_dir() -> str:
    """Return ffmpeg directory for yt-dlp, or empty string to use system PATH."""
    from core.ffmpeg_manager import get_ffmpeg_path
    return get_ffmpeg_path()


class YouTubeClient:
    def __init__(self):
        self._ffmpeg = _ffmpeg_dir()
        ffmpeg_status = "OK" if self._ffmpeg else "NÃO ENCONTRADO (sem conversão)"
        log.info(f"YouTubeClient init — ffmpeg: {ffmpeg_status} | path: '{self._ffmpeg}'")

    def download(self, track: dict, output_path: Path, fmt: str = "mp3_320", progress_cb=None) -> Path | None:
        """
        Download a track from YouTube.
        Returns the downloaded file Path or None on failure.
        Raises RuntimeError with details on failure.
        """
        query = f"{track.get('artist', '')} - {track.get('title', '')}"
        log.info(f"A iniciar download: '{query}' | fmt={fmt} | dest={output_path}")

        preset = FORMAT_OPTS.get(fmt, FORMAT_OPTS["mp3_320"])
        has_ffmpeg = bool(self._ffmpeg) or bool(__import__("shutil").which("ffmpeg"))

        # Se precisa de ffmpeg mas não tem, usa raw
        if preset["needs_ffmpeg"] and not has_ffmpeg:
            log.warning(f"ffmpeg não disponível — a usar formato raw (sem conversão) para '{query}'")
            preset = FORMAT_RAW
            use_raw = True
        else:
            use_raw = False

        stem = _safe_stem(track)
        out_template = str(output_path / stem)
        log.debug(f"Template de saída: {out_template}")

        opts = {
            "format": preset["format"],
            "postprocessors": preset["postprocessors"],
            "outtmpl": out_template + ".%(ext)s",
            "quiet": False,
            "no_warnings": False,
            "logger": _YtDlpLogger(),
            "noplaylist": True,
            "socket_timeout": 30,
            # Android client contorna o bloqueio HTTP 403 / SABR do YouTube
            "extractor_args": {"youtube": {"player_client": ["android"]}},
        }

        if self._ffmpeg:
            opts["ffmpeg_location"] = self._ffmpeg
            log.debug(f"ffmpeg_location={self._ffmpeg}")

        if progress_cb:
            opts["progress_hooks"] = [lambda d: _hook(d, progress_cb)]

        try:
            log.info(f"Chamando yt-dlp: ytsearch1:{query}")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                if info and "entries" in info and info["entries"]:
                    entry = info["entries"][0]
                    log.info(f"Download concluído: '{entry.get('title', '?')}' de {entry.get('channel', '?')}")
                elif info:
                    log.info(f"Download concluído: '{info.get('title', '?')}'")
                else:
                    log.warning(f"yt-dlp retornou None para '{query}'")

        except yt_dlp.utils.DownloadError as e:
            log.error(f"yt-dlp DownloadError para '{query}': {e}")
            raise RuntimeError(f"YouTube: {e}") from e
        except Exception as e:
            log.error(f"Erro inesperado no download de '{query}': {e}", exc_info=True)
            raise RuntimeError(f"Erro inesperado: {e}") from e

        # Encontrar o ficheiro descarregado
        if not use_raw:
            ext = preset["ext"]
            target = Path(out_template + f".{ext}")
            if target.exists():
                log.info(f"Ficheiro encontrado: {target}")
                return target

        # Fallback: scan output dir for file with matching stem
        log.debug(f"A procurar ficheiros com stem '{stem}' em {output_path}")
        try:
            for f in output_path.iterdir():
                if f.stem == stem:
                    log.info(f"Ficheiro encontrado por scan: {f}")
                    return f
        except Exception as e:
            log.error(f"Erro ao fazer scan do dir de saída: {e}")

        log.error(f"Ficheiro não encontrado após download de '{query}'. Verificar {output_path}")
        return None


def _hook(d: dict, cb):
    if d.get("status") == "downloading":
        pct_str = d.get("_percent_str", "0%").strip().replace("%", "").replace("\x1b[0;94m", "").replace("\x1b[0m", "")
        try:
            cb(float(pct_str))
        except ValueError:
            pass
    elif d.get("status") == "finished":
        cb(100.0)


def _safe_stem(track: dict) -> str:
    name = track.get("title", "Unknown")
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)[:200]
