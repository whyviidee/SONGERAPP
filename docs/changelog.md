# SONGER — Changelog

## v2.0.0 — Liquid Redesign (2026-03-23)

### New
- **Complete UI rewrite** — React 19 + Vite 6 + Tailwind v4 + Framer Motion
- **"Liquid" design system** — animated violet/cyan gradient blobs, glassmorphism, floating nav dock
- **PyWebView desktop wrapper** — native macOS window, single `python3 songer.py` launch
- **Unified launcher** (`songer.py`) — Flask backend auto-starts in background thread
- **Search redesign** — tabs (Tracks/Albums/Artists), album detail view with "Download Album", artist cards
- **My Music view** — Playlists + Liked Songs tabs with search and pagination
- **Downloads view** — active queue + download history in one place
- **Trending view** — 8 genre categories from TRENDING-TRACKS with refresh and "Download All"
- **Mini Player** — plays downloaded tracks with seekable progress bar (HTTP Range), cover art from file
- **Download badge** — nav dock shows count of active downloads
- **Track deletion** — delete from app with smart folder cleanup (removes empty artist/album dirs)
- **Cover art extraction** — `/api/track-cover` reads embedded artwork from MP3/FLAC
- **Global downloaded state** — checkmarks persist across all views and app restarts
- **Spotify auto-config** — credentials pre-populated, one-click OAuth
- **MWLBYD signature** — clickable in Settings, opens dagotinho.pt
- **Performance optimized** — faster page transitions, reduced animation overhead, slower background blobs
- **ZIP playlist download** — download entire playlist as ZIP to music folder
- **Unzip with confirmation** — one-click extract ZIP to library + auto-delete ZIP + registers all tracks in history and downloaded map
- **ZIP progress in Downloads** — real-time progress via SSE (tracks done/total + progress bar)
- **ZIP jobs persistent** — `/api/zip-jobs` endpoint, visible when navigating between views
- **Duplicate detection** — warns before downloading already-downloaded tracks (skip existing or force all)
- **Spotify URL support** — paste track/album/playlist URLs directly in search bar
- **Smart storage display** — auto MB/GB based on size
- **Tidal integration** — alternative to Spotify, OAuth login, search/playlists/liked songs
- **Music Service selector** — switch between Spotify and Tidal in Settings
- **YouTube fix** — Deno JS solver + Chrome cookies for YouTube bot detection bypass

### Architecture changes
- Frontend moved from Vanilla JS to React (`frontend/` directory)
- `app_state.py` now works without PyQt6 (headless mode for Flask-only)
- Stream endpoint supports HTTP Range requests for audio seeking
- New endpoints: `/api/stream`, `/api/track-cover`, `/api/delete-track`, `/api/open-url`, `/api/zip-jobs`, `/api/zip/<id>/extract`, `/api/tidal/login`, `/api/tidal/login/complete`, `/api/service`, `/api/check-update`
- `core/tidal.py` — TidalClient with same interface as SpotifyClient
- PyInstaller spec updated for React build + PyWebView + trending symlinks
- Cover proxy (`/api/cover?url=`) for Spotify CDN images

### Removed
- PyQt6 desktop UI dependency (optional, backwards compatible)
- `winotify` dependency (Windows-only)
- Separate History view (merged into Downloads)
- Downloaded tab from Library (moved to Home "Your Music")

---

## v1.4.0 — UX Upgrade: Preview, Artists, Queue Modal, Library Sort (2026-03-03)
### Adicionado
- **Preview 30s** — botão headphones em cada track para ouvir preview do Spotify antes de download
- **Artistas clicáveis** — nomes de artistas são links em todas as views (navega para página do artista)
- **Now Playing modal** — botão queue abre modal com playlist actual (em vez de ir para downloads)
- **Custom modals** — todas as confirmações usam modais bonitos em vez de `confirm()`/`prompt()` do browser
- **Library sort** — sort por Recently Added (default), Artist A-Z, Year, Genre
- **Metadata library** — scan lê ano e género dos ficheiros via Mutagen
- **Download badge** — contador no sidebar (+1, +2...) em vez de toasts empilhados
- **Recently Downloaded playable** — cards na home fazem play/pause ao clicar
- **Top Artists clickable** — navega para página do artista no Spotify
- **"In Your Library"** — página de artista mostra tracks que o user já tem localmente
- **Reset Download Database** — botão nos Settings para limpar tracking (ficheiros não são apagados)
- **Folder picker** — modal com opções de pasta (Music, Downloads, Desktop) usando paths do server
- **Path migration** — ao mudar download path, opção de manter ambos os paths ou só o novo
- **Player preview mode** — borda verde, badge "PREVIEW", progress bar amber, shuffle/next/prev/repeat

### Corrigido
- Nome dos ficheiros agora é só o título da música (artista/álbum vão nos metadados)
- Double-click numa track só faz play se o ficheiro existir localmente
- Confirm modal centrado com flex-wrap nos botões
- Browse folder era lento (timeout do API) — agora abre modal instantâneo

---

## v1.3.0 — Web App: Artist/Album Pages, Smart Home, Download State (2026-03-02)
### Adicionado
- Artist detail page — top tracks, discografia, header com imagem/géneros/followers
- Album detail page — tracklist, "Download All", header com capa/artista/ano
- Search limit 9 por categoria + "See all" com paginação
- Download state tracking — Play button para tracks já baixadas
- Persistent downloaded map (`~/.songer/downloaded_map.json`)
- Home: Quick Actions, Top Artists com fotos, Recommendations, Clear recent
- Soundwave loading animation ao mudar de tab
- Cover art auto-preenchida no histórico via Spotify search
- Stats: playlists count real do Spotify

### Corrigido
- Download buttons não passavam `cover`
- Artist/Album views não mostravam estado de download
- Liked Songs e Playlists usavam formato de dados diferente — unificado com `_wireDownloadButtons`

---

## v1.2.0 — Player + Home + Rendering (2026-03-02)
### Adicionado
- Home View — dashboard com saudação, quick actions, stats, histórico recente
- Player embutido — QMediaPlayer local (play/pause, stop, seek, volume, mute)
- Badges Spotify/Soulseek na bottom bar
- Botão play em cada track da biblioteca e da fila
- Double-click em qualquer track para play
- Filtro por artista/nome na Biblioteca
- Verificação de duplicados antes de download
- Auto-scroll na fila de downloads
- Tooltips em todos os botões de ícone

### Corrigido
- Caracteres Unicode que não renderizavam no Windows
- Spinner da fila usa ASCII garantido
- Botões circulares com font-size pequeno

---

## v1.1.0 — UX Polish (2026-03-02)
### Adicionado
- AppState singleton para estado global partilhado
- Badge verde/vermelho na sidebar (estado Spotify em tempo real)
- Banner onboarding na Search View
- Loading bar indeterminada ao pesquisar/carregar
- Botão cancelar download individual
- Botão "Cancelar tudo" no header Downloads
- Windows toast notification quando batch termina

---

## v1.0.0 — First Release (2026-03-02)
### Implementado
- App desktop Windows completa com PyQt6
- Integração Spotify (OAuth2, search, playlists, albums, artistas)
- Download via YouTube (yt-dlp) e Soulseek (slskd)
- Modo híbrido Soulseek → fallback YouTube
- Formatos: FLAC, MP3 320/256/128
- Metadata embed (ID3v2, FLAC tags, cover art)
- UI dark theme com 5 views
- Settings dialog completo
- ffmpeg bundled via imageio-ffmpeg
- Logging centralizado
- Build Windows via PyInstaller
