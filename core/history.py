"""Persistência de histórico de downloads."""

import json
from datetime import datetime
from pathlib import Path

from core.logger import get_logger

log = get_logger("history")

HISTORY_PATH = Path.home() / ".songer" / "history.json"
MAX_ENTRIES = 200


class DownloadHistory:
    def __init__(self):
        self._entries: list[dict] = []
        self._load()

    def add(self, url: str, name: str, tracks_count: int, done_count: int, fail_count: int, fmt: str, cover: str = ""):
        entry = {
            "date": datetime.now().isoformat(timespec="seconds"),
            "url": url,
            "name": name,
            "tracks_count": tracks_count,
            "done_count": done_count,
            "fail_count": fail_count,
            "format": fmt,
            "cover": cover,
        }
        self._entries.insert(0, entry)
        if len(self._entries) > MAX_ENTRIES:
            self._entries = self._entries[:MAX_ENTRIES]
        self._save()
        log.debug(f"History entry added: {name} ({done_count}/{tracks_count})")

    def get_all(self) -> list[dict]:
        return list(self._entries)

    def clear(self):
        self._entries.clear()
        self._save()

    def _load(self):
        if HISTORY_PATH.exists():
            try:
                with open(HISTORY_PATH, encoding="utf-8") as f:
                    self._entries = json.load(f)
            except Exception:
                self._entries = []

    def _save(self):
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self._entries, f, indent=2, ensure_ascii=False)
