# SONGER — Arquitectura

## Visão Geral

SONGER tem duas interfaces: uma web app (Flask, principal) e uma desktop app (PyQt6, legacy).
O core de negócio é partilhado entre ambas.

```
Browser ──→ Flask (server.py) ──→ Core Layer ──→ YouTube / Soulseek / Spotify
                │
                ├── /app           → SPA (single-page app)
                ├── /api/*         → REST endpoints (JSON)
                ├── /api/events    → SSE (real-time updates)
                └── /stream/*      → Audio streaming
```

## Camadas

### Core (sem dependência de UI)

| Módulo | Responsabilidade |
|--------|-----------------|
| `config.py` | Leitura/escrita `~/.songer/config.json` |
| `spotify.py` | Auth OAuth2 + search + playlists + albums + artists + liked songs + recommendations |
| `youtube.py` | yt-dlp wrapper — search YouTube + download + FFmpeg conversion |
| `soulseek.py` | slskd REST — search + download P2P |
| `downloader.py` | Orquestração — ThreadPool, hybrid logic, duplicate check, callbacks |
| `metadata.py` | Embed ID3v2/FLAC tags + cover art via Mutagen |
| `matcher.py` | Score 0.0-1.0 para resultados Soulseek (bitrate, format, name match) |
| `library.py` | Scan recursivo da pasta de downloads + leitura de metadados (ano, género) |
| `history.py` | CRUD histórico JSON (max 200 entradas) |
| `ffmpeg_manager.py` | Setup ffmpeg de imageio-ffmpeg ou system PATH |
| `logger.py` | Logger centralizado por módulo |

### Web App (Flask + Vanilla JS)

**Backend** (`server.py`):
- Flask server com ~40 endpoints REST
- SSE (Server-Sent Events) para updates em tempo real
- Streaming de áudio local via `/stream/`
- OAuth2 flow completo (setup → callback → token refresh)
- Download queue com thread pool

**Frontend** (`web/`):
- SPA com router client-side (`APP.navigate()`)
- 10 views: home, search, artist, album, library, liked, playlists, queue, history, faq
- `api.js` — HTTP client + shared utilities (artist links, preview, download buttons, modals)
- `player.js` — Audio player com dois modos (local files + Spotify preview)
- `app.js` — Router, settings, onboarding, boot

### Desktop App (Legacy PyQt6)

- `main.py` → QApplication + MainWindow
- Workers separados para operações Spotify (não bloqueiam UI)
- QMediaPlayer para reprodução local
- Windows toast notifications (winotify)
- Build via PyInstaller → SONGER.exe

## Dados Persistentes

```
~/.songer/
├── config.json            # Credenciais Spotify + preferências download
├── .spotify_token.json    # OAuth token cache (auto-refreshed)
├── downloaded_map.json    # Track ID → file path (tracking de downloads)
├── history.json           # Histórico de downloads (max 200)
├── songer.log             # Logs completos
└── tools/
    └── ffmpeg.exe         # ffmpeg copiado de imageio-ffmpeg
```

## Fluxo de Download

```
1. User pesquisa ou cola URL no frontend
2. Frontend chama /api/search ou /api/album/<id> etc.
3. Server usa SpotifyClient para obter metadata das tracks
4. User clica "Download" → POST /api/download
5. Server cria job na queue e submete ao Downloader ThreadPool
6. Worker executa:
   ├── [Hybrid] SoulseekClient.search() → Matcher.score()
   │     → score >= threshold → SoulseekClient.download()
   │     → falha → fallback YouTube
   └── [YouTube] yt-dlp search "ytsearch1:{artist} - {title}"
7. MetadataEmbedder embute tags (artist, album, title, cover, year, genre, track#)
8. Ficheiro final: ~/Music/SONGER/Artist/Album/Title.mp3
9. SSE push notifica o frontend
10. downloaded_map.json é actualizado
```

## Player Architecture

O player web tem dois modos:

**Local mode** — reproduz ficheiros downloaded via `/stream/<path>`:
- `PLAYER.playFile(path, info)` — play de um ficheiro
- `PLAYER.setPlaylist(files, idx)` — define playlist local

**Preview mode** — reproduz previews 30s do Spotify CDN:
- `PLAYER.preview(url, info)` — play de um preview
- `PLAYER.setPreviewPlaylist(tracks, idx)` — define playlist de previews
- Visual: borda verde no player, badge "PREVIEW", progress bar amber

Ambos os modos suportam shuffle, next, previous, repeat.

## Decisões de Design

- **Flask + Vanilla JS** — simplicidade máxima, sem frameworks, sem build step
- **JSON em vez de SQLite** — dados simples, sem queries complexas
- **ThreadPool em vez de asyncio** — yt-dlp não é async-native
- **imageio-ffmpeg bundled** — evita dependência de instalação manual
- **slskd como proxy** — Soulseek não tem API pública; slskd é self-hosted
- **SSE em vez de WebSocket** — mais simples para push unidirecional
- **SPA client-side** — router simples sem page reloads, estado em memória
- **Track title as filename** — metadata fica nos tags, nome do ficheiro limpo
- **downloaded_map.json** — tracking simples de downloads sem DB
