#!/usr/bin/env python3
"""SONGER — Single entry point for macOS app.
Starts Flask backend + opens PyWebView native window.
"""
import threading
import sys
import os
import json
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

_CONFIG_PATH = Path.home() / ".songer" / "config.json"


def _ensure_config():
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = {}
    if _CONFIG_PATH.exists():
        try:
            cfg = json.loads(_CONFIG_PATH.read_text())
        except Exception:
            pass
    spotify = cfg.setdefault("spotify", {})
    if not spotify.get("redirect_uri"):
        spotify["redirect_uri"] = "http://127.0.0.1:8888/callback"
        _CONFIG_PATH.write_text(json.dumps(cfg, indent=2))


_ensure_config()


def start_flask():
    from server import app
    app.run(host='127.0.0.1', port=8888, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    import time
    time.sleep(1)

    try:
        import webview
        window = webview.create_window(
            'SONGER',
            'http://127.0.0.1:8888/app',
            width=1100,
            height=750,
            min_size=(900, 600),
            background_color='#0a0a0f',
            frameless=False,
        )
        webview.start()
    except ImportError:
        import webbrowser
        webbrowser.open('http://127.0.0.1:8888/app')
        print('SONGER running at http://127.0.0.1:8888/app')
        print('Press Ctrl+C to quit')
        try:
            flask_thread.join()
        except KeyboardInterrupt:
            pass
