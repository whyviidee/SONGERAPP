# SONGER — Arquitectura

## Visão Geral

```
main.py
  └── QApplication + MainWindow
        ├── Sidebar (navegação)
        ├── StackedWidget
        │   ├── SearchView  ──→ Downloader ──→ YouTube / Soulseek
        │   ├── PlaylistsView ──→ SpotifyClient
        │   ├── QueueView  (lê estado Downloader)
        │   ├── LibraryView ──→ LibraryScanner
        │   └── HistoryView ──→ HistoryManager
        └── BottomBar (stats + QMediaPlayer)
```

## Camadas

### Core (sem dependência de UI)
| Módulo | Responsabilidade |
|--------|-----------------|
| `config.py` | Leitura/escrita `~/.songer/config.json` |
| `spotify.py` | Auth + fetch tracks/playlists/albums |
| `youtube.py` | yt-dlp wrapper — search + download |
| `soulseek.py` | slskd REST — search + download |
| `downloader.py` | Orquestração — ThreadPool, hybrid logic, callbacks |
| `metadata.py` | Embed ID3/FLAC tags + cover art |
| `matcher.py` | Score 0.0-1.0 para resultados Soulseek |
| `library.py` | Scan recursivo `~/Music/SONGER` |
| `history.py` | CRUD histórico JSON (max 200) |
| `ffmpeg_manager.py` | Setup ffmpeg de imageio-ffmpeg ou PATH |
| `logger.py` | Logger centralizado por módulo |

### UI (PyQt6 Signals/Slots)
- Workers separados para operações Spotify (não bloqueiam UI)
- Downloader emite sinais `progress_updated`, `download_complete`
- MainWindow coordena sinais entre views e downloader

## Dados Persistentes
```
~/.songer/
├── config.json         # Credenciais + preferências
├── history.json        # Histórico de downloads
├── songer.log          # Logs completos
├── .spotify_token.json # OAuth token cache
└── tools/
    └── ffmpeg.exe      # ffmpeg copiado de imageio-ffmpeg
```

## Fluxo de Download
```
URL Spotify → SpotifyClient → lista de tracks
  ↓
Downloader.queue_tracks()
  ↓
ThreadPool Worker por track:
  ├── [Hybrid] SoulseekClient.search() → Matcher.score()
  │     → se score >= threshold → SoulseekClient.download()
  │     → se falha → fallback YouTube
  └── [YouTube] YouTubeClient.download(f"ytsearch1:{artist} - {title}")
  ↓
MetadataEmbedder.embed(file, track_info)
  ↓
Ficheiro final: ~/Music/SONGER/Artist/Album/Title.mp3
```

## Decisões de Design
- **JSON em vez de SQLite** — histórico simples, sem queries complexas
- **ThreadPool em vez de asyncio** — yt-dlp não é async-native
- **imageio-ffmpeg bundled** — evita dependência de instalação manual
- **slskd como proxy** — Soulseek não tem API pública; slskd é self-hosted
