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
SCOPES = "user-library-read playlist-read-private playlist-read-collaborative"
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

    return redirect("/app")


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


@app.route("/app")
def app_shell():
    if not TOKEN_PATH.exists():
        return redirect("/?error=no_token")
    return render_template("app.html")


@app.route("/api/status")
def api_status():
    cfg = _load_config()
    has_spotify = TOKEN_PATH.exists() and bool(cfg.get("spotify", {}).get("client_id"))

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
        "spotify": "ok" if has_spotify else "error",
        "soulseek": "ok" if slsk_ok else "error",
    })


@app.route("/api/stats")
def api_stats():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))

    try:
        files = scan_library(dl_path)
    except Exception:
        files = []

    total_mb = sum(f.get("size_mb", 0) for f in files)

    history = DownloadHistory()
    playlists_count = len(set(
        e.get("url", "") for e in history.get_all()
        if "playlist" in e.get("url", "")
    ))

    active = len([t for t in _download_queue.values() if t.get("status") == "downloading"]) if "_download_queue" in globals() else 0

    return jsonify({
        "tracks": len(files),
        "downloading": active,
        "playlists": playlists_count,
        "storage_gb": round(total_mb / 1024, 1),
    })


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
                    "album": t.get("album", ""),
                    "cover": t.get("cover_url", ""),
                    "duration_ms": t.get("duration_ms", 0),
                    "uri": "",
                    "external_url": "",
                })
        else:
            results = sp.search(q, limit=30)
            tracks = []
            for t in results.get("tracks", []):
                tracks.append({
                    "id": t.get("id", ""),
                    "name": t.get("title", ""),
                    "artist": t.get("artist", ""),
                    "album": t.get("album", ""),
                    "cover": t.get("cover_url", ""),
                    "duration_ms": t.get("duration_ms", 0),
                    "uri": "",
                    "external_url": "",
                })
        return jsonify(tracks)
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

@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.get_json() or {}
    track_id = data.get("id") or data.get("uri", "")
    if not track_id:
        return jsonify({"error": "id required"}), 400

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "track_id": track_id,
        "name": data.get("name", "Unknown"),
        "artist": data.get("artist", ""),
        "album": data.get("album", ""),
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
            "title": track.get("name", "Unknown"),
            "artist": track.get("artist", ""),
            "album": track.get("album", ""),
            "cover_url": track.get("cover", ""),
            "uri": track.get("uri", ""),
        }

        cfg = _load_config()
        fmt = cfg.get("download", {}).get("format", "mp3")
        source = cfg.get("download", {}).get("source", "youtube")

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


@app.route("/api/playlists/<playlist_id>/tracks")
def api_playlist_tracks(playlist_id):
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
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "uri": t.get("id", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/library")
def api_library():
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", str(Path.home() / "Music" / "SONGER"))
    try:
        files = scan_library(dl_path)
        return jsonify(files)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history")
def api_history():
    h = DownloadHistory()
    return jsonify(h.get_all())


@app.route("/api/history", methods=["DELETE"])
def api_history_clear():
    h = DownloadHistory()
    h.clear()
    return jsonify({"ok": True})


@app.route("/api/browse-folder")
def api_browse_folder():
    """Abre folder picker nativo e devolve o path escolhido."""
    try:
        if sys.platform == "win32":
            ps = (
                'Add-Type -AssemblyName System.Windows.Forms;'
                '$f=New-Object System.Windows.Forms.Form;'
                '$f.TopMost=$true;'
                '$d=New-Object System.Windows.Forms.FolderBrowserDialog;'
                '$d.Description="Escolhe pasta de downloads";'
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


@app.route("/api/cover")
def api_cover():
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
                "album": t.get("album", ""),
                "cover": t.get("cover_url", ""),
                "duration_ms": t.get("duration_ms", 0),
                "uri": t.get("id", ""),
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "downloading"})

        sp = _get_spotify()
        sp.connect()
        tracks, _ = sp._playlist_tracks(playlist_id)
        j["total"] = len(tracks)

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
            _sse_push({"type": "zip_update", "job_id": job_id, "progress": j["progress"], "done": j["done"], "total": j["total"]})

        zip_path = tmp_dir.parent / f"{safe_pl}.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in downloaded:
                zf.write(str(f), arcname=f"{safe_pl}/{f.name}")

        shutil.rmtree(str(tmp_dir), ignore_errors=True)

        j["status"] = "done"
        j["progress"] = 100
        j["zip_path"] = str(zip_path)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "done", "progress": 100})

    except Exception as e:
        j["status"] = "error"
        j["error"] = str(e)
        _sse_push({"type": "zip_update", "job_id": job_id, "status": "error", "error": str(e)})


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


@app.route("/stream/<path:filepath>")
def stream_file(filepath):
    # filepath is URL-encoded absolute path
    decoded = urllib.parse.unquote(filepath)
    p = Path(decoded)
    if not p.exists() or not p.is_file():
        return jsonify({"error": "File not found"}), 404
    # Only serve files from the configured download path
    cfg = _load_config()
    dl_path = cfg.get("download", {}).get("path", "")
    try:
        p.relative_to(dl_path)
    except ValueError:
        return jsonify({"error": "Access denied"}), 403
    return send_file(str(p))


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
