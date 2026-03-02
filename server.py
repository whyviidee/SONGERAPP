# -*- coding: utf-8 -*-
"""
SONGER Setup Server - localhost:8888
Configura credenciais Spotify e faz OAuth sem copiar/colar URLs.

Uso:
    pip install flask
    python server.py
"""

import json
import time
import webbrowser
import threading
from pathlib import Path
from urllib.parse import urlencode

import requests
from flask import Flask, request, redirect, render_template, jsonify

app = Flask(__name__, template_folder="web")
app.secret_key = "songer-setup-key"

REDIRECT_URI = "http://localhost:8888/callback"
SCOPES = "user-library-read playlist-read-private playlist-read-collaborative"
CONFIG_PATH = Path.home() / ".songer" / "config.json"
TOKEN_PATH = Path.home() / ".songer" / ".spotify_token.json"

# Guarda temporariamente client_id/secret durante o fluxo OAuth
_session = {}


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

    return render_template("success.html")


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


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def _open_browser():
    time.sleep(0.8)
    webbrowser.open("http://localhost:8888")


if __name__ == "__main__":
    print("=" * 45)
    print("  SONGER Setup — http://localhost:8888")
    print("=" * 45)
    print("A abrir browser...")
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=8888, debug=False)
