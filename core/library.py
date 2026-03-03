"""Scan da pasta de downloads — mostra música já descarregada."""

from pathlib import Path

from core.logger import get_logger

log = get_logger("library")

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".wma", ".aac"}


def _read_metadata(filepath: Path) -> dict:
    """Try to read year and genre from audio metadata."""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(str(filepath), easy=True)
        if audio is None:
            return {}
        year = ""
        genre = ""
        if "date" in audio:
            year = str(audio["date"][0])[:4]
        elif "year" in audio:
            year = str(audio["year"][0])[:4]
        if "genre" in audio:
            genre = str(audio["genre"][0])
        return {"year": int(year) if year.isdigit() else 0, "genre": genre}
    except Exception:
        return {}


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

            stat = f.stat()
            meta = _read_metadata(f)

            files.append({
                "path": str(f),
                "name": f.stem,
                "ext": f.suffix.lower().lstrip("."),
                "artist": artist,
                "album": album,
                "size_mb": round(stat.st_size / (1024 * 1024), 1),
                "modified": stat.st_mtime,
                "year": meta.get("year", 0),
                "genre": meta.get("genre", ""),
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
