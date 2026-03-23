# SONGER

Music download manager powered by Spotify, YouTube and Soulseek. Search any song, album or artist on Spotify, download it in high quality, and manage your local music library — all from a native desktop app.

## What it does

1. You search for music using Spotify's catalog (text search or paste a Spotify URL)
2. SONGER finds and downloads the audio from YouTube or Soulseek
3. Metadata (artist, album, cover art, track number, genre, year) is embedded automatically
4. Files are organized in `Artist/Album/Title.mp3` structure

## Stack

| Component | Tech |
|-----------|------|
| Backend | Python 3.11+ / Flask |
| Frontend | React 19 + Vite 6 + Tailwind v4 + Framer Motion |
| Desktop | PyWebView (native macOS/Windows window) |
| Music API | Spotify (Spotipy) or Tidal (tidalapi) — user's choice |
| YouTube DL | yt-dlp |
| Soulseek | slskd REST API |
| Metadata | Mutagen (ID3v2, FLAC tags) |
| FFmpeg | imageio-ffmpeg (bundled) |
| Build | PyInstaller (.app / .exe) |

## Requirements

- **Python 3.11+**
- **Node.js 18+** (for building the frontend)
- **Spotify Developer Account** (free) — for API credentials
- **FFmpeg** — bundled automatically via imageio-ffmpeg
- **slskd** (optional) — only needed for Soulseek downloads

## Quick Start

### macOS (.app)

```bash
# Build and run
bash build_mac.sh
open dist/SONGER.app
```

### Development

```bash
# Install Python deps
pip install -r requirements.txt

# Install and build frontend
cd frontend && npm install && npm run build && cd ..

# Run
python3 songer.py
```

### First-time setup

1. The app opens with Spotify credentials pre-configured
2. Click **Connect to Spotify** — authorize in your browser
3. After authorizing, the Liquid UI loads automatically
4. You're ready to search and download

## Features

### Home
- Quick access cards: Search, Downloads, Library, Trending
- Library stats: tracks count, artists, storage used (auto MB/GB)
- Your Music: downloaded tracks with play button and cover art
- Delete tracks with smart cleanup (removes empty folders)

### Search
- Live search with debounce (400ms)
- Tabs: Tracks / Albums / Artists with result counts
- Album detail view with cover, tracklist, "Download Album"
- Artist cards with genre info — click to search their tracks
- Paste Spotify URLs directly (tracks, albums, playlists)
- Downloaded tracks marked with checkmark (persists across sessions)
- Duplicate detection — warns before re-downloading existing tracks

### Downloads
- Real-time download progress with SSE (Server-Sent Events)
- Active queue with cancel per-job or cancel all
- ZIP playlist downloads with real-time progress (tracks done/total)
- Unzip with confirmation — extracts to library, registers tracks in history + downloaded map, deletes ZIP
- Download history with covers, dates, format, success/fail count
- Badge counter on nav dock showing active downloads
- ZIP and track downloads visible together, persist across view navigation

### My Music (Library)
- Two tabs: **Playlists** and **Liked Songs**
- Search/filter within each tab
- Pagination with "Load more" for large libraries
- Playlists clickable — opens track list with **Download** and **ZIP** buttons
- Download All for liked songs
- Downloaded tracks tagged with checkmark everywhere

### Trending
- 8 genre categories linked from TRENDING-TRACKS
- Preview top 3 per category, expand for full list
- Refresh per category (runs fetch script)
- Download individual tracks or "Download All" per genre

### Player
- Built-in audio player for downloaded tracks
- Seekable progress bar with drag support
- HTTP Range requests for instant seek
- Cover art extracted from MP3/FLAC metadata
- Play/pause, time display, close

### Settings
- Music Service: switch between Spotify and Tidal
- Download folder path
- Audio format: MP3 320/256/128
- Max concurrent downloads (1-12)
- Organize by Artist/Album toggle
- Refresh app button
- Spotify connection status
- MWLBYD signature → dagotinho.pt

## Architecture

```
SONGER/
├── songer.py              # Unified launcher (Flask + PyWebView)
├── server.py              # Flask backend (50+ REST endpoints + SSE)
├── requirements.txt       # Python dependencies
├── build_mac.sh           # macOS build script
├── songer_mac.spec        # PyInstaller spec (arm64)
│
├── frontend/              # React UI (Liquid design)
│   ├── src/
│   │   ├── App.jsx        # Root: routing, global state, player
│   │   ├── components/    # LiquidBackground, NavDock, GlassCard, TrackRow, DownloadButton, MiniPlayer
│   │   ├── views/         # HomeView, SearchView, QueueView, LibraryView, TrendingView, SettingsView
│   │   ├── hooks/         # useSSE, useSpotifyStatus, useDownloadQueue
│   │   └── lib/api.js     # API client (get/post/del + all endpoints)
│   └── dist/              # Production build (served by Flask)
│
├── core/                  # Backend business logic
│   ├── config.py          # ~/.songer/config.json
│   ├── spotify.py         # Spotify OAuth2 + API
│   ├── youtube.py         # yt-dlp wrapper
│   ├── soulseek.py        # slskd REST client
│   ├── downloader.py      # ThreadPool download orchestrator
│   ├── metadata.py        # ID3v2/FLAC tag embedding
│   ├── matcher.py         # Soulseek result scoring
│   ├── library.py         # Local music scanner
│   ├── history.py         # Download history CRUD
│   ├── ffmpeg_manager.py  # FFmpeg bundling
│   ├── logger.py          # Centralized logging
│   └── app_state.py       # Global state (Qt-optional)
│
├── web/                   # Legacy web frontend (Vanilla JS)
├── tools/trending/        # Trending tracks .md files (symlinked)
└── docs/                  # Documentation
```

## Data Files

All persistent data in `~/.songer/`:

| File | Purpose |
|------|---------|
| `config.json` | Spotify credentials, download preferences |
| `.spotify_token.json` | OAuth2 token (auto-refreshed) |
| `downloaded_map.json` | Track ID → file path (download checkmarks) |
| `history.json` | Download history (last 200 entries) |
| `songer.log` | Application logs |
| `tools/ffmpeg` | FFmpeg binary (auto-extracted) |

## Design: "Liquid"

- Dark background (#0a0a0f) with animated violet/cyan gradient blobs
- Glassmorphism panels with backdrop blur
- Floating navigation dock at bottom
- Spring animations on page transitions
- Cover art as hero elements
- Palette: violet (#8b5cf6) + cyan (#06b6d4) + white soft (#f0f0f5)

## API Endpoints (key)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search?q=...` | Search Spotify |
| GET | `/api/album/<id>` | Album tracks |
| GET | `/api/playlists` | User playlists |
| GET | `/api/liked-songs` | Liked songs |
| POST | `/api/download` | Queue download |
| GET | `/api/queue` | Download queue |
| GET | `/api/events` | SSE real-time updates |
| GET | `/api/library` | Local music scan |
| GET | `/api/history` | Download history |
| GET | `/api/stream?path=...` | Stream audio (range support) |
| GET | `/api/track-cover?path=...` | Extract cover from audio file |
| GET | `/api/trending` | Trending tracks by genre |
| POST | `/api/delete-track` | Delete track + cleanup folders |
| POST | `/api/playlists/<id>/zip` | Download playlist as ZIP |
| GET | `/api/zip-jobs` | List active ZIP jobs |
| GET | `/api/zip/<id>/status` | ZIP job progress |
| POST | `/api/zip/<id>/extract` | Extract ZIP to library + delete ZIP |
| POST | `/api/open-url` | Open URL in browser |
| GET | `/api/stats` | Library stats (tracks, artists, storage MB) |
| GET | `/api/cover?url=...` | Proxy Spotify CDN images |
| GET | `/api/downloaded-ids` | Map of downloaded track IDs |
| POST | `/api/settings` | Update config |
| POST | `/api/tidal/login` | Start Tidal OAuth |
| POST | `/api/tidal/login/complete` | Check Tidal login status |
| POST | `/api/service` | Switch music service (spotify/tidal) |
| GET | `/api/check-update` | Check for app updates |

## License

Personal project by Yuri Dagot. Not affiliated with Spotify, YouTube, or Soulseek.
