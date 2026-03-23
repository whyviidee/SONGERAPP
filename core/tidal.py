"""Tidal API client — same interface as SpotifyClient for server.py compatibility."""
import json
from pathlib import Path
from core.logger import get_logger

log = get_logger("tidal")

SESSION_PATH = Path.home() / ".songer" / "tidal_session.json"


class TidalClient:
    def __init__(self):
        self._session = None

    def _get_session(self):
        if self._session is None:
            import tidalapi
            self._session = tidalapi.Session()
        return self._session

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Connect using saved session or return False."""
        session = self._get_session()
        if session.check_login():
            return True
        if SESSION_PATH.exists():
            try:
                data = json.loads(SESSION_PATH.read_text())
                session.load_oauth_session(
                    token_type=data.get("token_type", "Bearer"),
                    access_token=data.get("access_token", ""),
                    refresh_token=data.get("refresh_token", ""),
                )
                if session.check_login():
                    log.info("Tidal session restored")
                    return True
            except Exception as e:
                log.warning(f"Failed to restore Tidal session: {e}")
        return False

    def login_oauth(self) -> dict:
        """Start OAuth login flow. Returns {url, future} for the setup page."""
        session = self._get_session()
        login, future = session.login_oauth()
        uri = login.verification_uri_complete or ""
        if uri and not uri.startswith("http"):
            uri = "https://" + uri
        return {
            "verification_uri": uri,
            "expires_in": login.expires_in,
            "future": future,
            "session": session,
        }

    def complete_login(self, future, session) -> bool:
        """Check if OAuth completed (non-blocking)."""
        if not future.done():
            return False
        try:
            future.result(timeout=0)
            if session.check_login():
                self._session = session
                self._save_session()
                log.info(f"Tidal logged in: {session.user.first_name}")
                return True
        except Exception as e:
            log.error(f"Tidal login failed: {e}")
        return False

    def _save_session(self):
        s = self._session
        if not s:
            return
        SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSION_PATH.write_text(json.dumps({
            "token_type": s.token_type,
            "access_token": s.access_token,
            "refresh_token": s.refresh_token,
        }))

    def is_connected(self) -> bool:
        try:
            return self._session is not None and self._session.check_login()
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, limit: int = 10) -> dict:
        import tidalapi
        session = self._get_session()
        results = session.search(query, models=[tidalapi.Track, tidalapi.Album, tidalapi.Artist], limit=limit)

        tracks = []
        for t in (results.get("tracks") or results.get("top_hit") or [])[:limit]:
            if not hasattr(t, 'name'):
                continue
            tracks.append(self._format_track(t))

        albums = []
        for a in (results.get("albums") or [])[:limit]:
            if not hasattr(a, 'name'):
                continue
            albums.append(self._format_album(a))

        artists = []
        for ar in (results.get("artists") or [])[:limit]:
            if not hasattr(ar, 'name'):
                continue
            artists.append(self._format_artist(ar))

        log.info(f"Search: '{query}' → {len(tracks)} tracks, {len(albums)} albums, {len(artists)} artists")
        return {"tracks": tracks, "albums": albums, "artists": artists}

    # ------------------------------------------------------------------
    # Playlists & Liked Songs
    # ------------------------------------------------------------------

    def get_my_playlists(self) -> list:
        session = self._get_session()
        playlists = session.user.playlists() or []
        result = []
        for p in playlists:
            cover = ""
            try:
                cover = p.image(320) if hasattr(p, 'image') else ""
            except Exception:
                pass
            result.append({
                "id": str(p.id),
                "name": p.name,
                "tracks_total": p.num_tracks if hasattr(p, 'num_tracks') else 0,
                "cover": cover,
                "owner": p.creator.name if hasattr(p, 'creator') and p.creator else "",
                "url": f"https://tidal.com/playlist/{p.id}",
            })
        log.info(f"Playlists: {len(result)}")
        return result

    def get_liked_songs(self, limit: int = 500) -> list:
        session = self._get_session()
        favorites = session.user.favorites
        tracks = favorites.tracks(limit=limit) or []
        result = [self._format_track(t) for t in tracks if hasattr(t, 'name')]
        log.info(f"Liked songs: {len(result)}")
        return result

    def _playlist_tracks(self, playlist_id: str):
        session = self._get_session()
        playlist = session.playlist(playlist_id)
        tracks = playlist.tracks() or []
        result = [self._format_track(t) for t in tracks if hasattr(t, 'name')]
        return result, playlist.name if hasattr(playlist, 'name') else ""

    # ------------------------------------------------------------------
    # Album & Artist
    # ------------------------------------------------------------------

    def get_album(self, album_id: str) -> dict:
        session = self._get_session()
        album = session.album(int(album_id))
        tracks = album.tracks() or []
        return {
            "name": album.name,
            "artist": album.artist.name if album.artist else "",
            "release_date": str(album.release_date) if hasattr(album, 'release_date') else "",
            "cover": self._album_cover(album),
            "tracks": [self._format_track(t) for t in tracks],
        }

    def get_artist(self, artist_id: str) -> dict:
        session = self._get_session()
        artist = session.artist(int(artist_id))
        top_tracks = artist.get_top_tracks(limit=10) or []
        albums = artist.get_albums(limit=20) or []
        return {
            "name": artist.name,
            "cover": artist.image(320) if hasattr(artist, 'image') else "",
            "top_tracks": [self._format_track(t) for t in top_tracks],
            "albums": [self._format_album(a) for a in albums],
        }

    # ------------------------------------------------------------------
    # Formatting helpers
    # ------------------------------------------------------------------

    def _format_track(self, t) -> dict:
        cover = ""
        try:
            if hasattr(t, 'album') and t.album:
                cover = self._album_cover(t.album)
        except Exception:
            pass
        return {
            "id": str(t.id),
            "name": t.name,
            "artist": t.artist.name if hasattr(t, 'artist') and t.artist else "",
            "artist_id": str(t.artist.id) if hasattr(t, 'artist') and t.artist else "",
            "album": t.album.name if hasattr(t, 'album') and t.album else "",
            "cover": cover,
            "duration_ms": (t.duration or 0) * 1000 if hasattr(t, 'duration') else 0,
            "uri": f"tidal:track:{t.id}",
            "preview_url": None,
            "external_url": f"https://tidal.com/track/{t.id}",
        }

    def _format_album(self, a) -> dict:
        return {
            "id": str(a.id),
            "name": a.name,
            "artists": [{"name": a.artist.name, "id": str(a.artist.id)}] if hasattr(a, 'artist') and a.artist else [],
            "cover": self._album_cover(a),
            "release_date": str(a.release_date) if hasattr(a, 'release_date') else "",
        }

    def _format_artist(self, ar) -> dict:
        cover = ""
        try:
            cover = ar.image(320) if hasattr(ar, 'image') else ""
        except Exception:
            pass
        return {
            "id": str(ar.id),
            "name": ar.name,
            "cover": cover,
            "genres": [],
        }

    def _album_cover(self, album) -> str:
        try:
            return album.image(640) if hasattr(album, 'image') else ""
        except Exception:
            return ""
