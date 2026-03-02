import time
import shutil
from pathlib import Path
import requests

from .matcher import score_file


class SoulseekClient:
    """
    Thin wrapper around the slskd REST API.
    slskd must be running separately (or started by the app).
    Docs: https://github.com/slskd/slskd
    """

    SEARCH_DELAY = 6.0  # seconds between searches to avoid bans

    def __init__(self, url: str = "http://localhost:5030", api_key: str = "", username: str = "", password: str = ""):
        self.url = url.rstrip("/")
        self._api_key = api_key
        self._username = username
        self._password = password
        self._session = requests.Session()
        self._session.timeout = 10
        self._last_search_ts = 0.0

    def connect(self) -> bool:
        if self._api_key:
            self._session.headers["X-API-Key"] = self._api_key
        else:
            self._login()
        r = self._session.get(f"{self.url}/api/v0/application", timeout=5)
        r.raise_for_status()
        return True

    def is_connected(self) -> bool:
        try:
            r = self._session.get(f"{self.url}/api/v0/application", timeout=3)
            return r.ok
        except Exception:
            return False

    def download(self, track: dict, output_path: Path, fmt: str = "mp3_320", progress_cb=None) -> Path | None:
        """
        Search slskd for the track and download the best match.
        Returns destination Path or None on failure.
        """
        results = self._search(track)
        if not results:
            return None

        best = self._pick_best(results, track, fmt)
        if not best:
            return None

        username = best["username"]
        filename = best["filename"]

        # Request download
        try:
            r = self._session.post(
                f"{self.url}/api/v0/transfers/downloads/{username}",
                json=[{"filename": filename, "size": best.get("size", 0)}],
            )
            r.raise_for_status()
        except Exception:
            return None

        # Wait and get result
        local_file = self._wait_download(username, filename, timeout=300, progress_cb=progress_cb)
        if not local_file or not local_file.exists():
            return None

        # Move to output path
        dest = output_path / local_file.name
        output_path.mkdir(parents=True, exist_ok=True)
        shutil.move(str(local_file), str(dest))
        return dest

    def _login(self):
        r = self._session.put(
            f"{self.url}/api/v0/session",
            json={"username": self._username, "password": self._password},
        )
        r.raise_for_status()
        token = r.json().get("token", "")
        if token:
            self._session.headers["Authorization"] = f"Bearer {token}"

    def _search(self, track: dict) -> list:
        # Rate limiting
        elapsed = time.time() - self._last_search_ts
        if elapsed < self.SEARCH_DELAY:
            time.sleep(self.SEARCH_DELAY - elapsed)

        query = f"{track['artist']} {track['title']}"
        try:
            r = self._session.post(
                f"{self.url}/api/v0/searches",
                json={"searchText": query, "fileLimit": 100},
            )
            r.raise_for_status()
            search_id = r.json()["id"]
            self._last_search_ts = time.time()
        except Exception:
            return []

        # Poll for results
        deadline = time.time() + 30
        while time.time() < deadline:
            time.sleep(2)
            try:
                r = self._session.get(f"{self.url}/api/v0/searches/{search_id}")
                if r.ok:
                    data = r.json()
                    state = data.get("state", "")
                    responses = data.get("responses") or []
                    if state in ("Completed", "TimedOut") or responses:
                        return responses
            except Exception:
                pass

        return []

    def _pick_best(self, responses: list, track: dict, fmt: str) -> dict | None:
        candidates = []

        for response in responses:
            for f in response.get("files") or []:
                fname = f.get("filename", "")
                ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
                bitrate = f.get("bitRate") or 0

                s = score_file(
                    filename=fname,
                    title=track["title"],
                    artist=track["artist"],
                    bitrate=bitrate,
                    file_format=ext,
                    preferred_format=fmt,
                )

                if s > 0.35:
                    candidates.append({
                        "username": response.get("username", ""),
                        "filename": fname,
                        "size": f.get("size", 0),
                        "bitrate": bitrate,
                        "format": ext,
                        "score": s,
                        "free_slots": response.get("freeUploadSlots", 0),
                    })

        if not candidates:
            return None

        # Prefer free upload slots + higher score
        candidates.sort(key=lambda x: x["score"] + (0.05 if x["free_slots"] > 0 else 0), reverse=True)
        return candidates[0]

    def _wait_download(self, username: str, filename: str, timeout: int = 300, progress_cb=None) -> Path | None:
        deadline = time.time() + timeout

        while time.time() < deadline:
            time.sleep(2)
            try:
                r = self._session.get(f"{self.url}/api/v0/transfers/downloads/{username}")
                if not r.ok:
                    continue
                for transfer in r.json():
                    if transfer.get("filename") == filename:
                        state = transfer.get("state", "")
                        pct = transfer.get("percentComplete", 0)

                        if progress_cb:
                            progress_cb(float(pct))

                        if "Completed" in state or "Succeeded" in state:
                            # slskd saves to its configured download dir
                            local_path = self._find_file(username, filename)
                            return local_path

                        if "Errored" in state or "Cancelled" in state:
                            return None
            except Exception:
                pass

        return None

    def _find_file(self, username: str, filename: str) -> Path | None:
        """Try to locate the downloaded file in common slskd download dirs."""
        local_name = filename.replace("\\", "/").split("/")[-1]

        search_dirs = [
            Path.home() / "Downloads" / username,
            Path.home() / "Downloads",
            Path("./slskd/downloads") / username,
            Path("./downloads") / username,
        ]

        for d in search_dirs:
            candidate = d / local_name
            if candidate.exists():
                return candidate

        return None
