import re
import json
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests as _requests
import spotipy

from core.logger import get_logger
from core.app_state import AppState

log = get_logger("spotify")

SCOPES = "user-library-read playlist-read-private playlist-read-collaborative"
CACHE_PATH = Path.home() / ".songer" / ".spotify_token.json"
REDIRECT_URI = "https://open.spotify.com"


class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._sp = None
        self._sp_cc = None  # Client Credentials — para endpoints públicos

    def _get_public_sp(self) -> spotipy.Spotify:
        """Spotipy com Client Credentials — não precisa de token do utilizador."""
        if self._sp_cc is None:
            from spotipy.oauth2 import SpotifyClientCredentials
            self._sp_cc = spotipy.Spotify(
                auth_manager=SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                )
            )
        return self._sp_cc

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "scope": SCOPES,
        }
        return "https://accounts.spotify.com/authorize?" + urlencode(params)

    def open_browser_for_auth(self):
        webbrowser.open(self.get_auth_url())

    def connect_with_code(self, pasted_url: str) -> bool:
        code = self._extract_code(pasted_url)
        if not code:
            raise ValueError("Não encontrei o código no URL. Cola o URL completo da barra do browser.")
        token_data = self._exchange_code(code)
        self._save_token(token_data)
        self._sp = spotipy.Spotify(auth=token_data["access_token"])
        user = self._sp.current_user()
        username = user.get("display_name") or user.get("id", "")
        AppState.instance().set_spotify_connected(True, username)
        return True

    def connect(self) -> bool:
        token_data = self._load_token()
        if not token_data:
            AppState.instance().set_spotify_connected(False)
            return False
        if time.time() > token_data.get("expires_at", 0) - 60:
            try:
                token_data = self._refresh_token(token_data["refresh_token"])
                self._save_token(token_data)
            except Exception:
                AppState.instance().set_spotify_connected(False)
                return False
        self._sp = spotipy.Spotify(auth=token_data["access_token"])
        try:
            user = self._sp.current_user()
            username = user.get("display_name") or user.get("id", "")
            AppState.instance().set_spotify_connected(True, username)
        except Exception:
            AppState.instance().set_spotify_connected(False)
            return False
        return True

    def is_connected(self) -> bool:
        if not self._sp:
            return False
        try:
            self._sp.current_user()
            return True
        except Exception:
            return False

    def has_saved_token(self) -> bool:
        return CACHE_PATH.exists()

    def logout(self):
        self._sp = None
        if CACHE_PATH.exists():
            CACHE_PATH.unlink()
        AppState.instance().set_spotify_connected(False)

    # ------------------------------------------------------------------
    # Search por texto
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 50) -> dict:
        """
        Pesquisa no Spotify por texto.
        Retorna: {"tracks": [...], "albums": [...], "artists": [...]}
        """
        if not self._sp and not self.client_id:
            raise RuntimeError("Spotify não conectado")

        log.info(f"Search: '{query}' (limit={limit})")
        per_type_limit = min(limit, 50)  # Spotify API suporta até 50 por tipo
        results = self._get_public_sp().search(q=query, limit=per_type_limit, type="track,album,artist")

        tracks = []
        for t in (results.get("tracks", {}).get("items") or []):
            tracks.append(self._parse_track(t))

        albums = []
        for a in (results.get("albums", {}).get("items") or []):
            images = a.get("images") or []
            artists = [ar["name"] for ar in (a.get("artists") or [])]
            albums.append({
                "id": a["id"],
                "name": a["name"],
                "artist": ", ".join(artists),
                "cover_url": images[0]["url"] if images else "",
                "year": (a.get("release_date") or "")[:4],
                "total_tracks": a.get("total_tracks", 0),
                "url": a.get("external_urls", {}).get("spotify", ""),
            })

        artists = []
        for ar in (results.get("artists", {}).get("items") or []):
            images = ar.get("images") or []
            artists.append({
                "id": ar["id"],
                "name": ar["name"],
                "cover_url": images[0]["url"] if images else "",
                "genres": ar.get("genres", [])[:3],
                "followers": ar.get("followers", {}).get("total", 0),
                "url": ar.get("external_urls", {}).get("spotify", ""),
            })

        log.info(f"Search results: {len(tracks)} tracks, {len(albums)} albums, {len(artists)} artists")
        return {"tracks": tracks, "albums": albums, "artists": artists}

    # ------------------------------------------------------------------
    # Minhas Playlists
    # ------------------------------------------------------------------

    def get_my_playlists(self, limit: int = 50) -> list[dict]:
        """Retorna as playlists do user autenticado."""
        if not self._sp:
            raise RuntimeError("Spotify não conectado")

        log.info("A carregar playlists do user...")
        playlists = []
        results = self._sp.current_user_playlists(limit=limit)

        while results:
            for p in results.get("items") or []:
                images = p.get("images") or []
                playlists.append({
                    "id": p["id"],
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "cover_url": images[0]["url"] if images else "",
                    "total_tracks": p.get("tracks", {}).get("total", 0),
                    "owner": p.get("owner", {}).get("display_name", ""),
                    "url": p.get("external_urls", {}).get("spotify", ""),
                })
            if results.get("next"):
                results = self._sp.next(results)
            else:
                break

        log.info(f"Playlists carregadas: {len(playlists)}")
        return playlists

    def get_liked_songs(self, limit: int = 500) -> list[dict]:
        """Retorna as músicas guardadas (Liked Songs) do user."""
        if not self._sp:
            raise RuntimeError("Spotify não conectado")
        log.info("A carregar liked songs...")
        tracks = []
        results = self._sp.current_user_saved_tracks(limit=50)
        while results and len(tracks) < limit:
            for item in (results.get("items") or []):
                t = item.get("track")
                if not t or not t.get("id"):
                    continue
                try:
                    tracks.append(self._parse_track(t))
                except Exception:
                    continue
            if results.get("next") and len(tracks) < limit:
                results = self._sp.next(results)
            else:
                break
        log.info(f"Liked songs carregadas: {len(tracks)}")
        return tracks

    def get_artist_albums(self, artist_id: str) -> list[dict]:
        """Retorna albums e singles de um artista, sem duplicados."""
        if not self._sp:
            raise RuntimeError("Spotify não conectado")
        albums = []
        seen: set[str] = set()
        results = self._sp.artist_albums(artist_id, album_type="album,single", limit=50)
        for a in (results.get("items") or []):
            name_key = a["name"].lower()
            if name_key in seen:
                continue
            seen.add(name_key)
            images = a.get("images") or []
            albums.append({
                "id": a["id"],
                "name": a["name"],
                "album_type": a.get("album_type", "album"),
                "year": (a.get("release_date") or "")[:4],
                "total_tracks": a.get("total_tracks", 0),
                "cover_url": images[0]["url"] if images else "",
                "url": a.get("external_urls", {}).get("spotify", ""),
            })
        return albums

    def get_track_with_album(self, track_id: str) -> tuple[list[dict], str, str]:
        """Retorna todas as tracks do álbum a que a track pertence + id da track original."""
        if not self._sp:
            raise RuntimeError("Spotify não conectado")
        track = self._sp.track(track_id)
        album_id = (track.get("album") or {}).get("id", "")
        if album_id:
            tracks, name = self._album_tracks(album_id)
            return tracks, name, track_id
        return [self._parse_track(track)], track.get("name", ""), track_id

    def get_artist_top_tracks(self, artist_id: str) -> tuple[list[dict], str]:
        """Retorna top tracks de um artista."""
        pub = self._get_public_sp()
        artist = pub.artist(artist_id)
        results = pub._get(f"artists/{artist_id}/top-tracks")
        tracks = [self._parse_track(t) for t in (results.get("tracks") or [])]
        return tracks, artist.get("name", "")

    # ------------------------------------------------------------------
    # Leitura de tracks
    # ------------------------------------------------------------------

    def parse_link(self, url: str):
        patterns = [
            r"spotify\.com/(playlist|album|track|artist)/([A-Za-z0-9]+)",
            r"spotify:(playlist|album|track|artist):([A-Za-z0-9]+)",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1), m.group(2)
        return None, None

    def get_tracks(self, url: str):
        kind, id_ = self.parse_link(url)
        if not kind:
            raise ValueError("Link Spotify inválido.")
        if kind == "playlist":
            return self._playlist_tracks(id_)
        elif kind == "album":
            return self._album_tracks(id_)
        elif kind == "track":
            track = self._sp.track(id_)
            return [self._parse_track(track)], track["name"]
        elif kind == "artist":
            return self.get_artist_top_tracks(id_)
        raise ValueError(f"Tipo desconhecido: {kind}")

    def _playlist_tracks(self, playlist_id: str):
        data = self._sp.playlist(playlist_id)
        name = data["name"]
        tracks = []
        results = data.get("tracks") or {}
        while True:
            for item in (results.get("items") or []):
                t = item.get("track")
                # Ignorar episódios de podcast e tracks nulas/locais
                if not t or not t.get("id"):
                    continue
                if t.get("type") != "track":
                    continue
                try:
                    tracks.append(self._parse_track(t))
                except Exception:
                    continue
            if results.get("next"):
                results = self._sp.next(results)
            else:
                break
        return tracks, name

    def _album_tracks(self, album_id: str):
        album = self._sp.album(album_id)
        name = album["name"]
        tracks = []
        results = album["tracks"]
        while True:
            for t in results["items"]:
                tracks.append(self._parse_track(t, album=album))
            if results["next"]:
                results = self._sp.next(results)
            else:
                break
        return tracks, name

    def _parse_track(self, track: dict, album: dict = None) -> dict:
        alb = album or track.get("album") or {}
        artists = [a["name"] for a in track.get("artists") or []]
        images = alb.get("images") or []
        cover_url = images[0]["url"] if images else ""
        alb_artists = alb.get("artists") or []
        album_artist = alb_artists[0]["name"] if alb_artists else (artists[0] if artists else "")
        return {
            "id": track.get("id", ""),
            "title": track.get("name", ""),
            "artist": ", ".join(artists),
            "album": alb.get("name", ""),
            "album_artist": album_artist,
            "year": (alb.get("release_date") or "")[:4],
            "track_number": track.get("track_number", 1),
            "disc_number": track.get("disc_number", 1),
            "duration_ms": track.get("duration_ms", 0),
            "cover_url": cover_url,
            "preview_url": track.get("preview_url", ""),
        }

    # ------------------------------------------------------------------
    # OAuth helpers
    # ------------------------------------------------------------------

    def _extract_code(self, url_or_code: str) -> str:
        url_or_code = url_or_code.strip()
        if url_or_code.startswith("http"):
            qs = parse_qs(urlparse(url_or_code).query)
            codes = qs.get("code", [])
            return codes[0] if codes else ""
        return url_or_code

    def _exchange_code(self, code: str) -> dict:
        r = _requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT_URI},
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        data["expires_at"] = time.time() + data.get("expires_in", 3600)
        return data

    def _refresh_token(self, refresh_token: str) -> dict:
        r = _requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            auth=(self.client_id, self.client_secret),
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        data["expires_at"] = time.time() + data.get("expires_in", 3600)
        if "refresh_token" not in data:
            saved = self._load_token() or {}
            data["refresh_token"] = saved.get("refresh_token", "")
        return data

    def _save_token(self, data: dict):
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "w") as f:
            json.dump(data, f)

    def _load_token(self) -> dict:
        if not CACHE_PATH.exists():
            return {}
        try:
            with open(CACHE_PATH) as f:
                return json.load(f)
        except Exception:
            return {}
