import re
import json
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests as _requests
import spotipy

from core.logger import get_logger
from core.app_state import AppState

log = get_logger("spotify")

SCOPES = "user-library-read user-read-private playlist-read-private playlist-read-collaborative"
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

    def _get_user_market(self) -> str:
        """Retorna o país do user (ex: 'PT', 'MZ') para o param market."""
        if not self._sp:
            return ""
        try:
            user = self._sp.current_user()
            return user.get("country", "")
        except Exception:
            return ""

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

    def search(self, query: str, limit: int = 10) -> dict:
        """
        Pesquisa no Spotify por texto.
        Retorna: {"tracks": [...], "albums": [...], "artists": [...]}
        """
        if not self._sp and not self.client_id:
            raise RuntimeError("Spotify não conectado")

        sp_instance = self._sp if self._sp else self._get_public_sp()

        # Spotify API search limit: 0-10 (Dev Mode), default 5
        safe_limit = min(limit, 10)
        results = {}
        for try_limit in [safe_limit, 5, 3]:
            try:
                log.info(f"Search: '{query}' (limit={try_limit})")
                results = sp_instance.search(q=query, limit=try_limit, type="track,album,artist")
                break
            except Exception as e:
                if "Invalid limit" in str(e) and try_limit > 3:
                    log.warning(f"Search falhou com limit={try_limit}, a tentar menor...")
                    continue
                raise

        tracks = []
        for t in (results.get("tracks", {}).get("items") or []):
            tracks.append(self._parse_track(t))

        albums = []
        for a in (results.get("albums", {}).get("items") or []):
            images = a.get("images") or []
            artists = [ar["name"] for ar in (a.get("artists") or [])]
            albums.append({
                "id": a.get("id", ""),
                "name": a.get("name", ""),
                "artist": ", ".join(artists),
                "year": (a.get("release_date") or "")[:4],
                "cover_url": images[0]["url"] if images else "",
                "total_tracks": a.get("total_tracks", 0),
                "album_type": a.get("album_type", "album"),
                "url": a.get("external_urls", {}).get("spotify", ""),
            })

        artists = []
        for ar in (results.get("artists", {}).get("items") or []):
            images = ar.get("images") or []
            artists.append({
                "id": ar.get("id", ""),
                "name": ar.get("name", ""),
                "cover_url": images[0]["url"] if images else "",
                "genres": (ar.get("genres") or [])[:3],
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

    def get_recommendations(self, seed_tracks: list[dict] = None, limit: int = 10) -> list[dict]:
        """Recomendações via top tracks de artistas das liked songs.
        O endpoint /recommendations foi deprecado pelo Spotify em Nov 2024."""
        sp = self._sp or self._get_public_sp()
        if not seed_tracks:
            return []

        # Extrair artist IDs únicos das seed tracks
        artist_ids = []
        seen_artists = set()
        seed_ids = set()
        for t in seed_tracks:
            if not isinstance(t, dict):
                continue
            seed_ids.add(t.get("id", ""))
            aid = t.get("artist_id", "")
            if aid and aid not in seen_artists:
                seen_artists.add(aid)
                artist_ids.append(aid)
            if len(artist_ids) >= 3:
                break

        if not artist_ids:
            return []

        # Buscar top tracks de cada artista (excluindo as seed)
        tracks = []
        seen_tracks = set(seed_ids)
        for aid in artist_ids:
            try:
                results = sp._get(f"artists/{aid}/top-tracks")
                for t in (results.get("tracks") or []):
                    if t["id"] not in seen_tracks:
                        seen_tracks.add(t["id"])
                        tracks.append(self._parse_track(t))
                    if len(tracks) >= limit:
                        break
            except Exception as e:
                log.debug(f"Top tracks falhou para artist {aid}: {e}")
            if len(tracks) >= limit:
                break

        return tracks[:limit]

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

    def _extract_paging_tracks(self, results: dict) -> list[dict]:
        """Extrai tracks de um paging object, com paginação."""
        tracks = []
        while results:
            for item in (results.get("items") or []):
                t = item.get("track") if "track" in item else item
                if not t or not t.get("id") or t.get("type") != "track":
                    continue
                try:
                    tracks.append(self._parse_track(t))
                except Exception:
                    continue
            if results.get("next"):
                try:
                    results = self._sp.next(results)
                except Exception:
                    break
            else:
                break
        return tracks

    def _playlist_tracks(self, playlist_id: str):
        tracks = []
        name = "Playlist"
        market = self._get_user_market()

        # Estratégia 1: playlist() completo
        try:
            kwargs = {"additional_types": ("track",)}
            if market:
                kwargs["market"] = market
            data = self._sp.playlist(playlist_id, **kwargs)
            name = data.get("name", "Playlist")
            # Spotify migra de "tracks" para "items" — verificar ambos
            results = data.get("tracks") or data.get("items") or {}
            items_count = len(results.get("items") or [])
            log.info(f"[PLAYLIST] '{name}': {items_count} items inline")
            if items_count > 0:
                tracks = self._extract_paging_tracks(results)
        except Exception as e:
            log.warning(f"[PLAYLIST] playlist() falhou: {e}")

        # Estratégia 2: playlist_items() fallback
        if not tracks:
            try:
                kwargs2 = {"limit": 50, "additional_types": ("track",)}
                if market:
                    kwargs2["market"] = market
                results = self._sp.playlist_items(playlist_id, **kwargs2)
                tracks = self._extract_paging_tracks(results)
            except Exception as e:
                log.warning(f"[PLAYLIST] playlist_items falhou (esperado em Dev Mode): {e}")

        # Estratégia 3: embed page scraping (Dev Mode workaround)
        if not tracks:
            log.info(f"[PLAYLIST] '{name}': API retornou 0 tracks, a tentar embed fallback...")
            tracks = self._embed_playlist_tracks(playlist_id)

        log.info(f"[PLAYLIST] '{name}': {len(tracks)} tracks FINAL")
        return tracks, name

    def get_album(self, album_id: str) -> dict:
        """Retorna info do álbum + todas as tracks."""
        sp = self._sp or self._get_public_sp()
        album = sp.album(album_id)
        images = album.get("images") or []
        alb_artists = [a["name"] for a in (album.get("artists") or [])]
        album_info = {
            "id": album["id"],
            "name": album.get("name", ""),
            "artist": ", ".join(alb_artists),
            "artist_id": (album.get("artists") or [{}])[0].get("id", ""),
            "cover_url": images[0]["url"] if images else "",
            "year": (album.get("release_date") or "")[:4],
            "total_tracks": album.get("total_tracks", 0),
        }
        tracks = []
        results = album.get("tracks", {})
        while True:
            for t in (results.get("items") or []):
                tracks.append(self._parse_track(t, album=album))
            if results.get("next"):
                results = sp.next(results)
            else:
                break
        return {"album": album_info, "tracks": tracks}

    def search_type(self, query: str, search_type: str, limit: int = 10, offset: int = 0) -> dict:
        """Search paginado de um só tipo (track, album, artist)."""
        sp = self._sp or self._get_public_sp()
        safe_limit = min(limit, 10)
        results = sp.search(q=query, limit=safe_limit, offset=offset, type=search_type)
        key = search_type + "s"  # "track" → "tracks"
        data = results.get(key, {})
        total = data.get("total", 0)
        items_raw = data.get("items") or []

        items = []
        if search_type == "track":
            items = [self._parse_track(t) for t in items_raw]
        elif search_type == "album":
            for a in items_raw:
                img = a.get("images") or []
                arts = [ar["name"] for ar in (a.get("artists") or [])]
                items.append({
                    "id": a.get("id", ""), "name": a.get("name", ""),
                    "artist": ", ".join(arts),
                    "year": (a.get("release_date") or "")[:4],
                    "cover_url": img[0]["url"] if img else "",
                    "total_tracks": a.get("total_tracks", 0),
                })
        elif search_type == "artist":
            for ar in items_raw:
                img = ar.get("images") or []
                items.append({
                    "id": ar.get("id", ""), "name": ar.get("name", ""),
                    "cover_url": img[0]["url"] if img else "",
                    "genres": (ar.get("genres") or [])[:3],
                })

        return {"items": items, "total": total, "offset": offset, "has_more": offset + safe_limit < total}

    # ------------------------------------------------------------------
    # Embed fallback (Dev Mode workaround)
    # ------------------------------------------------------------------

    def _embed_playlist_tracks(self, playlist_id: str) -> list[dict]:
        """Fallback: scrape Spotify embed page quando API bloqueia tracks (Dev Mode)."""
        embed_url = f"https://open.spotify.com/embed/playlist/{playlist_id}"
        log.info(f"[EMBED] A tentar embed fallback: {embed_url}")

        session = _requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        try:
            resp = session.get(embed_url, timeout=15)
            if resp.status_code != 200:
                log.warning(f"[EMBED] HTTP {resp.status_code}")
                return []
        except Exception as e:
            log.warning(f"[EMBED] Request falhou: {e}")
            return []

        html = resp.text

        # Extrair __NEXT_DATA__ JSON (fonte principal de dados estruturados)
        next_data = self._embed_parse_next_data(html)

        # Strategy A: IDs do __NEXT_DATA__ → batch fetch (rápido se API permitir)
        if next_data:
            track_ids = self._embed_extract_ids_from_data(next_data)
            if track_ids:
                log.info(f"[EMBED] Strategy A: {len(track_ids)} IDs, a tentar batch fetch...")
                tracks = self._batch_fetch_tracks(track_ids)
                if tracks:
                    return tracks

        # Strategy B: nomes/artistas do __NEXT_DATA__ → parallel search
        if next_data:
            entries = self._embed_extract_names_from_data(next_data)
            if entries:
                log.info(f"[EMBED] Strategy B: {len(entries)} tracks com nome/artista, a pesquisar...")
                return self._parallel_search_tracks(entries)

        # Strategy C: regex fallback no HTML para IDs
        track_ids = self._embed_extract_ids_regex(html)
        if track_ids:
            log.info(f"[EMBED] Strategy C: {len(track_ids)} IDs via regex")
            tracks = self._batch_fetch_tracks(track_ids)
            if tracks:
                return tracks

        log.warning("[EMBED] Nenhuma strategy funcionou")
        return []

    def _embed_parse_next_data(self, html: str) -> dict | None:
        """Parse do __NEXT_DATA__ JSON do embed."""
        m = re.search(r'<script\s+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except (json.JSONDecodeError, ValueError):
            return None

    def _embed_extract_ids_from_data(self, data: dict) -> list[str]:
        """Extrai track IDs do __NEXT_DATA__ JSON."""
        seen = set()
        ids = []

        def walk(obj):
            if isinstance(obj, str):
                wm = re.search(r'spotify:track:([a-zA-Z0-9]{22})', obj)
                if wm and wm.group(1) not in seen:
                    seen.add(wm.group(1))
                    ids.append(wm.group(1))
            elif isinstance(obj, dict):
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        return ids

    def _embed_extract_names_from_data(self, data: dict) -> list[dict]:
        """Extrai nomes e artistas de tracks do __NEXT_DATA__ JSON."""
        entries = []
        seen = set()

        def walk(obj):
            if isinstance(obj, dict):
                # Detectar objectos track: têm "uri" com spotify:track e "title"/"name"
                uri = obj.get("uri", "")
                is_track = "spotify:track:" in uri
                title = obj.get("title") or obj.get("name") or ""
                if is_track and title:
                    # Extrair artistas — pode ser lista de objectos ou string
                    artist = ""
                    artists_raw = obj.get("artists") or obj.get("subtitle") or ""
                    if isinstance(artists_raw, list):
                        names = []
                        for a in artists_raw:
                            if isinstance(a, dict):
                                names.append(a.get("name", ""))
                            elif isinstance(a, str):
                                names.append(a)
                        artist = ", ".join(n for n in names if n)
                    elif isinstance(artists_raw, str):
                        artist = artists_raw
                    if not artist:
                        artist = obj.get("artist", "")
                    if title and artist:
                        key = f"{title.lower()}|{artist.lower()}"
                        if key not in seen:
                            seen.add(key)
                            entries.append({"title": title, "artist": artist})
                    elif title:
                        key = title.lower()
                        if key not in seen:
                            seen.add(key)
                            entries.append({"title": title, "artist": ""})
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)
        return entries

    def _embed_extract_ids_regex(self, html: str) -> list[str]:
        """Fallback: extrai track IDs do HTML via regex."""
        patterns = [
            r'spotify:track:([a-zA-Z0-9]{22})',
            r'/track/([a-zA-Z0-9]{22})',
        ]
        seen = set()
        ids = []
        for pat in patterns:
            for m in re.finditer(pat, html):
                tid = m.group(1)
                if tid not in seen:
                    seen.add(tid)
                    ids.append(tid)
        return ids

    def _batch_fetch_tracks(self, track_ids: list[str]) -> list[dict]:
        """Batch fetch de tracks por ID. Falha rápido no primeiro 403."""
        sp = self._sp or self._get_public_sp()
        tracks = []
        for i in range(0, len(track_ids), 50):
            batch = track_ids[i:i + 50]
            try:
                results = sp.tracks(batch)
                for t in (results.get("tracks") or []):
                    if t and t.get("id"):
                        tracks.append(self._parse_track(t))
            except Exception as e:
                if "403" in str(e):
                    log.info(f"[EMBED] batch fetch 403 — endpoint bloqueado em Dev Mode")
                    return []  # Falha rápido, não tenta mais batches
                log.warning(f"[EMBED] batch fetch falhou (batch {i}): {e}")
        log.info(f"[EMBED] Batch fetch: {len(tracks)}/{len(track_ids)} tracks")
        return tracks

    def _parallel_search_tracks(self, entries: list[dict]) -> list[dict]:
        """Search paralelo por nome/artista usando ThreadPoolExecutor."""
        sp = self._sp or self._get_public_sp()
        tracks = [None] * len(entries)

        def search_one(idx: int, entry: dict):
            title = entry["title"]
            artist = entry.get("artist", "")
            if artist:
                q = f"track:{title} artist:{artist}"
            else:
                q = f"track:{title}"
            # Spotify search query max 250 chars
            if len(q) > 240:
                q = q[:240]
            try:
                res = sp.search(q=q, limit=1, type="track")
                items = res.get("tracks", {}).get("items") or []
                if items:
                    return idx, self._parse_track(items[0])
            except Exception as e:
                log.debug(f"[EMBED] search falhou para '{title}': {e}")
            return idx, None

        workers = min(8, len(entries))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(search_one, i, e) for i, e in enumerate(entries)]
            for f in as_completed(futures):
                idx, track = f.result()
                if track:
                    tracks[idx] = track

        result = [t for t in tracks if t is not None]
        log.info(f"[EMBED] Parallel search: {len(result)}/{len(entries)} tracks encontradas")
        return result

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
        track_artists = track.get("artists") or []
        artists = [a["name"] for a in track_artists]
        first_artist_id = track_artists[0]["id"] if track_artists else ""
        images = alb.get("images") or []
        cover_url = images[0]["url"] if images else ""
        alb_artists = alb.get("artists") or []
        album_artist = alb_artists[0]["name"] if alb_artists else (artists[0] if artists else "")
        return {
            "id": track.get("id", ""),
            "title": track.get("name", ""),
            "artist": ", ".join(artists),
            "artist_id": first_artist_id,
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
