"""Scan da pasta de downloads — mostra música já descarregada."""

from pathlib import Path

from core.logger import get_logger

log = get_logger("library")

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".wma", ".aac"}


def scan_library(base_path: str) -> list[dict]:
    """
    Faz scan da pasta de downloads.
    Retorna lista de dicts com info de cada ficheiro de áudio.
    Organizado por artista → álbum (se existir estrutura de pastas).
    """
    base = Path(base_path)
    if not base.exists():
        return []

    files = []
    for f in base.rglob("*"):
        if f.suffix.lower() in AUDIO_EXTS and f.is_file():
            # Extrair artista/álbum do path relativo
            rel = f.relative_to(base)
            parts = rel.parts

            if len(parts) >= 3:
                artist = parts[0]
                album = parts[1]
            elif len(parts) == 2:
                artist = parts[0]
                album = ""
            else:
                artist = ""
                album = ""

            files.append({
                "path": str(f),
                "name": f.stem,
                "ext": f.suffix.lower().lstrip("."),
                "artist": artist,
                "album": album,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 1),
            })

    files.sort(key=lambda x: (x["artist"].lower(), x["album"].lower(), x["name"].lower()))
    log.info(f"Library scan: {len(files)} ficheiros em {base}")
    return files


def get_library_stats(base_path: str) -> dict:
    """Estatísticas rápidas da library."""
    files = scan_library(base_path)
    artists = set(f["artist"] for f in files if f["artist"])
    albums = set((f["artist"], f["album"]) for f in files if f["album"])
    total_mb = sum(f["size_mb"] for f in files)
    return {
        "total_files": len(files),
        "total_artists": len(artists),
        "total_albums": len(albums),
        "total_size_mb": round(total_mb, 1),
    }
