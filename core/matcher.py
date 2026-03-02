import re
import unicodedata
from difflib import SequenceMatcher


def normalize(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    # Remove noise words
    text = re.sub(
        r"\b(feat\.?|ft\.?|featuring|explicit|remastered?|remix|radio.?edit|version|edit|single|deluxe)\b",
        " ", text, flags=re.I,
    )
    # Remove parentheses content
    text = re.sub(r"[\(\[\{][^\)\]\}]{0,60}[\)\]\}]", " ", text)
    # Remove non-alphanumeric
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def score_file(
    filename: str,
    title: str,
    artist: str,
    bitrate: int = 0,
    file_format: str = "",
    preferred_format: str = "mp3_320",
) -> float:
    """
    Score a Soulseek file result. Returns 0.0-1.0.
    Higher = better match.
    """
    stem = re.sub(r"\.[^.]+$", "", filename.replace("\\", "/").split("/")[-1])

    # Content matching
    combined_score = similarity(stem, f"{artist} {title}")
    split_score = (similarity(stem, artist) + similarity(stem, title)) / 2
    content_score = max(combined_score, split_score)

    # Format scoring
    fmt = (file_format or "").lower().strip(".")
    pref = preferred_format.lower()

    if pref == "flac":
        fmt_score = 1.0 if fmt == "flac" else (0.4 if fmt == "mp3" else 0.2)
    else:
        if fmt == "flac":
            fmt_score = 0.85
        elif fmt in ("mp3",):
            fmt_score = 0.9
        elif fmt in ("ogg", "aac", "m4a", "opus"):
            fmt_score = 0.6
        elif fmt in ("wma",):
            fmt_score = 0.4
        else:
            fmt_score = 0.3

    # Bitrate scoring
    if bitrate >= 320:
        br_score = 1.0
    elif bitrate >= 256:
        br_score = 0.8
    elif bitrate >= 192:
        br_score = 0.5
    elif bitrate > 0:
        br_score = 0.3
    else:
        br_score = 0.5  # Unknown bitrate — neutral

    return content_score * 0.65 + fmt_score * 0.25 + br_score * 0.10
