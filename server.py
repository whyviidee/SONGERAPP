#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SONGER Setup Server - localhost:8888
Configura credenciais Spotify e faz OAuth sem copiar/colar URLs.

Uso:
    pip install flask
    python server.py
"""

import json
import os
import subprocess
import sys
import time
import urllib.parse
import webbrowser
import threading
import uuid
import queue as queue_mod
from collections import OrderedDict
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import Flask, request, redirect, render_template, jsonify, send_file
from core.config import Config
from core.library import scan_library
from core.history import DownloadHistory

app = Flask(__name__, template_folder="web", static_folder="web/static")
app.secret_key = "songer-setup-key"

REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPES = "user-library-read user-read-private playlist-read-private playlist-read-collaborative"
CONFIG_PATH = Path.home() / ".songer" / "config.json"
TOKEN_PATH = Path.home() / ".songer" / ".spotify_token.json"

# Guarda temporariamente client_id/secret durante o fluxo OAuth
_session = {}

# Download queue state
_download_queue: dict = OrderedDict()
_queue_lock = threading.Lock()
_sse_queues: list = []

# ZIP download jobs
_zip_jobs: dict = {}

# Persistent mapping of Spotify track ID → local file path
_DOWNLOADED_MAP_PATH = Path.home() / ".songer" / "downloaded_map.json"

def _load_downloaded_map() -> dict:
    if _DOWNLOADED_MAP_PATH.exists():
        try:
            with open(_DOWNLOADED_MAP_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_downloaded_entry(track_id: str, file_path: str):
    m = _load_downloaded_map()
    m[track_id] = file_path
    _DOWNLOADED_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DOWNLOADED_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False)


def _load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}


def _save_config(data: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2))


def _save_token(data: dict):
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(json.dumps(data))


# ------------------------------------------------------------------
# Rotas
# ------------------------------------------------------------------

@app.route("/")
def index():
    cfg = _load_config()
    client_id = cfg.get("spotify", {}).get("client_id", "")
    client_secret = cfg.get("spotify", {}).get("client_secret", "")
    has_token = TOKEN_PATH.exists()
    return render_template(
        "index.html",
        client_id=client_id,
        client_secret=client_secret,
        has_token=has_token,
    )


@app.route("/api/spotify/auth-url", methods=["POST"])
def api_spotify_auth_url():
    """Save Spotify credentials and return the OAuth URL (for system browser flow)."""
    data = request.get_json() or {}
    client_id = data.get("client_id", "").strip()
    client_secret = data.get("client_secret", "").strip()

    if not client_id or not client_secret:
        return jsonify({"error": "client_id and client_secret required"}), 400

    cfg = _load_config()
    cfg.setdefault("spotify", {})
    cfg["spotify"]["client_id"] = client_id
    cfg["spotify"]["client_secret"] = client_secret
    cfg["spotify"]["redirect_uri"] = REDIRECT_URI
    _save_config(cfg)

    _session["client_id"] = client_id
    _session["client_secret"] = client_secret

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return jsonify({"ok": True, "url": auth_url})


@app.route("/setup", methods=["POST"])
def setup():
    client_id = request.form.get("client_id", "").strip()
    client_secret = request.form.get("client_secret", "").strip()

    if not client_id or not client_secret:
        return redirect("/?error=missing")

    # Guardar credenciais
    cfg = _load_config()
    cfg.setdefault("spotify", {})
    cfg["spotify"]["client_id"] = client_id
    cfg["spotify"]["client_secret"] = client_secret
    cfg["spotify"]["redirect_uri"] = REDIRECT_URI
    _save_config(cfg)

    # Guardar temporariamente para o callback
    _session["client_id"] = client_id
    _session["client_secret"] = client_secret

    # Redirecionar para Spotify OAuth
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error or not code:
        return render_template("index.html", error=error or "cancelled", has_token=False)

    client_id = _session.get("client_id")
    client_secret = _session.get("client_secret")

    if not client_id or not client_secret:
        # Tentar carregar do config
        cfg = _load_config()
        client_id = cfg.get("spotify", {}).get("client_id", "")
        client_secret = cfg.get("spotify", {}).get("client_secret", "")

    if not client_id:
        return render_template("index.html", error="no_credentials", has_token=False)

    # Trocar code por token
    try:
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            auth=(client_id, client_secret),
            timeout=15,
        )
        r.raise_for_status()
        token_data = r.json()
        token_data["expires_at"] = time.time() + token_data.get("expires_in", 3600)
        _save_token(token_data)
    except Exception as e:
        return render_template("index.html", error=str(e), has_token=False)

    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>SONGER</title>
<style>body{background:#0a0a0f;color:#f0f0f5;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;flex-direction:column;gap:12px;}
h2{color:#22c55e;margin:0;}p{color:rgba(240,240,245,0.5);font-size:14px;margin:0;}</style></head>
<body><h2>Spotify connected!</h2><p>You can close this tab and return to SONGER.</p></body></html>"""


@app.route("/status")
def status():
    cfg = _load_config()
    has_token = TOKEN_PATH.exists()
    client_id = cfg.get("spotify", {}).get("client_id", "")
    return jsonify({
        "configured": bool(client_id),
        "has_token": has_token,
        "client_id_set": bool(client_id),
    })


@app.route("/disconnect", methods=["POST"])
def disconnect():
    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
    return redirect("/")


_FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"

@app.route("/app")
@app.route("/app/<path:path>")
def app_shell(path=''):
    if not TOKEN_PATH.exists():
        return redirect("/?error=no_token")
    # Serve React build (static assets or fallback to index.html)
    if path and (_FRONTEND_DIST / path).exists():
        return send_file(_FRONTEND_DIST / path)
    index = _FRONTEND_DIST / "index.html"
    if index.exists():
        return send_file(index)
    # Fallback to legacy app.html
    return render_template("app.html")

@app.route("/assets/<path:path>")
def serve_react_assets(path):
    return send_file(_FRONTEND_DIST / "assets" / path)


# ------------------------------------------------------------------
# Tidal support
# ------------------------------------------------------------------
_tidal_client = None
_tidal_login_state = {}

def _get_tidal():
    global _tidal_client
    if _tidal_client is None:
        from core.tidal import TidalClient
        _tidal_client = TidalClient()
    return _tidal_client

def _get_music_service():
    """Returns 'tidal' or 'spotify' based on config."""
    cfg = _load_config()
    return cfg.get("music_service", "spotify")


@app.route("/api/status")
def api_status():
    cfg = _load_config()
    service = _get_music_service()

    spotify_ok = TOKEN_PATH.exists() and bool(cfg.get("spotify", {}).get("client_id"))
    tidal_ok = False
    try:
        tidal_ok = _get_tidal().connect()
    except Exception:
        pass

    slsk_ok = False
    if cfg.get("soulseek", {}).get("enabled"):
        try:
            import requests as req
            slsk_url = cfg.get("soulseek", {}).get("slskd_url", "http://localhost:5030")
            r = req.get(f"{slsk_url}/api/v0/application", timeout=2)
            slsk_ok = r.status_code == 200
        except Exception:
            slsk_ok = False

    return jsonify({
        "music_service": service,
        "spotify": "ok" if spotify_ok else "error",
        "tidal": "ok" if tidal_ok else "error",
        "soulseek": "ok" if slsk_ok else "error",
    })


@app.route("/api/tidal/login", methods=["POST"])
def api_tidal_login():
    """Start Tidal OAuth login."""
    try:
        tidal = _get_tidal()
        result = tidal.login_oauth()
        _tidal_login_state["future"] = result["future"]
        _tidal_login_state["session"] = result["session"]
        return jsonify({
            "ok": True,
            "url": result["verification_uri"],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tidal/login/complete", methods=["POST"])
def api_tidal_login_complete():
    """Check if Tidal OAuth completed."""
    future = _tidal_login_state.get("future")
    session = _tidal_login_state.get("session")
    if not future or not session:
        return jsonify({"error": "No login in progress"}), 400
    try:
        tidal = _get_tidal()
        ok = tidal.complete_login(future, session)
        if ok:
            # Set music service to tidal
            cfg = _load_config()
            cfg["music_service"] = "tidal"
            _save_config(cfg)
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Login not completed yet"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/tidal/disconnect", methods=["POST"])
def api_tidal_disconnect():
    """Clear Tidal session."""
    from pathlib import Path
    session_path = Path.home() / ".songer" / "tidal_session.json"
    if session_path.exists():
        session_path.unlink()
    _tidal_login_state.clear()
    global _tidal_client
    _tidal_client = None
    return jsonify({"ok": True})


@app.route("/api/service", methods=["POST"])
def api_set_service():
    """Switch between spotify and tidal."""
    data = request.get_json() or {}
    service = data.get("service", "spotify")
    if service not in ("spotify", "tidal"):
        return jsonify({"error": "Invalid service"}), 400
    cfg = _load_config()
    cfg["music_service"] = service
    _save_config(cfg)
    return jsonify({"ok": True, "service": service})


@app.route("/api/stats")
def api_stats():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))

    try:
        files = scan_library(dl_path)
    except Exception:
        files = []

    total_mb = sum(f.get("size_mb", 0) for f in files)

    playlists_count = 0
    try:
        sp = _get_spotify()
        sp.connect()
        playlists_count = len(sp.get_my_playlists())
    except Exception:
        pass

    active = len([t for t in _download_queue.values() if t.get("status") == "downloading"]) if "_download_queue" in globals() else 0

    # Top artists by file count
    artist_counts = {}
    for f in files:
        a = f.get("artist", "").strip()
        if a:
            artist_counts[a] = artist_counts.get(a, 0) + 1
    top_artists_raw = sorted(artist_counts.items(), key=lambda x: -x[1])[:8]

    # Enrich top artists with Spotify images
    top_artists = []
    try:
        sp = _get_spotify()
        sp.connect()
        for name, count in top_artists_raw:
            cover = ""
            try:
                results = sp.search(name, limit=1)
                artists = results.get("artists", [])
                if artists:
                    cover = artists[0].get("cover_url", "")
            except Exception:
                pass
            top_artists.append({"name": name, "count": count, "cover": cover})
    except Exception:
        top_artists = [{"name": a, "count": c, "cover": ""} for a, c in top_artists_raw]

    pending = len([t for t in _download_queue.values() if t.get("status") in ("pending", "downloading")])

    return jsonify({
        "tracks": len(files),
        "downloading": active,
        "pending": pending,
        "playlists": playlists_count,
        "storage_mb": round(total_mb, 1),
        "top_artists": top_artists,
    })


@app.route("/api/recommendations")
def api_recommendations():
    try:
        sp = _get_spotify()
        sp.connect()
        # Usar liked songs como seed para descobrir artistas relacionados
        liked = sp.get_liked_songs(limit=5)
        if not liked:
            return jsonify([])
        recs = sp.get_recommendations(seed_tracks=liked[:5], limit=10)
        tracks = []
        for t in recs:
            tracks.append({
                "id": t.get("id", ""), "name": t.get("title", ""),
                "artist": t.get("artist", ""), "album": t.get("album", ""),
                "cover": t.get("cover_url", ""), "duration_ms": t.get("duration_ms", 0),
            })
        return jsonify(tracks)
    except Exception as e:
        return jsonify([])


# ------------------------------------------------------------------
# Spotify lazy init
# ------------------------------------------------------------------

_spotify = None


def _get_spotify():
    global _spotify
    if _spotify is None:
        from core.spotify import SpotifyClient
        cfg = _load_config()
        client_id = cfg.get("spotify", {}).get("client_id", "")
        client_secret = cfg.get("spotify", {}).get("client_secret", "")
        if not client_id or not client_secret:
            raise RuntimeError("Spotify não configurado — falta client_id/client_secret")
        _spotify = SpotifyClient(client_id, client_secret)
    return _spotify


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q required"}), 400

    # Use Tidal if configured
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            # Tidal search returns same format as we need
            if "tidal.com" in q:
                # TODO: parse tidal URLs
                pass
            results = tidal.search(q, limit=10)
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    try:
        sp = _get_spotify()
        sp.connect()
        if "spotify.com" in q or q.startswith("spotify:"):
            # URL ou URI Spotify — devolver as tracks do álbum/playlist/track
            tracks_raw, _name = sp.get_tracks(q)
            tracks = []
            for t in tracks_raw:
                tracks.append({
                    "id": t.get("id", ""),
                    "name": t.get("title", t.get("name", "")),
                    "artist": t.get("artist", ""),
                    "artist_id": t.get("artist_id", ""),
                    "album": t.get("album", ""),
                    "cover": t.get("cover_url", ""),
                    "duration_ms": t.get("duration_ms", 0),
                    "preview_url": t.get("preview_url", ""),
                    "uri": "",
                    "external_url": "",
                })
        else:
            results = sp.search(q, limit=10)
            tracks = []
            for t in results.get("tracks", []):
                tracks.append({
                    "id": t.get("id", ""),
                    "name": t.get("title", ""),
                    "artist": t.get("artist", ""),
                    "artist_id": t.get("artist_id", ""),
                    "album": t.get("album", ""),
                    "cover": t.get("cover_url", ""),
                    "duration_ms": t.get("duration_ms", 0),
                    "preview_url": t.get("preview_url", ""),
                    "uri": "",
                    "external_url": "",
                })
            albums = []
            for a in results.get("albums", []):
                albums.append({
                    "id": a.get("id", ""),
                    "name": a.get("name", ""),
                    "artist": a.get("artist", ""),
                    "year": a.get("year", ""),
                    "cover": a.get("cover_url", ""),
                    "total_tracks": a.get("total_tracks", 0),
                    "album_type": a.get("album_type", "album"),
                    "url": a.get("url", ""),
                })
            artists = []
            for ar in results.get("artists", []):
                artists.append({
                    "id": ar.get("id", ""),
                    "name": ar.get("name", ""),
                    "cover": ar.get("cover_url", ""),
                    "genres": ar.get("genres", []),
                    "url": ar.get("url", ""),
                })
            return jsonify({"tracks": tracks, "albums": albums, "artists": artists})
        return jsonify({"tracks": tracks, "albums": [], "artists": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/artist/<artist_id>")
def api_artist(artist_id):
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            return jsonify(tidal.get_artist(artist_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        sp = _get_spotify()
        sp.connect()
        pub = sp._get_public_sp()
        artist_raw = pub.artist(artist_id)
        images = artist_raw.get("images") or []
        artist_info = {
            "id": artist_raw["id"],
            "name": artist_raw.get("name", ""),
            "cover": images[0]["url"] if images else "",
            "genres": (artist_raw.get("genres") or [])[:5],
            "followers": (artist_raw.get("followers") or {}).get("total", 0),
        }
        top_tracks_raw, _ = sp.get_artist_top_tracks(artist_id)
        top_tracks = []
        for t in top_tracks_raw:
            top_tracks.append({
                "id": t.get("id", ""), "name": t.get("title", ""),
                "artist": t.get("artist", ""), "artist_id": t.get("artist_id", ""),
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""), "duration_ms": t.get("duration_ms", 0),
                "preview_url": t.get("preview_url", ""),
                "uri": "", "external_url": "",
            })
        albums = []
        for a in sp.get_artist_albums(artist_id):
            albums.append({
                "id": a.get("id", ""), "name": a.get("name", ""),
                "year": a.get("year", ""), "cover": a.get("cover_url", ""),
                "total_tracks": a.get("total_tracks", 0),
                "album_type": a.get("album_type", "album"),
            })
        return jsonify({"artist": artist_info, "top_tracks": top_tracks, "albums": albums})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/album/<album_id>")
def api_album(album_id):
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            return jsonify(tidal.get_album(album_id))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        sp = _get_spotify()
        sp.connect()
        data = sp.get_album(album_id)
        album_info = data["album"]
        tracks = []
        for t in data["tracks"]:
            tracks.append({
                "id": t.get("id", ""), "name": t.get("title", ""),
                "artist": t.get("artist", ""), "artist_id": t.get("artist_id", ""),
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""), "duration_ms": t.get("duration_ms", 0),
                "preview_url": t.get("preview_url", ""),
                "uri": "", "external_url": "",
            })
        return jsonify({
            "album": {
                "id": album_info["id"], "name": album_info["name"],
                "artist": album_info["artist"], "artist_id": album_info.get("artist_id", ""),
                "cover": album_info["cover_url"], "year": album_info["year"],
                "total_tracks": album_info["total_tracks"],
            },
            "tracks": tracks,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/search/<search_type>")
def api_search_type(search_type):
    type_map = {"tracks": "track", "albums": "album", "artists": "artist"}
    sp_type = type_map.get(search_type)
    if not sp_type:
        return jsonify({"error": "Invalid type. Use: tracks, albums, artists"}), 400
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"error": "q required"}), 400
    offset = int(request.args.get("offset", 0))
    try:
        sp = _get_spotify()
        sp.connect()
        data = sp.search_type(q, sp_type, limit=10, offset=offset)
        # Normalize field names for frontend
        items = []
        for item in data["items"]:
            if sp_type == "track":
                items.append({
                    "id": item.get("id", ""), "name": item.get("title", ""),
                    "artist": item.get("artist", ""), "artist_id": item.get("artist_id", ""),
                    "album": item.get("album", ""),
                    "cover": item.get("cover_url", ""), "duration_ms": item.get("duration_ms", 0),
                    "preview_url": item.get("preview_url", ""),
                    "uri": "", "external_url": "",
                })
            elif sp_type == "album":
                items.append({
                    "id": item.get("id", ""), "name": item.get("name", ""),
                    "artist": item.get("artist", ""), "year": item.get("year", ""),
                    "cover": item.get("cover_url", ""), "total_tracks": item.get("total_tracks", 0),
                })
            elif sp_type == "artist":
                items.append({
                    "id": item.get("id", ""), "name": item.get("name", ""),
                    "cover": item.get("cover_url", ""), "genres": item.get("genres", []),
                })
        return jsonify({"items": items, "total": data["total"], "offset": data["offset"], "has_more": data["has_more"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/config")
def api_config():
    return jsonify(_load_config())


@app.route("/api/settings", methods=["POST"])
def api_settings():
    data = request.get_json() or {}
    cfg = _load_config()
    for section, values in data.items():
        if section not in cfg:
            cfg[section] = {}
        cfg[section].update(values)
    _save_config(cfg)
    return jsonify({"ok": True})


# ------------------------------------------------------------------
# Download queue
# ------------------------------------------------------------------

@app.route("/api/url-info", methods=["POST"])
def api_url_info():
    """Extract metadata from a direct URL (SoundCloud, Bandcamp, Mixcloud, etc.)."""
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "url required"}), 400
    try:
        from core.ytdlp import YtDlpClient
        info = YtDlpClient().extract_info(url)
        return jsonify({"ok": True, "track": info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json() or {}
    track_id = data.get("id") or data.get("uri", "") or data.get("url", "")
    if not track_id:
        return jsonify({"error": "id required"}), 400

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "track_id": track_id,
        "name": data.get("name", "Unknown"),
        "artist": data.get("artist", ""),
        "album": data.get("album", ""),
        "cover": data.get("cover", ""),
        "uri": data.get("uri", ""),
        "status": "pending",
        "progress": 0,
        "error": "",
    }
    with _queue_lock:
        _download_queue[job_id] = job

    threading.Thread(target=_run_download, args=(job_id, data), daemon=True).start()
    _sse_push({"type": "queue_update"})
    return jsonify({"job_id": job_id})


def _run_download(job_id: str, track: dict):
    with _queue_lock:
        if job_id not in _download_queue:
            return
        _download_queue[job_id]["status"] = "downloading"
    _sse_push({"type": "queue_update"})

    try:
        from core.config import Config
        from core.downloader import Downloader, DownloadResult
        c = Config()
        dl = Downloader(c)
        dl.setup()

        # Build track dict matching the downloader's expected format
        t = {
            "id": track.get("id", ""),
            "title": track.get("name", "") or track.get("title", "Unknown"),
            "artist": track.get("artist", ""),
            "album": track.get("album", ""),
            "cover_url": track.get("cover", "") or track.get("cover_url", ""),
            "uri": track.get("uri", ""),
            "url": track.get("url", ""),
            "genre": track.get("genre", ""),
        }

        cfg = _load_config()
        fmt = cfg.get("download", {}).get("format", "mp3")
        # Allow per-request source override (e.g. "direct" for URL downloads)
        source = track.get("_source") or cfg.get("download", {}).get("source", "youtube")

        result_holder = {}
        done_event = threading.Event()

        def progress_cb(pct):
            with _queue_lock:
                if job_id in _download_queue:
                    _download_queue[job_id]["progress"] = pct
            _sse_push({"type": "progress", "job_id": job_id, "progress": pct})

        def done_cb(result: DownloadResult):
            result_holder["result"] = result
            done_event.set()

        dl.submit(t, fmt, source, progress_cb=progress_cb, done_cb=done_cb)
        done_event.wait(timeout=600)

        result = result_holder.get("result")
        with _queue_lock:
            if job_id in _download_queue:
                if result is not None:
                    _download_queue[job_id]["status"] = "done" if result.success else "error"
                    _download_queue[job_id]["progress"] = 100 if result.success else 0
                    _download_queue[job_id]["error"] = result.error
                    _download_queue[job_id]["path"] = result.path or ""
                    if result.success:
                        try:
                            if track.get("id") and result.path:
                                _save_downloaded_entry(track["id"], result.path)
                            DownloadHistory().add(
                                url=t.get("uri", ""),
                                name=f"{t.get('artist', '')} – {t.get('title', '')}",
                                tracks_count=1, done_count=1, fail_count=0,
                                fmt=fmt, cover=t.get("cover_url", ""),
                            )
                        except Exception:
                            pass
                else:
                    _download_queue[job_id]["status"] = "error"
                    _download_queue[job_id]["error"] = "Timeout"
    except Exception as e:
        with _queue_lock:
            if job_id in _download_queue:
                _download_queue[job_id]["status"] = "error"
                _download_queue[job_id]["error"] = str(e)

    _sse_push({"type": "queue_update"})


@app.route("/api/queue")
def api_queue():
    with _queue_lock:
        return jsonify(list(_download_queue.values()))


@app.route("/api/folder-options")
def api_folder_options():
    home = Path.home()
    return jsonify([
        {"label": "Music/SONGER", "path": str(home / "Music" / "SONGER")},
        {"label": "Downloads/SONGER", "path": str(home / "Downloads" / "SONGER")},
        {"label": "Desktop/SONGER", "path": str(home / "Desktop" / "SONGER")},
    ])


@app.route("/api/downloaded-ids")
def api_downloaded_ids():
    # Start with persistent map (survives restarts)
    result = _load_downloaded_map()
    # Merge in-memory queue (current session downloads)
    with _queue_lock:
        for j in _download_queue.values():
            if j.get("status") == "done" and j.get("track_id") and j.get("path"):
                result[j["track_id"]] = j["path"]
    return jsonify({"ids": list(result.keys())})


@app.route("/api/downloaded-ids", methods=["DELETE"])
def api_downloaded_ids_clear():
    """Clear the downloaded map and in-memory queue done entries."""
    if _DOWNLOADED_MAP_PATH.exists():
        _DOWNLOADED_MAP_PATH.unlink()
    with _queue_lock:
        for j in _download_queue.values():
            if j.get("status") == "done":
                j["status"] = "cleared"
    return jsonify({"ok": True})


@app.route("/api/queue/<job_id>", methods=["DELETE"])
def api_queue_cancel(job_id):
    with _queue_lock:
        if job_id in _download_queue:
            _download_queue[job_id]["status"] = "cancelled"
    _sse_push({"type": "queue_update"})
    return jsonify({"ok": True})


@app.route("/api/queue", methods=["DELETE"])
def api_queue_clear():
    with _queue_lock:
        for job in _download_queue.values():
            if job["status"] in ("pending", "downloading"):
                job["status"] = "cancelled"
    _sse_push({"type": "queue_update"})
    return jsonify({"ok": True})


def _sse_push(data: dict):
    msg = f"data: {json.dumps(data)}\n\n"
    for q in list(_sse_queues):
        try:
            q.put_nowait(msg)
        except Exception:
            pass


@app.route("/api/events")
def api_events():
    q = queue_mod.Queue()
    _sse_queues.append(q)

    def generate():
        try:
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield msg
                except queue_mod.Empty:
                    yield ": ping\n\n"
        except GeneratorExit:
            pass
        finally:
            if q in _sse_queues:
                _sse_queues.remove(q)

    return app.response_class(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ------------------------------------------------------------------
# Playlists, Library, History
# ------------------------------------------------------------------

@app.route("/api/playlists")
def api_playlists():
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            return jsonify(tidal.get_my_playlists())
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        sp = _get_spotify()
        sp.connect()
        playlists = sp.get_my_playlists()
        result = []
        for p in playlists:
            result.append({
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "tracks_total": p.get("total_tracks", 0),
                "cover": p.get("cover_url", ""),
                "url": p.get("url", ""),
                "owner": p.get("owner", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/playlists/<playlist_id>/count")
def api_playlist_count(playlist_id):
    """Lightweight endpoint — returns just the track count for a playlist."""
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            tracks, _ = tidal._playlist_tracks(playlist_id)
            return jsonify({"count": len(tracks)})
        except Exception as e:
            log.warning(f"[COUNT] Tidal error for {playlist_id}: {e}")
            return jsonify({"count": 0}), 200
    try:
        sp = _get_spotify()
        sp.connect()
        data = sp._sp.playlist(playlist_id, fields="tracks.total")
        count = data.get("tracks", {}).get("total", 0)
        return jsonify({"count": count})
    except Exception as e:
        log.warning(f"[COUNT] Spotify error for {playlist_id}: {e}")
        return jsonify({"count": 0}), 200


@app.route("/api/playlists/<playlist_id>/tracks")
def api_playlist_tracks(playlist_id):
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            tracks, _ = tidal._playlist_tracks(playlist_id)
            return jsonify(tracks)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        sp = _get_spotify()
        sp.connect()
        tracks, _name = sp._playlist_tracks(playlist_id)
        result = []
        for t in tracks:
            result.append({
                "id": t.get("id", ""),
                "name": t.get("title", t.get("name", "")),
                "artist": t.get("artist", ""),
                "artist_id": t.get("artist_id", ""),
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "preview_url": t.get("preview_url", ""),
                "uri": t.get("id", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library")
def api_library():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))
    legacy_paths = cfg.get("download", {}).get("legacy_paths", [])
    try:
        files = scan_library(dl_path)
        # Also scan legacy paths (old download locations user chose to keep)
        for lp in legacy_paths:
            if lp and lp != dl_path and Path(lp).exists():
                try:
                    files.extend(scan_library(lp))
                except Exception:
                    pass
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/track-cover")
def api_track_cover():
    """Extract embedded cover art from audio file."""
    path = request.args.get("path", "")
    if not path:
        return ("", 404)
    p = Path(path)
    if not p.exists():
        return ("", 404)
    try:
        from flask import Response
        ext = p.suffix.lower()
        img_data = mime = None
        if ext == ".mp3":
            from mutagen.id3 import ID3
            tags = ID3(str(p))
            for tag in tags.values():
                if hasattr(tag, "FrameID") and tag.FrameID == "APIC":
                    img_data, mime = tag.data, tag.mime
                    break
        elif ext == ".flac":
            from mutagen.flac import FLAC
            audio = FLAC(str(p))
            if audio.pictures:
                img_data, mime = audio.pictures[0].data, audio.pictures[0].mime
        if img_data:
            return Response(img_data, content_type=mime or "image/jpeg")
    except Exception:
        pass
    return ("", 404)


@app.route("/api/history")
def api_history():
    h = DownloadHistory()
    entries = h.get_all()
    # Try to fill missing covers via Spotify search
    needs_save = False
    try:
        sp = _get_spotify()
        sp.connect()
        for entry in entries:
            if entry.get("cover"):
                continue
            name = entry.get("name", "")
            if not name:
                continue
            try:
                results = sp.search(name.replace(" – ", " "), limit=1)
                tracks = results.get("tracks", [])
                if tracks and tracks[0].get("cover_url"):
                    entry["cover"] = tracks[0]["cover_url"]
                    needs_save = True
            except Exception:
                break  # stop trying if Spotify fails
    except Exception:
        pass
    if needs_save:
        h._entries = entries
        h._save()
    return jsonify(entries)


@app.route("/api/history", methods=["DELETE"])
def api_history_clear():
    h = DownloadHistory()
    h.clear()
    return jsonify({"ok": True})


@app.route("/api/browse-folder")
def api_browse_folder():
    """Abre folder picker nativo e devolve o path escolhido."""
    try:
        if sys.platform == "darwin":
            script = (
                'set chosen to POSIX path of (choose folder with prompt "Choose download folder")'
            )
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=60
            )
            chosen = result.stdout.strip().rstrip("/")
            if result.returncode != 0 or not chosen:
                return jsonify({"path": ""})
            return jsonify({"path": chosen})
        elif sys.platform == "win32":
            ps = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                '$f=New-Object System.Windows.Forms.Form;'
                '$f.TopMost=$true;'
                '$d=New-Object System.Windows.Forms.FolderBrowserDialog;'
                '$d.Description="Choose download folder";'
                '$d.ShowNewFolderButton=$true;'
                'if($d.ShowDialog($f) -eq "OK"){$d.SelectedPath}else{""}'
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-STA", "-Command", ps],
                capture_output=True, text=True, timeout=60
            )
            chosen = result.stdout.strip()
            return jsonify({"path": chosen})
        else:
            return jsonify({"error": "Not supported on this platform"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/open-folder")
def api_open_folder():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))
    p = Path(dl_path)
    p.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True, "path": str(p)})


@app.route("/api/open-file", methods=["POST"])
def api_open_file():
    data = request.get_json() or {}
    filepath = data.get("path", "")
    action = data.get("action", "reveal")  # "reveal" or "open"
    if not filepath:
        return jsonify({"error": "path required"}), 400
    p = Path(filepath)
    if not p.exists():
        return jsonify({"error": "File not found"}), 404
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", "")
    if dl_path:
        try:
            p.relative_to(dl_path)
        except ValueError:
            return jsonify({"error": "Access denied"}), 403
    try:
        if sys.platform == "win32":
            if action == "reveal":
                subprocess.Popen(["explorer", "/select,", str(p)])
            else:
                os.startfile(str(p))
        elif sys.platform == "darwin":
            if action == "reveal":
                subprocess.Popen(["open", "-R", str(p)])
            else:
                subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p.parent)])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


def _read_version():
    """Read version from VERSION file (single source of truth)."""
    for base in [os.path.dirname(os.path.abspath(__file__)), os.path.dirname(sys.executable)]:
        vf = os.path.join(base, "VERSION")
        if os.path.exists(vf):
            return open(vf).read().strip()
    # PyInstaller _internal fallback
    if getattr(sys, "frozen", False):
        vf = os.path.join(sys._MEIPASS, "VERSION")
        if os.path.exists(vf):
            return open(vf).read().strip()
    return "0.0.0"


APP_VERSION = _read_version()


@app.route("/api/version")
def api_version():
    return jsonify({"version": APP_VERSION})


@app.route("/api/check-update")
def api_check_update():
    """Check GitHub Releases for a newer version."""
    current = APP_VERSION
    try:
        r = requests.get(
            "https://api.github.com/repos/whyviidee/SONGERAPP/releases/latest",
            timeout=5,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        r.raise_for_status()
        data = r.json()
        latest = data.get("tag_name", "").lstrip("v")
        import platform as _plat
        _machine = _plat.machine().lower()  # "arm64" or "x86_64"
        _arch_tag = "arm64" if _machine == "arm64" else "x86_64"
        download_url = ""
        fallback_url = ""
        for asset in data.get("assets", []):
            name = asset["name"]
            if name.endswith(".dmg"):
                if _arch_tag in name:
                    download_url = asset["browser_download_url"]
                    break
                elif not fallback_url:
                    fallback_url = asset["browser_download_url"]
        if not download_url:
            download_url = fallback_url
        def _ver(v):
            try: return tuple(int(x) for x in v.split('.'))
            except: return (0,)
        has_update = latest and latest != current and _ver(latest) > _ver(current)
        app_bundle = _find_current_app_bundle() or ""
        translocated = "AppTranslocation" in app_bundle
        return jsonify({
            "current": current,
            "latest": latest,
            "has_update": has_update,
            "download_url": download_url,
            "arch": _arch_tag,
            "release_notes": data.get("body", ""),
            "translocated": translocated,
        })
    except Exception as e:
        return jsonify({"current": current, "latest": current, "has_update": False, "error": str(e)})


@app.route("/api/open-url", methods=["POST"])
def api_open_url():
    data = request.get_json() or {}
    url = data.get("url", "")
    if not url or not url.startswith("http"):
        return jsonify({"error": "valid URL required"}), 400
    webbrowser.open(url)
    return jsonify({"ok": True})


# ── Auto-update (macOS .dmg / Windows .exe) ──────────────────────────
_update_status = {"stage": "idle", "progress": 0, "error": ""}


@app.route("/api/auto-update", methods=["POST"])
def api_auto_update():
    """Download, install and relaunch — fully automatic."""
    data = request.get_json() or {}
    download_url = data.get("download_url", "")
    if not download_url or not download_url.startswith("http"):
        return jsonify({"error": "valid download_url required"}), 400

    def _run_update():
        import tempfile
        import shutil
        import platform

        _update_status.update(stage="downloading", progress=0, error="")
        try:
            # ── Download ──
            tmp_dir = tempfile.mkdtemp(prefix="songer_update_")
            filename = download_url.split("/")[-1]
            tmp_file = os.path.join(tmp_dir, filename)

            with requests.get(download_url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_file, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 256):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            _update_status["progress"] = int(downloaded / total * 100)

            _update_status.update(stage="installing", progress=100)

            if platform.system() == "Darwin" and filename.endswith(".dmg"):
                _install_mac(tmp_file, tmp_dir)
            elif platform.system() == "Windows" and filename.endswith(".exe"):
                _install_windows(tmp_file)
            else:
                _update_status.update(stage="error", error=f"Unsupported file: {filename}")
                return

            _update_status.update(stage="restarting", progress=100)
            time.sleep(1)
            _relaunch()

        except Exception as e:
            _update_status.update(stage="error", error=str(e))

    threading.Thread(target=_run_update, daemon=True).start()
    return jsonify({"ok": True})


def _install_mac(dmg_path, tmp_dir):
    """Mount .dmg, copy .app over current bundle, unmount."""
    import shutil

    # Find where current app is running from
    app_bundle = _find_current_app_bundle()
    if not app_bundle:
        raise RuntimeError("Cannot detect current .app bundle path")

    # Detect AppTranslocation — macOS runs apps from a read-only sandbox when
    # they haven't been moved to /Applications (e.g. run directly from DMG).
    if "AppTranslocation" in app_bundle:
        raise RuntimeError(
            "Move SONGER.app to your Applications folder first, then relaunch."
        )

    # Mount the dmg
    mount_point = os.path.join(tmp_dir, "mount")
    os.makedirs(mount_point, exist_ok=True)
    subprocess.run(
        ["hdiutil", "attach", dmg_path, "-mountpoint", mount_point, "-nobrowse", "-quiet"],
        check=True, timeout=60,
    )

    try:
        # Find .app inside mounted volume
        new_app = None
        for item in os.listdir(mount_point):
            if item.endswith(".app"):
                new_app = os.path.join(mount_point, item)
                break
        if not new_app:
            raise RuntimeError("No .app found in dmg")

        # Replace current app bundle
        parent = os.path.dirname(app_bundle)
        app_name = os.path.basename(app_bundle)
        backup = app_bundle + ".bak"
        dest = os.path.join(parent, app_name)

        # Move current → backup
        if os.path.exists(backup):
            shutil.rmtree(backup)
        os.rename(app_bundle, backup)
        try:
            # Use ditto (not shutil) — preserves codesign + notarization ticket
            subprocess.run(
                ["ditto", new_app, dest],
                check=True, timeout=120,
            )
        except Exception:
            # Rollback if copy fails
            if os.path.exists(backup):
                os.rename(backup, app_bundle)
            raise

        # Clean backup
        shutil.rmtree(backup, ignore_errors=True)

        # Remove quarantine xattr added by browser download
        subprocess.run(["xattr", "-cr", dest], timeout=30, check=False)
    finally:
        subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], timeout=30)


def _install_windows(exe_path):
    """Run the Windows installer silently."""
    subprocess.Popen([exe_path, "/SILENT", "/NORESTART"], creationflags=0x00000008)


def _find_current_app_bundle():
    """Detect the .app bundle path on macOS by walking up from the executable."""
    exe = sys.executable
    # PyInstaller frozen app: /path/to/SONGER.app/Contents/MacOS/SONGER
    parts = exe.split(os.sep)
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].endswith(".app"):
            return os.sep + os.path.join(*parts[:i + 1])
    # Fallback: check common location
    common = "/Applications/SONGER.app"
    if os.path.exists(common):
        return common
    return None


def _relaunch():
    """Relaunch the app after update."""
    import platform
    app_bundle = _find_current_app_bundle()
    if platform.system() == "Darwin" and app_bundle:
        subprocess.Popen(["open", "-n", app_bundle])
    elif platform.system() == "Windows":
        exe = sys.executable
        subprocess.Popen([exe] + sys.argv)
    os._exit(0)


@app.route("/api/update-status")
def api_update_status():
    return jsonify(_update_status)


@app.route("/api/delete-track", methods=["POST"])
def api_delete_track():
    data = request.get_json() or {}
    path = data.get("path", "")
    if not path:
        return jsonify({"error": "path required"}), 400

    p = Path(path)
    if not p.exists():
        return jsonify({"error": "file not found"}), 404

    # Security: only allow deleting from the download folder
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))
    try:
        p.relative_to(dl_path)
    except ValueError:
        return jsonify({"error": "not in download folder"}), 403

    try:
        p.unlink()
        # Clean up empty album folder
        album_dir = p.parent
        if album_dir.exists() and not any(album_dir.iterdir()):
            album_dir.rmdir()
            # Clean up empty artist folder
            artist_dir = album_dir.parent
            if artist_dir.exists() and not any(artist_dir.iterdir()):
                artist_dir.rmdir()

        # Remove from downloaded map
        m = _load_downloaded_map()
        to_remove = [k for k, v in m.items() if v == str(p)]
        for k in to_remove:
            del m[k]
        if to_remove:
            _DOWNLOADED_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(_DOWNLOADED_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(m, f, ensure_ascii=False)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"ok": True})


@app.route("/api/cover")
def api_cover():
    # Proxy external image URLs (Spotify CDN etc.)
    url = request.args.get("url", "")
    if url and url.startswith("http"):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            from flask import Response
            return Response(r.content, content_type=r.headers.get("Content-Type", "image/jpeg"))
        except Exception:
            return ("", 404)

    path = request.args.get("path", "")
    if not path:
        return ("", 404)
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ("", 404)
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", "")
    if dl_path:
        try:
            p.relative_to(dl_path)
        except ValueError:
            return ("", 403)
    try:
        from mutagen.flac import FLAC
        from mutagen.id3 import ID3
        from mutagen.mp4 import MP4
        from flask import Response
        ext = p.suffix.lower()
        img_data = mime = None
        if ext == ".flac":
            audio = FLAC(str(p))
            if audio.pictures:
                pic = audio.pictures[0]
                img_data, mime = pic.data, pic.mime
        elif ext == ".mp3":
            tags = ID3(str(p))
            for tag in tags.values():
                if hasattr(tag, "FrameID") and tag.FrameID == "APIC":
                    img_data, mime = tag.data, tag.mime
                    break
        elif ext in (".m4a", ".aac"):
            audio = MP4(str(p))
            if "covr" in audio:
                img_data = bytes(audio["covr"][0])
                mime = "image/jpeg"
        if not img_data:
            # Fallback: buscar no Spotify por artista+álbum
            artist = request.args.get("artist", "")
            album = request.args.get("album", "")
            if artist or album:
                try:
                    sp = _get_spotify()
                    results = sp.search(f"{artist} {album}".strip(), limit=1)
                    tracks = results.get("tracks", [])
                    if tracks:
                        cover_url = tracks[0].get("cover_url", "")
                        if cover_url:
                            r = requests.get(cover_url, timeout=5)
                            if r.ok:
                                img_data = r.content
                                mime = "image/jpeg"
                except Exception:
                    pass
        if not img_data:
            return ("", 404)
        return Response(img_data, mimetype=mime or "image/jpeg")
    except Exception:
        return ("", 404)


@app.route("/api/liked-songs")
def api_liked_songs():
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 500))
    if _get_music_service() == "tidal":
        try:
            tidal = _get_tidal()
            tidal.connect()
            all_tracks = tidal.get_liked_songs(limit=offset + limit)
            return jsonify(all_tracks[offset:offset + limit])
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    try:
        sp = _get_spotify()
        sp.connect()
        tracks = sp.get_liked_songs(limit=500)
        result = []
        for t in tracks:
            result.append({
                "id": t.get("id", ""),
                "name": t.get("title", t.get("name", "")),
                "artist": t.get("artist", ""),
                "artist_id": t.get("artist_id", ""),
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "preview_url": t.get("preview_url", ""),
                "uri": t.get("id", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _run_zip_job_tracks(job_id: str, tracks: list, name: str):
    """Generic zip job — takes a pre-built list of track dicts."""
    import tempfile
    import zipfile
    import re
    import shutil

    def safe_name(s):
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s).strip()[:80] or "download"

    j = _zip_jobs[job_id]
    try:
        j["status"] = "downloading"
        j["total"] = len(tracks)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading"})

        cfg = _load_config()
        fmt = cfg.get("download", {}).get("format", "mp3_320")
        safe_n = safe_name(name)
        tmp_dir = Path(tempfile.mkdtemp(prefix="songer_zip_"))

        from core.youtube import YouTubeClient
        yt = YouTubeClient()

        downloaded = []
        from core.metadata import embed_metadata
        for i, track in enumerate(tracks):
            t = {
                "id": track.get("id", ""),
                "title": track.get("title") or track.get("name", "Unknown"),
                "artist": track.get("artist", ""),
                "album": track.get("album", ""),
                "cover_url": track.get("cover_url") or track.get("cover", ""),
                "genre": track.get("genre", ""),
                "track_number": i + 1,
            }
            try:
                path = yt.download(t, tmp_dir, fmt)
                if path and path.exists():
                    try:
                        embed_metadata(path, t)
                    except Exception:
                        pass
                    downloaded.append(path)
            except Exception:
                pass
            j["done"] = i + 1
            j["progress"] = int((i + 1) / len(tracks) * 85)
            _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading", "name": name, "progress": j["progress"], "done": j["done"], "total": j["total"]})

        zip_path = tmp_dir.parent / f"{safe_n}.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in downloaded:
                zf.write(str(f), arcname=f"{safe_n}/{f.name}")

        shutil.rmtree(str(tmp_dir), ignore_errors=True)

        j["status"] = "done"
        j["progress"] = 100
        j["zip_path"] = str(zip_path)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "done", "progress": 100})

    except Exception as e:
        j["status"] = "error"
        j["error"] = str(e)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "error", "error": str(e)})


@app.route("/api/zip/tracks", methods=["POST"])
def api_zip_tracks():
    data = request.get_json() or {}
    tracks = data.get("tracks", [])
    name = data.get("name", "download")
    if not tracks:
        return jsonify({"error": "tracks required"}), 400
    job_id = str(uuid.uuid4())
    _zip_jobs[job_id] = {
        "id": job_id, "status": "pending", "progress": 0,
        "total": len(tracks), "done": 0, "zip_path": "", "error": "", "name": name,
    }
    threading.Thread(target=_run_zip_job_tracks, args=(job_id, tracks, name), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/playlists/<playlist_id>/zip", methods=["POST"])
def api_playlist_zip(playlist_id):
    data = request.get_json() or {}
    playlist_name = data.get("name", "playlist")
    job_id = str(uuid.uuid4())
    _zip_jobs[job_id] = {
        "id": job_id,
        "status": "pending",
        "progress": 0,
        "total": 0,
        "done": 0,
        "zip_path": "",
        "error": "",
        "name": playlist_name,
    }
    threading.Thread(target=_run_zip_job, args=(job_id, playlist_id, playlist_name), daemon=True).start()
    return jsonify({"job_id": job_id})


def _run_zip_job(job_id: str, playlist_id: str, playlist_name: str):
    import tempfile
    import zipfile
    import re
    import shutil

    def safe_name(s):
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", s).strip()[:80] or "playlist"

    j = _zip_jobs[job_id]
    try:
        j["status"] = "downloading"
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading", "name": playlist_name, "total": 0, "done": 0, "progress": 0})

        if _get_music_service() == "tidal":
            tidal = _get_tidal()
            tidal.connect()
            tracks, _ = tidal._playlist_tracks(playlist_id)
        else:
            sp = _get_spotify()
            sp.connect()
            tracks, _ = sp._playlist_tracks(playlist_id)
        j["total"] = len(tracks)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading", "name": playlist_name, "total": len(tracks), "done": 0, "progress": 0})

        cfg = _load_config()
        fmt = cfg.get("download", {}).get("format", "mp3_320")

        safe_pl = safe_name(playlist_name)
        tmp_dir = Path(tempfile.mkdtemp(prefix="songer_zip_"))

        from core.youtube import YouTubeClient
        yt = YouTubeClient()

        downloaded = []
        for i, track in enumerate(tracks):
            t = {
                "id": track.get("id", ""),
                "title": track.get("title", track.get("name", "Unknown")),
                "artist": track.get("artist", ""),
                "album": track.get("album", ""),
                "cover_url": track.get("cover_url", ""),
                "track_number": i + 1,
            }
            try:
                path = yt.download(t, tmp_dir, fmt)
                if path and path.exists():
                    downloaded.append(path)
            except Exception:
                pass
            j["done"] = i + 1
            j["progress"] = int((i + 1) / len(tracks) * 85)
            _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading", "name": playlist_name, "progress": j["progress"], "done": j["done"], "total": j["total"]})

        # Save ZIP to configured download folder
        cfg = _load_config()
        dl_path = Path(cfg.get("download", {}).get("path", "") or str(Path.home() / "Music" / "SONGER"))
        dl_path.mkdir(parents=True, exist_ok=True)
        zip_path = dl_path / f"{safe_pl}.zip"

        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in downloaded:
                zf.write(str(f), arcname=f.name)

        shutil.rmtree(str(tmp_dir), ignore_errors=True)

        j["status"] = "done"
        j["progress"] = 100
        j["zip_path"] = str(zip_path)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "done", "name": playlist_name, "progress": 100, "total": j["total"], "done": j["done"], "path": str(zip_path)})

    except Exception as e:
        j["status"] = "error"
        j["error"] = str(e)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "error", "error": str(e)})


@app.route("/api/zip-jobs")
def api_zip_jobs():
    return jsonify(list(_zip_jobs.values()))


@app.route("/api/zip/<job_id>/extract", methods=["POST"])
def api_zip_extract(job_id):
    """Extract ZIP to download folder and delete the ZIP file."""
    job = _zip_jobs.get(job_id)
    zip_path = None
    if job and job.get("zip_path"):
        zip_path = Path(job["zip_path"])
    else:
        # Try from request body
        data = request.get_json() or {}
        if data.get("path"):
            zip_path = Path(data["path"])

    if not zip_path or not zip_path.exists():
        return jsonify({"error": "ZIP not found"}), 404

    cfg = _load_config()
    dl_path = Path(cfg.get("download", {}).get("path", "") or str(Path.home() / "Music" / "SONGER"))

    try:
        import zipfile
        audio_exts = {'.mp3', '.flac', '.m4a', '.ogg', '.opus', '.wav', '.aac', '.wma'}
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            zf.extractall(str(dl_path))
            extracted = zf.namelist()

        # Register extracted audio files in downloaded_map
        registered = 0
        for name in extracted:
            file_path = dl_path / name
            if file_path.exists() and file_path.suffix.lower() in audio_exts:
                # Use filename without extension as a pseudo track ID
                _save_downloaded_entry(f"zip_{file_path.stem}", str(file_path))
                registered += 1

        # Add to download history
        playlist_name = job.get("name", "Playlist") if job else zip_path.stem
        try:
            DownloadHistory().add(
                url="",
                name=f"{playlist_name} (ZIP)",
                tracks_count=registered,
                done_count=registered,
                fail_count=0,
                fmt="zip",
                cover="",
            )
        except Exception:
            pass

        # Delete the ZIP
        zip_path.unlink()

        # Remove from zip jobs
        if job_id in _zip_jobs:
            del _zip_jobs[job_id]

        return jsonify({"ok": True, "extracted": registered, "path": str(dl_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/zip/<job_id>/status")
def api_zip_status(job_id):
    job = _zip_jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    return jsonify(job)


@app.route("/api/zip/<job_id>")
def api_zip_download(job_id):
    job = _zip_jobs.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404
    if job["status"] != "done":
        return jsonify({"error": "not ready"}), 400
    zip_path = Path(job["zip_path"])
    if not zip_path.exists():
        return jsonify({"error": "file not found"}), 404
    return send_file(str(zip_path), as_attachment=True, download_name=zip_path.name)


@app.route("/api/stream")
@app.route("/stream/<path:filepath>")
def stream_file(filepath=None):
    # Support both query param and path param
    if filepath is None:
        filepath = request.args.get("path", "")
    decoded = urllib.parse.unquote(filepath)
    p = Path(decoded)
    if not p.exists() or not p.is_file():
        return jsonify({"error": "File not found"}), 404
    # Only serve files from the configured download path
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", "") or str(Path.home() / "Music" / "SONGER")
    try:
        p.relative_to(dl_path)
    except ValueError:
        return jsonify({"error": "Access denied"}), 403

    # Support range requests for seek
    file_size = p.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        # Parse range header: "bytes=start-end"
        import re as _re_stream
        m = _re_stream.match(r"bytes=(\d+)-(\d*)", range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            end = min(end, file_size - 1)
            length = end - start + 1

            with open(str(p), "rb") as f:
                f.seek(start)
                data = f.read(length)

            from flask import Response
            resp = Response(data, status=206, mimetype="audio/mpeg")
            resp.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            resp.headers["Accept-Ranges"] = "bytes"
            resp.headers["Content-Length"] = str(length)
            return resp

    # Full file response with Accept-Ranges
    resp = send_file(str(p))
    resp.headers["Accept-Ranges"] = "bytes"
    return resp


# ------------------------------------------------------------------
# Trending Tracks (hidden feature)
# ------------------------------------------------------------------

_TRENDING_DIR = Path(__file__).parent / "tools" / "trending"

_TRENDING_LABELS = {
    "portugal-top50":        "🇵🇹 Portugal Top 50",
    "funk-brasil":           "🇧🇷 Funk Brasil",
    "reggaeton":             "🎤 Reggaeton",
    "house":                 "🎛️ House Music",
    "amapiano":              "🥁 Amapiano",
    "afro-house-electronic": "⚡ Afro House — Electrónico",
    "afro-house-african":    "🌍 Afro House — Africano",
    "underground-remixes":   "🔊 Underground Remixes",
}

import re as _re

def _parse_trending_md(path: Path) -> list:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []
    pattern = _re.compile(
        r'^- (.+?) — (.+?)\s*\n\s*\[(Spotify|SoundCloud)\]\((https?://[^\)]+)\)',
        _re.MULTILINE,
    )
    tracks = []
    for m in pattern.finditer(text):
        tracks.append({
            "artist": m.group(1).strip(),
            "title":  m.group(2).strip(),
            "source": m.group(3),
            "url":    m.group(4).strip(),
        })
    return tracks


@app.route("/api/trending")
def api_trending():
    categories = []
    for key, label in _TRENDING_LABELS.items():
        md_path = _TRENDING_DIR / f"{key}.md"
        if md_path.exists():
            tracks = _parse_trending_md(md_path)
            categories.append({"key": key, "label": label, "tracks": tracks})
    return jsonify(categories)


@app.route("/api/trending/<key>/refresh", methods=["POST"])
def api_trending_refresh(key):
    if key not in _TRENDING_LABELS:
        return jsonify({"error": "unknown key"}), 404
    import subprocess
    fetch_script = Path(__file__).parent / "tools" / "trending" / "fetch.py"
    # Find Python: venv first, then system
    python_exe = Path(__file__).parent / "venv" / "bin" / "python"
    if not python_exe.exists():
        python_exe = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    if not python_exe.exists():
        python_exe = Path(sys.executable)
    try:
        result = subprocess.run(
            [str(python_exe), str(fetch_script), "--key", key],
            capture_output=True, text=True, timeout=120,
            cwd=str(Path(__file__).parent),
        )
        if result.returncode != 0:
            return jsonify({"error": result.stderr or "Script falhou"}), 500
        tracks = _parse_trending_md(_TRENDING_DIR / f"{key}.md")
        return jsonify({"ok": True, "tracks": tracks, "count": len(tracks)})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout (>120s)"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def _open_browser():
    time.sleep(0.8)
    url = "http://127.0.0.1:8888/app" if TOKEN_PATH.exists() else "http://127.0.0.1:8888"
    webbrowser.open(url)


if __name__ == "__main__":
    print("=" * 45)
    print("  SONGER Setup — http://localhost:8888")
    print("=" * 45)
    print("A abrir browser...")
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=8888, debug=False)
