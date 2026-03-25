# SONGER

Desktop app to download music from Spotify & Tidal via YouTube. Native macOS & Windows.

## Features

| Feature | Description |
|---|---|
| **Search** | Search tracks, albums & artists via Spotify or Tidal |
| **Playlists** | Browse and download full playlists (individual or ZIP) |
| **Downloads** | Real-time download queue with SSE progress |
| **My Music** | Local library of downloaded tracks |
| **Trending** | Top 50 charts by country |
| **Player** | Built-in audio player with seek, cover art |
| **Auto-Update** | One-click updates via GitHub Releases |

## Install (macOS)

1. Download the latest `.dmg` from [Releases](https://github.com/whyviidee/SONGERAPP/releases/latest)
2. Open the `.dmg` and drag **SONGER** to Applications
3. Open SONGER — on first run, configure your Spotify or Tidal credentials in Settings

## Install (Windows)

1. Download the latest `.exe` from [Releases](https://github.com/whyviidee/SONGERAPP/releases/latest)
2. Run the installer
3. Open SONGER and configure credentials in Settings

## Spotify Setup

SONGER requires your own Spotify Developer credentials:

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard)
2. Create an app — add redirect URI `http://127.0.0.1:8888/callback`
3. Go to **User Management** and add your Spotify email
4. Copy **Client ID** and **Client Secret** into SONGER Settings
5. Click connect and authorize

## Tidal Setup

In Settings, switch to Tidal and click Login. Authorize in the browser window that opens.

## Download Sources

| Source | Quality | Requirements |
|---|---|---|
| **YouTube** | Up to 320kbps MP3 | Internet only |
| **Soulseek** | FLAC lossless | Soulseek account + slskd |
| **Hybrid** | Soulseek first, YouTube fallback | Both |

## Tech Stack

- **Frontend:** React 19 + Vite 6 + Framer Motion
- **Backend:** Python Flask
- **Desktop:** PyWebView (macOS), PyQt6 (Windows)
- **Music APIs:** Spotify (spotipy), Tidal (tidalapi)
- **Download:** yt-dlp + imageio-ffmpeg

## Config Files

All stored locally in `~/.songer/`:

| File | Content |
|---|---|
| `config.json` | Settings (download path, format, credentials) |
| `.spotify_token.json` | Spotify OAuth token (auto-renewed) |
| `history.json` | Download history |
| `songer.log` | Application logs |

## Development

```bash
# Frontend
cd frontend && npm install && npm run dev

# Backend
pip install -r requirements.txt
python server.py

# Build macOS
./build_mac.sh

# Release (bump + build + DMG + GitHub Release)
./release.sh patch   # or minor / major
```

## Legal

SONGER is an open-source personal tool. Users are solely responsible for compliance with copyright laws in their jurisdiction.
