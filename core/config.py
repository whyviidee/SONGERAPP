import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".songer" / "config.json"

DEFAULT_CONFIG = {
    "spotify": {
        "client_id": "",
        "client_secret": "",
        "redirect_uri": "http://localhost:8888/callback",
    },
    "soulseek": {
        "enabled": False,
        "username": "",
        "password": "",
        "slskd_url": "http://localhost:5030",
        "slskd_api_key": "",
    },
    "download": {
        "path": str(Path.home() / "Music" / "SONGER"),
        "format": "mp3_320",
        "source": "hybrid",
        "max_concurrent": 6,
        "organize": True,
    },
}


class Config:
    def __init__(self):
        self._data = {}
        self.load()

    def load(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, encoding="utf-8") as f:
                    saved = json.load(f)
                # Deep merge saved over defaults
                self._data = self._merge(DEFAULT_CONFIG, saved)
            except Exception:
                self._data = json.loads(json.dumps(DEFAULT_CONFIG))
        else:
            self._data = json.loads(json.dumps(DEFAULT_CONFIG))
            self.save()

    def save(self):
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, *keys, default=None):
        d = self._data
        for k in keys:
            if not isinstance(d, dict) or k not in d:
                return default
            d = d[k]
        return d

    def set(self, *args):
        """set("section", "key", value)"""
        *keys, value = args
        d = self._data
        for k in keys[:-1]:
            d = d.setdefault(k, {})
        d[keys[-1]] = value
        self.save()

    def _merge(self, base, override):
        result = json.loads(json.dumps(base))
        for k, v in override.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._merge(result[k], v)
            else:
                result[k] = v
        return result
