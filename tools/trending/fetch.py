"""
Trending Tracks Fetcher
Vai buscar tracks trending por género e guarda em .md nesta pasta.
Fontes: Spotify (charts + playlists) + SoundCloud (underground remixes)

Credenciais lidas de ~/.songer/config.json (mesmo ficheiro do SONGER).
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

import sys
import requests
import spotipy
sys.stdout.reconfigure(encoding='utf-8')
from spotipy.oauth2 import SpotifyClientCredentials

# ── Config ──────────────────────────────────────────────────────────────────
CONFIG_PATH = Path.home() / ".songer" / "config.json"
OUTPUT_DIR = Path(__file__).parent

def load_spotify_creds():
    data = json.loads(CONFIG_PATH.read_text())
    sp = data["spotify"]
    return sp["client_id"], sp["client_secret"]

def get_spotify():
    client_id, client_secret = load_spotify_creds()
    return spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    ))

# ── Helpers ──────────────────────────────────────────────────────────────────
def safe_name(name):
    return re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '-').lower()

def track_line(track):
    artists = ", ".join(a["name"] for a in track["artists"])
    name = track["name"]
    url = track["external_urls"].get("spotify", "")
    return f"- {artists} — {name}  \n  [Spotify]({url})"

def write_md(filename, title, sections):
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"# {title}", f"*Atualizado: {today}*", ""]
    for section_title, tracks in sections:
        lines.append(f"## {section_title}")
        lines.extend(tracks)
        lines.append("")
    path = OUTPUT_DIR / filename
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✓ {filename}")

# ── Spotify: Genre playlists ─────────────────────────────────────────────────
GENRE_PLAYLISTS = {
    "portugal": "0ricqsTobzaG4tjzdogu1B",           # MEGA HITS FM 2026 Portugal Top 50
    "funk-brasil": "0gMdDTXoAiqt6mc4XwTNnX",        # FUNK BRASILEIRO 2026 Maiores Hits
    "reggaeton": "659ULOqOfJqmX7bXYsIVAr",          # REGGETON 2026 Mix
    "house": "7bu7BZEusLNJSaAuUUZBKn",              # HOUSE MUSIC 2026 Top 100
    "amapiano": "4Ymf8eaPQGT7HMTymoX82f",           # AMAPIANO 2026 SA
}

def fetch_genre_playlist(sp, playlist_id, limit=25):
    results = sp.playlist_tracks(playlist_id, limit=limit)
    tracks = [item["track"] for item in results["items"] if item["track"]]
    return [track_line(t) for t in tracks]

# ── SoundCloud: Underground remixes ──────────────────────────────────────────
SC_BASE = "https://api-v2.soundcloud.com"

def get_sc_client_id():
    """Pega o client_id do SoundCloud da página principal (muda ocasionalmente)"""
    try:
        r = requests.get("https://soundcloud.com", timeout=10,
                         headers={"User-Agent": "Mozilla/5.0"})
        scripts = re.findall(r'src="(https://a-v2\.sndcdn\.com/assets/[^"]+\.js)"', r.text)
        for script_url in scripts[-3:]:
            sr = requests.get(script_url, timeout=10)
            match = re.search(r'client_id:"([a-zA-Z0-9]+)"', sr.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return "iZIs9mchVcX5lhVRyQGGAYlNPVldzAoX"

def sc_search(client_id, query, limit=15):
    try:
        r = requests.get(
            f"{SC_BASE}/search/tracks",
            params={
                "q": query,
                "limit": limit,
                "filter.duration.from": 120000,
                "client_id": client_id,
            },
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        lines = []
        for track in data.get("collection", []):
            artist = track.get("user", {}).get("username", "?")
            title = track.get("title", "?")
            url = track.get("permalink_url", "")
            lines.append(f"- {artist} — {title}  \n  [SoundCloud]({url})")
        return lines
    except Exception as e:
        return [f"- *erro: {e}*"]

SC_QUERIES = {
    "afro-house-electronic": [
        "afro house hugel",
        "afro house black coffee",
        "kinemusic afro house",
    ],
    "afro-house-african": [
        "afro house tribal 2024",
        "afro house south africa 2024",
        "deep afro house",
    ],
    "underground-remixes": [
        "kybba remix 2024",
        "dave nunes remix",
        "klap remix",
        "karyo remix",
        "ajay remix",
        "ovano remix",
        "onderkoffer remix",
    ],
}

def fetch_soundcloud(client_id, queries, limit_per_query=8):
    lines = []
    seen = set()
    for q in queries:
        results = sc_search(client_id, q, limit=limit_per_query)
        for line in results:
            key = line[:60]
            if key not in seen:
                seen.add(key)
                lines.append(line)
        time.sleep(0.5)
    return lines[:30]

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("A buscar credenciais Spotify...")
    sp = get_spotify()

    print("A obter client_id SoundCloud...")
    sc_id = get_sc_client_id()

    print("\n[1/8] Portugal Top 50")
    pt_tracks = fetch_genre_playlist(sp, GENRE_PLAYLISTS["portugal"], limit=30)
    write_md("portugal-top50.md", "Portugal — Top 50", [("Top 50", pt_tracks)])

    print("[2/8] Funk Brasil")
    funk_tracks = fetch_genre_playlist(sp, GENRE_PLAYLISTS["funk-brasil"])
    write_md("funk-brasil.md", "Funk Brasil — Trending", [("Trending", funk_tracks)])

    print("[3/8] Reggaeton")
    reg_tracks = fetch_genre_playlist(sp, GENRE_PLAYLISTS["reggaeton"])
    write_md("reggaeton.md", "Reggaeton — Trending", [("Trending", reg_tracks)])

    print("[4/8] House Music")
    house_tracks = fetch_genre_playlist(sp, GENRE_PLAYLISTS["house"])
    write_md("house.md", "House Music — Trending", [("Trending", house_tracks)])

    print("[5/8] Amapiano")
    amapiano_tracks = fetch_genre_playlist(sp, GENRE_PLAYLISTS["amapiano"])
    write_md("amapiano.md", "Amapiano — Trending", [("Trending", amapiano_tracks)])

    print("[6/8] Afro House (electrónico)")
    afro_el_tracks = fetch_soundcloud(sc_id, SC_QUERIES["afro-house-electronic"])
    write_md("afro-house-electronic.md", "Afro House — Estilo Electrónico (Hugel, Black Coffee, Kinemusic)", [("SoundCloud", afro_el_tracks)])

    print("[7/8] Afro House (africano)")
    afro_af_tracks = fetch_soundcloud(sc_id, SC_QUERIES["afro-house-african"])
    write_md("afro-house-african.md", "Afro House — Estilo Africano", [("SoundCloud", afro_af_tracks)])

    print("[8/8] Underground Remixes (SoundCloud)")
    remix_tracks = fetch_soundcloud(sc_id, SC_QUERIES["underground-remixes"], limit_per_query=6)
    write_md("underground-remixes.md", "Underground Remixes — SoundCloud (Kybba, Dave Nunes, Klap, Karyo...)", [("SoundCloud", remix_tracks)])

    print("\n✓ Tudo atualizado em tools/trending/")

_KEY_MAP = {
    "portugal-top50":        lambda sp, sc: (fetch_genre_playlist(sp, GENRE_PLAYLISTS["portugal"], limit=30),  "portugal-top50.md",        "Portugal — Top 50",                                                    "Top 50"),
    "funk-brasil":           lambda sp, sc: (fetch_genre_playlist(sp, GENRE_PLAYLISTS["funk-brasil"]),         "funk-brasil.md",           "Funk Brasil — Trending",                                               "Trending"),
    "reggaeton":             lambda sp, sc: (fetch_genre_playlist(sp, GENRE_PLAYLISTS["reggaeton"]),           "reggaeton.md",             "Reggaeton — Trending",                                                 "Trending"),
    "house":                 lambda sp, sc: (fetch_genre_playlist(sp, GENRE_PLAYLISTS["house"]),               "house.md",                 "House Music — Trending",                                               "Trending"),
    "amapiano":              lambda sp, sc: (fetch_genre_playlist(sp, GENRE_PLAYLISTS["amapiano"]),            "amapiano.md",              "Amapiano — Trending",                                                  "Trending"),
    "afro-house-electronic": lambda sp, sc: (fetch_soundcloud(sc, SC_QUERIES["afro-house-electronic"]),       "afro-house-electronic.md", "Afro House — Estilo Electrónico (Hugel, Black Coffee, Kinemusic)",     "SoundCloud"),
    "afro-house-african":    lambda sp, sc: (fetch_soundcloud(sc, SC_QUERIES["afro-house-african"]),          "afro-house-african.md",    "Afro House — Estilo Africano",                                         "SoundCloud"),
    "underground-remixes":   lambda sp, sc: (fetch_soundcloud(sc, SC_QUERIES["underground-remixes"], limit_per_query=6), "underground-remixes.md", "Underground Remixes — SoundCloud (Kybba, Dave Nunes, Klap, Karyo...)", "SoundCloud"),
}


def refresh_key(key: str):
    """Refresh a single category by key. Used by server --key mode."""
    if key not in _KEY_MAP:
        print(f"✗ Chave desconhecida: {key}", flush=True)
        return
    sp = get_spotify()
    sc_id = get_sc_client_id()
    tracks, filename, title, section = _KEY_MAP[key](sp, sc_id)
    write_md(filename, title, [(section, tracks)])
    print(f"✓ {filename}", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", help="Refresh only one category by key")
    args = parser.parse_args()
    if args.key:
        refresh_key(args.key)
    else:
        main()
