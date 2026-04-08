"""Generic yt-dlp client for direct URL downloads — SoundCloud, Bandcamp, Mixcloud, etc."""

import re
import hashlib
from pathlib import Path
import yt_dlp

from core.logger import get_logger

log = get_logger("ytdlp")

FORMAT_OPTS = {
    "flac": {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "flac"}],
        "ext": "flac",
        "needs_ffmpeg": True,
    },
    "mp3_320": {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "320"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
    "mp3_256": {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "256"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
    "mp3_128": {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
        "ext": "mp3",
        "needs_ffmpeg": True,
    },
}

FORMAT_RAW = {
    "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
    "postprocessors": [],
    "ext": None,
    "needs_ffmpeg": False,
}


class _YtDlpLogger:
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
    from core.ffmpeg_manager import get_ffmpeg_path
    return get_ffmpeg_path()


def detect_platform(url: str) -> str:
    url_lower = url.lower()
    if "soundcloud.com" in url_lower:
        return "soundcloud"
    if "bandcamp.com" in url_lower:
        return "bandcamp"
    if "mixcloud.com" in url_lower:
        return "mixcloud"
    if "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    return "web"


class YtDlpClient:
    def __init__(self):
        self._ffmpeg = _ffmpeg_dir()
        log.info(f"YtDlpClient init — ffmpeg: {'OK' if self._ffmpeg else 'NOT FOUND'}")

    def extract_info(self, url: str) -> dict:
        """Extract metadata from a direct URL without downloading."""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "logger": _YtDlpLogger(),
            "noplaylist": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("Não foi possível extrair informação do URL")
            return self._normalize(info, url)

    def _normalize(self, info: dict, url: str) -> dict:
        platform = detect_platform(url)
        title = info.get("title") or info.get("fulltitle") or "Unknown"
        artist = (
            info.get("artist")
            or info.get("uploader")
            or info.get("creator")
            or info.get("channel")
            or "Unknown"
        )
        album = info.get("album") or ""

        # Pick best thumbnail
        cover_url = info.get("thumbnail") or ""
        if not cover_url and info.get("thumbnails"):
            for t in reversed(info["thumbnails"]):
                if t.get("url"):
                    cover_url = t["url"]
                    break

        duration_s = info.get("duration") or 0
        track_id = info.get("id") or hashlib.md5(url.encode()).hexdigest()[:16]

        return {
            "id": f"direct_{track_id}",
            "title": title,
            "artist": artist,
            "album": album,
            "cover_url": cover_url,
            "duration_ms": int(duration_s * 1000),
            "url": url,
            "platform": platform,
            "track_number": 0,
        }

    def download(self, track: dict, output_path: Path, fmt: str = "mp3_320", progress_cb=None) -> Path | None:
        """Download audio from a direct URL. Returns the output file Path or None."""
        url = track.get("url", "")
        if not url:
            raise RuntimeError("Track sem URL para download directo")

        preset = FORMAT_OPTS.get(fmt, FORMAT_OPTS["mp3_320"])
        has_ffmpeg = bool(self._ffmpeg) or bool(__import__("shutil").which("ffmpeg"))

        if preset["needs_ffmpeg"] and not has_ffmpeg:
            log.warning("ffmpeg não disponível — a usar formato raw")
            preset = FORMAT_RAW
            use_raw = True
        else:
            use_raw = False

        stem = _safe_stem(track)
        out_template = str(output_path / stem)

        opts = {
            "format": preset["format"],
            "postprocessors": preset["postprocessors"],
            "outtmpl": out_template + ".%(ext)s",
            "quiet": False,
            "no_warnings": False,
            "logger": _YtDlpLogger(),
            "noplaylist": True,
            "socket_timeout": 30,
        }

        if self._ffmpeg:
            opts["ffmpeg_location"] = self._ffmpeg

        if progress_cb:
            opts["progress_hooks"] = [lambda d: _hook(d, progress_cb)]

        final_path_holder: dict = {}

        def pp_hook(d: dict):
            if d.get("status") == "finished":
                fp = (d.get("info_dict") or {}).get("filepath") or d.get("filepath", "")
                if fp:
                    final_path_holder["path"] = fp

        opts["postprocessor_hooks"] = [pp_hook]

        try:
            log.info(f"YtDlpClient.download: {url} | fmt={fmt}")
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
        except yt_dlp.utils.DownloadError as e:
            log.error(f"DownloadError: {e}")
            raise RuntimeError(f"Download error: {e}") from e
        except Exception as e:
            log.error(f"Erro inesperado: {e}", exc_info=True)
            raise RuntimeError(f"Erro inesperado: {e}") from e

        # 1. postprocessor_hook (mais fiável)
        if final_path_holder.get("path"):
            p = Path(final_path_holder["path"])
            if p.exists():
                log.info(f"Ficheiro via pp_hook: {p}")
                return p

        # 2. template path
        if not use_raw:
            ext = preset["ext"]
            target = Path(out_template + f".{ext}")
            if target.exists():
                log.info(f"Ficheiro encontrado: {target}")
                return target

        # 3. scan dir
        try:
            for f in output_path.iterdir():
                if f.stem == stem:
                    log.info(f"Ficheiro encontrado por scan: {f}")
                    return f
        except Exception as e:
            log.error(f"Erro ao fazer scan do dir de saída: {e}")

        log.error(f"Ficheiro não encontrado após download. Verificar {output_path}")
        return None


def _hook(d: dict, cb):
    if d.get("status") == "downloading":
        pct_str = (
            d.get("_percent_str", "0%")
            .strip()
            .replace("%", "")
            .replace("\x1b[0;94m", "")
            .replace("\x1b[0m", "")
        )
        try:
            cb(float(pct_str))
        except ValueError:
            pass
    elif d.get("status") == "finished":
        cb(100.0)


def _safe_stem(track: dict) -> str:
    name = f"{track.get('artist', 'Unknown')} - {track.get('title', 'Unknown')}"
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)[:200]
