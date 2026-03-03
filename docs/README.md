# SONGER

Music download manager powered by Spotify, YouTube and Soulseek. Search any song, album or artist on Spotify, download it in high quality, and manage your local music library — all from a web browser.

## What it does

1. You search for music using Spotify's catalog (text search or paste a Spotify URL)
2. SONGER finds and downloads the audio from YouTube or Soulseek
3. Metadata (artist, album, cover art, track number, genre, year) is embedded automatically
4. Files are organized in `Artist/Album/Title.mp3` structure

## Stack

| Component | Tech |
|-----------|------|
| Backend | Python 3.11 + Flask |
| Frontend | Vanilla JS + Lucide Icons |
| Music API | Spotify (Spotipy, OAuth2) |
| YouTube DL | yt-dlp |
| Soulseek | slskd REST API |
| Metadata | Mutagen (ID3v2, FLAC tags) |
| FFmpeg | imageio-ffmpeg (bundled) |
| Desktop UI | PyQt6 (legacy, still works) |

## Requirements

- **Python 3.11+**
- **Spotify Developer Account** (free) — for API credentials
- **FFmpeg** — bundled automatically via imageio-ffmpeg, or install manually
- **slskd** (optional) — self-hosted Soulseek client, only needed if you want Soulseek downloads

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/whyviidee/SONGERAPP.git
cd SONGERAPP

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create App**
3. Fill in:
   - App name: `SONGER` (or anything you want)
   - Redirect URI: `http://localhost:5000/callback`
   - Check **Web API**
4. Save and copy your **Client ID** and **Client Secret**

> **Important**: The redirect URI must be exactly `http://localhost:5000/callback`

### 3. Run the app

```bash
python server.py
```

Open your browser at `http://localhost:5000`

### 4. First-time setup

1. You'll see the setup page — paste your Spotify **Client ID** and **Client Secret**
2. Click **Connect to Spotify** — a Spotify login page will open
3. After authorizing, you'll be redirected to the app
4. An onboarding modal will ask you to choose:
   - **Download folder** (default: `~/Music/SONGER`)
   - **Audio format** (FLAC, MP3 320/256/128)
   - **Download source** (YouTube, Soulseek, or Hybrid)
5. You're ready to go!

## Configuration

All config is stored in `~/.songer/config.json`:

```json
{
  "spotify": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret"
  },
  "download": {
    "path": "C:\\Users\\you\\Music\\SONGER",
    "format": "mp3_320",
    "source": "hybrid",
    "organize": true
  },
  "soulseek": {
    "enabled": false,
    "slskd_url": "http://localhost:5030",
    "slskd_api_key": ""
  }
}
```

### Download formats

| Format | Quality | Needs FFmpeg |
|--------|---------|-------------|
| `flac` | Lossless | Yes |
| `mp3_320` | 320 kbps | Yes |
| `mp3_256` | 256 kbps | Yes |
| `mp3_128` | 128 kbps | Yes |

> If FFmpeg is not available, downloads fall back to raw audio (usually m4a/webm).

### Download sources

| Source | How it works |
|--------|-------------|
| `youtube` | Searches YouTube for `{artist} - {title}`, downloads best audio |
| `soulseek` | Searches Soulseek P2P via slskd, scores results by quality/match |
| `hybrid` | Tries Soulseek first, falls back to YouTube if no good match found |

### Soulseek setup (optional)

Soulseek downloads require [slskd](https://github.com/slskd/slskd) running locally:

1. Install and run slskd (Docker or standalone)
2. Set API key in slskd config
3. In SONGER Settings, enable Soulseek and fill in:
   - **slskd URL**: `http://localhost:5030` (default)
   - **slskd API Key**: your key from slskd config
4. Set download source to `soulseek` or `hybrid`

## Features

### Search & Discovery
- Text search across Spotify's entire catalog
- Paste any Spotify URL (track, album, playlist, artist)
- Browse artist pages with top tracks and full discography
- Album detail pages with full tracklists
- Paginated search results with "See all" for each category
- Personalized recommendations based on your liked songs

### Download & Library
- Download individual tracks or entire albums/playlists
- Batch download with concurrent workers (configurable)
- Automatic duplicate detection (skips existing files)
- Real-time download queue with progress tracking
- Cancel individual downloads or clear entire queue
- Library browser with sort by: Recently Added, Artist, Year, Genre
- Filter library by artist or track name

### Player
- Built-in web audio player for local files
- 30-second Spotify preview for any track (before downloading)
- Playlist queue with shuffle, next, previous, repeat
- Double-click any downloaded track to play it
- Now Playing modal showing current queue

### UI/UX
- Dark theme inspired by Spotify
- Clickable artist names across all views
- Download badge counter on sidebar
- Custom confirmation modals (no browser popups)
- Responsive soundwave loading animations
- "In Your Library" section on artist pages
- Recently downloaded tracks playable from home

### Settings
- Change download path with folder picker (Music, Downloads, Desktop)
- Switch audio format and download source anytime
- Reset download database (clears tracking without deleting files)
- Disconnect Spotify account
- Legacy path support when changing download folders

## File Structure

```
SONGER/
├── server.py              # Flask web server (main entry point)
├── main.py                # PyQt6 desktop app (legacy)
├── requirements.txt       # Python dependencies
│
├── core/                  # Business logic (no UI dependency)
│   ├── config.py          # ~/.songer/config.json read/write
│   ├── spotify.py         # Spotify API client (OAuth2, search, playlists)
│   ├── youtube.py         # yt-dlp wrapper (search + download)
│   ├── soulseek.py        # slskd REST client (search + download)
│   ├── downloader.py      # Download orchestrator + ThreadPool
│   ├── metadata.py        # Embed ID3/FLAC tags + cover art
│   ├── matcher.py         # Score Soulseek results (0.0-1.0)
│   ├── library.py         # Scan local music library + metadata
│   ├── history.py         # Download history (JSON, max 200)
│   ├── ffmpeg_manager.py  # FFmpeg setup from imageio-ffmpeg or PATH
│   ├── logger.py          # Centralized logging per module
│   └── app_state.py       # Global state (Qt signals, legacy)
│
├── web/                   # Web frontend
│   ├── app.html           # Single-page app shell
│   └── static/
│       ├── css/app.css    # All styles (dark theme)
│       └── js/
│           ├── api.js     # API client + shared utilities
│           ├── app.js     # Router, settings, boot
│           ├── player.js  # Audio player (local + preview)
│           └── views/     # Page renderers
│               ├── home.js
│               ├── search.js
│               ├── artist.js
│               ├── album.js
│               ├── library.js
│               ├── liked.js
│               ├── playlists.js
│               ├── queue.js
│               ├── history.js
│               └── faq.js
│
├── ui/                    # PyQt6 desktop UI (legacy)
│   ├── main_window.py
│   ├── views/
│   └── widgets/
│
└── docs/                  # Documentation
    ├── README.md          # This file
    ├── audit.md           # Feature audit
    ├── changelog.md       # Version history
    └── architecture.md    # System design
```

## Data Files

All persistent data is stored in `~/.songer/`:

| File | Purpose |
|------|---------|
| `config.json` | Spotify credentials, download preferences |
| `.spotify_token.json` | OAuth2 token cache (auto-refreshed) |
| `downloaded_map.json` | Track ID → file path mapping |
| `history.json` | Download history (last 200 entries) |
| `songer.log` | Application logs |
| `tools/ffmpeg.exe` | FFmpeg binary (auto-extracted) |

## API Endpoints

### Auth & Setup
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Setup page (enter Spotify credentials) |
| POST | `/setup` | Save Spotify credentials and start OAuth |
| GET | `/callback` | Spotify OAuth callback |
| GET | `/app` | Main web app |
| POST | `/disconnect` | Remove Spotify token |

### Music Data
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search?q=...` | Search Spotify (tracks, artists, albums) |
| GET | `/api/search/<type>?q=...&offset=...` | Paginated search by type |
| GET | `/api/artist/<id>` | Artist details + top tracks + albums |
| GET | `/api/album/<id>` | Album details + tracklist |
| GET | `/api/playlists` | User's Spotify playlists |
| GET | `/api/playlists/<id>/tracks` | Playlist tracks |
| GET | `/api/liked-songs` | User's liked songs |
| GET | `/api/recommendations` | Personalized recommendations |

### Downloads
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/download` | Queue a track for download |
| GET | `/api/queue` | Current download queue |
| DELETE | `/api/queue/<id>` | Cancel a download |
| DELETE | `/api/queue` | Cancel all pending downloads |
| GET | `/api/downloaded-ids` | Map of downloaded track IDs → paths |
| DELETE | `/api/downloaded-ids` | Reset download database |
| GET | `/api/events` | SSE stream for real-time updates |

### Library & History
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/library` | Scan and list local music files |
| GET | `/api/history` | Download history |
| DELETE | `/api/history` | Clear history |
| GET | `/api/cover?path=...` | Get embedded cover art |
| GET | `/api/stats` | Library stats (tracks, size, artists) |

### Settings & System
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/config` | Current configuration |
| POST | `/api/settings` | Update configuration |
| GET | `/api/status` | Spotify/Soulseek connection status |
| GET | `/api/folder-options` | Available download folder paths |
| GET | `/api/browse-folder` | Open native folder picker |
| GET | `/api/open-folder` | Open download folder in file explorer |
| POST | `/api/open-file` | Reveal file in explorer |
| GET | `/stream/<filepath>` | Stream local audio file |

## Troubleshooting

### "Spotify offline" after setup
- Check that your Client ID and Client Secret are correct
- Make sure the redirect URI in your Spotify app is exactly `http://localhost:5000/callback`
- Try disconnecting and reconnecting in Settings

### Downloads fail with "YouTubeClient não inicializado"
- This usually means yt-dlp couldn't initialize. Run `pip install -U yt-dlp` to update
- Check `~/.songer/songer.log` for detailed error messages

### FFmpeg not found / No audio conversion
- SONGER tries to use bundled FFmpeg from imageio-ffmpeg
- If that fails, install FFmpeg manually and add it to your PATH
- Without FFmpeg, downloads will be in raw format (m4a/webm) instead of mp3/flac

### Tracks show "Play" instead of "Download"
- The app tracks which songs you've downloaded in `~/.songer/downloaded_map.json`
- If you deleted your music files, go to Settings > **Reset Download Database**
- This clears the tracking so everything shows "Download" again (files are not affected)

### Soulseek downloads timeout
- Make sure slskd is running and accessible at the configured URL
- Check that your slskd API key is correct
- Soulseek depends on peer availability — some files may not be downloadable
- Use `hybrid` mode so YouTube acts as fallback

### Port 5000 already in use
- Another app is using port 5000. Either stop it or change the port:
```bash
python server.py  # Edit the port in server.py at the bottom
```

### Songs download with wrong audio
- YouTube search occasionally matches wrong videos
- Try downloading via Soulseek (`hybrid` or `soulseek` mode) for better accuracy
- Check the download log in `~/.songer/songer.log`

## Build Desktop App (Windows)

The legacy PyQt6 desktop app can be built as a standalone .exe:

```bash
pip install pyinstaller
pyinstaller songer_windows.spec
# Output: dist/SONGER.exe
```

## License

Personal project. Not affiliated with Spotify, YouTube, or Soulseek.

## Other Docs

- [audit.md](audit.md) — Complete feature audit (what's done, what's missing)
- [changelog.md](changelog.md) — Version history
- [architecture.md](architecture.md) — System design and tech decisions
