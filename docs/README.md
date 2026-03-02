# SONGER — Documentação

App desktop Windows para download de música via Spotify + YouTube + Soulseek.

## Stack
- **Python 3.11+** + **PyQt6** (UI)
- **Spotipy** — API Spotify (OAuth2)
- **yt-dlp** — Download YouTube
- **slskd** — Soulseek P2P
- **Mutagen** — Tags ID3/FLAC
- **imageio-ffmpeg** — ffmpeg bundled

## Estrutura
```
SONGER/
├── main.py                  # Entry point
├── core/                    # Lógica de negócio
│   ├── config.py            # ~/.songer/config.json
│   ├── spotify.py           # Cliente Spotify
│   ├── youtube.py           # yt-dlp wrapper
│   ├── soulseek.py          # slskd REST client
│   ├── downloader.py        # Orquestrador + ThreadPool
│   ├── metadata.py          # Embed tags + cover art
│   ├── matcher.py           # Scoring ficheiros Soulseek
│   ├── library.py           # Scan biblioteca local
│   ├── history.py           # Histórico JSON
│   ├── ffmpeg_manager.py    # Setup ffmpeg
│   └── logger.py            # Logs centralizados
└── ui/
    ├── main_window.py       # Janela principal
    ├── views/               # 5 abas (Search, Playlists, Queue, Library, History)
    └── widgets/             # Sidebar, AlbumHeader, TrackList, BottomBar
```

## Config
- Config: `~/.songer/config.json`
- Logs: `~/.songer/songer.log`
- Histórico: `~/.songer/history.json`
- Token Spotify: `~/.songer/.spotify_token.json`

## Saída de ficheiros
`~/Music/SONGER/Artist/Album/Track.mp3`

## Run dev
```bash
python main.py
```

## Build Windows
```bash
pyinstaller songer_windows.spec
# Output: dist/SONGER.exe
```

## Docs
- [audit.md](audit.md) — Features implementadas, em falta, bugs conhecidos
- [changelog.md](changelog.md) — Histórico de versões
- [architecture.md](architecture.md) — Decisões de arquitectura
