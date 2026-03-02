# SONGER — Changelog

## v1.3.0 — Web App: Artist/Album Pages, Smart Home, Download State (2026-03-02)
### Adicionado
- **Artist detail page** — top tracks, discografia, header com imagem/géneros/followers
- **Album detail page** — tracklist, "Download All", header com capa/artista/ano
- **Search limit 9** — max 9 resultados por categoria, "See all" com paginação
- **Download state tracking** — botão Play em vez de Download para tracks já baixadas (todas as views)
- **Persistent downloaded map** — `~/.songer/downloaded_map.json` sobrevive restarts
- **Home: Quick Actions** — sync liked, import URL, open folder, pending downloads
- **Home: Top Artists** — artistas mais frequentes na biblioteca com fotos do Spotify
- **Home: Recommendations** — sugestões baseadas nas liked songs do user (Spotify API)
- **Home: Clear recent** — botão para limpar histórico de downloads recentes
- **Soundwave loading animation** — animação de barras ao mudar de tab
- **Cover art in history** — capas auto-preenchidas via Spotify search para histórico antigo
- **Playlists count real** — stats mostra número real de playlists do Spotify

### Corrigido
- Download buttons não passavam `cover` — histórico ficava sem capas
- Artist/Album views não mostravam estado de download (missing `await`)
- Liked Songs e Playlists usavam formato de dados próprio — unificado com `_wireDownloadButtons`
- Stats "playlists synced" mostrava 0 — agora conta playlists reais do Spotify

### Backend
- `core/spotify.py`: `get_album()`, `search_type()`, `get_recommendations()`
- `server.py`: 5 novos endpoints (`/api/artist/<id>`, `/api/album/<id>`, `/api/search/<type>`, `/api/downloaded-ids`, `/api/recommendations`)
- `_wireDownloadButtons()` extraído para `api.js` como utility partilhado

---

## v1.2.0 — Player + Home + Rendering (2026-03-02)
### Adicionado
- Home View — dashboard com saudação, quick actions, stats da biblioteca, histórico recente
- Player embutido na bottom bar — QMediaPlayer local (play/pause, stop, seek, volume, mute)
- Badges Spotify/Soulseek movidos para a bottom bar (libertar sidebar)
- Botão ▶ em cada track da fila e da biblioteca — play directo
- Double-click em qualquer track para fazer play
- Botão ■ Stop + slider de volume + toggle mute (🔊/🔇) no player
- Botão "Limpar" nos Recentes da Home
- Botão ▶ no histórico para recarregar playlist na pesquisa
- Filtro por artista/nome na Biblioteca
- Verificação de duplicados antes de download (skip se ficheiro já existe)
- Auto-scroll na fila quando nova track é adicionada
- Soulseek badge e estado ligado ao AppState
- Tooltips em todos os botões de ícone

### Corrigido
- Logo "SONGER" cortado — badges removidas da sidebar
- Caracteres Unicode que não renderizavam no Windows: `↻ ⟳ ⟲ ⏹ ⏸ ⬇` substituídos por alternativas compatíveis
- Spinner da fila agora usa `| / - \` (ASCII garantido)
- Botões ▶ circulares com font-size demasiado pequeno (9-10px) — aumentado para 13px
- Botão stop agora mostra `■` em vez de `⏹`
- Botão pause agora mostra `II` em vez de `⏸`

---

## v1.1.0 — UX Polish (2026-03-02)
### Adicionado
- `core/app_state.py` — AppState singleton QObject para estado global partilhado
- Badge ● verde/vermelho junto ao logo SONGER (estado Spotify em tempo real)
- Banner onboarding na Search View quando Spotify não configurado
- Barra de loading indeterminada ao pesquisar/carregar playlists
- Botão ✕ por track na fila — cancelar download individual
- Botão "Cancelar tudo" no header da view Downloads
- Windows toast notification quando batch termina (winotify 1.1.0)

---

## v1.0.0 — Estado Actual (2026-03-02)
### Implementado
- App desktop Windows completa com PyQt6
- Integração Spotify (OAuth2, search, playlists, albums, artistas)
- Download via YouTube (yt-dlp) e Soulseek (slskd)
- Modo híbrido Soulseek → fallback YouTube
- Formatos: FLAC, MP3 320/256/128
- Metadata embed (ID3v2, FLAC tags, cover art)
- UI dark theme com 5 views (Pesquisar, Playlists, Downloads, Biblioteca, Histórico)
- Bottom bar com preview player Spotify e abrir pasta
- Settings dialog completo
- ffmpeg bundled via imageio-ffmpeg
- Logging centralizado
- Build Windows via PyInstaller → SONGER.exe
