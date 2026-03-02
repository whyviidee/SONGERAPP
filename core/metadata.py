from pathlib import Path
import requests


def embed_metadata(filepath: Path, track: dict):
    """Embed ID3/FLAC tags and cover art into a downloaded file."""
    filepath = Path(filepath)
    ext = filepath.suffix.lower()

    cover_data = _fetch_cover(track.get("cover_url", ""))

    if ext == ".mp3":
        _embed_mp3(filepath, track, cover_data)
    elif ext == ".flac":
        _embed_flac(filepath, track, cover_data)
    elif ext in (".ogg", ".opus"):
        _embed_ogg(filepath, track, cover_data)
    # Other formats: skip silently


def _fetch_cover(url: str) -> bytes:
    if not url:
        return b""
    try:
        r = requests.get(url, timeout=10)
        if r.ok:
            return r.content
    except Exception:
        pass
    return b""


def _embed_mp3(path: Path, track: dict, cover_data: bytes):
    from mutagen.id3 import (
        ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TPE2, TDRC, TRCK, TPOS, APIC
    )
    try:
        tags = ID3(str(path))
    except ID3NoHeaderError:
        tags = ID3()

    tags["TIT2"] = TIT2(encoding=3, text=track.get("title", ""))
    tags["TPE1"] = TPE1(encoding=3, text=track.get("artist", ""))
    tags["TALB"] = TALB(encoding=3, text=track.get("album", ""))
    tags["TPE2"] = TPE2(encoding=3, text=track.get("album_artist", ""))
    tags["TDRC"] = TDRC(encoding=3, text=track.get("year", ""))
    tags["TRCK"] = TRCK(encoding=3, text=str(track.get("track_number", 1)))
    tags["TPOS"] = TPOS(encoding=3, text=str(track.get("disc_number", 1)))

    if cover_data:
        tags.delall("APIC")
        tags["APIC"] = APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=cover_data,
        )

    tags.save(str(path))


def _embed_flac(path: Path, track: dict, cover_data: bytes):
    from mutagen.flac import FLAC, Picture

    audio = FLAC(str(path))
    audio["title"] = track.get("title", "")
    audio["artist"] = track.get("artist", "")
    audio["album"] = track.get("album", "")
    audio["albumartist"] = track.get("album_artist", "")
    audio["date"] = track.get("year", "")
    audio["tracknumber"] = str(track.get("track_number", 1))
    audio["discnumber"] = str(track.get("disc_number", 1))

    if cover_data:
        pic = Picture()
        pic.type = 3
        pic.mime = "image/jpeg"
        pic.data = cover_data
        audio.clear_pictures()
        audio.add_picture(pic)

    audio.save()


def _embed_ogg(path: Path, track: dict, cover_data: bytes):
    from mutagen.oggvorbis import OggVorbis

    audio = OggVorbis(str(path))
    audio["title"] = track.get("title", "")
    audio["artist"] = track.get("artist", "")
    audio["album"] = track.get("album", "")
    audio["albumartist"] = track.get("album_artist", "")
    audio["date"] = track.get("year", "")
    audio["tracknumber"] = str(track.get("track_number", 1))
    audio.save()
