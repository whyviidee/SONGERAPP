# SONGER — Web App Redesign

> Data: 2026-03-02
> Decisão: Converter SONGER de PyQt6 desktop para Flask web app local

---

## Contexto

SONGER v1.2.0 é uma app PyQt6 Windows para download de música via Spotify + YouTube + Soulseek.
O utilizador aprovou migrar para Flask web app a correr em `localhost:8888`, mantendo todos os backends existentes e implementando um UI completamente redesenhado.

## Decisão

**Flask web app local** — o server.py já existente serve de base. O browser é o frontend, Flask é o backend. Sem cloud, sem Vercel. Todos os downloads correm localmente.

---

## Stack

- **Backend**: Flask (Python 3.11+) — já existe `server.py`
- **Frontend**: HTML5 + CSS3 + Vanilla JS — sem frameworks JS
- **Icons**: Lucide icons via CDN
- **Font**: Inter via Google Fonts
- **Backends mantidos**: Spotipy, yt-dlp, slskd, Mutagen, imageio-ffmpeg

---

## Design Tokens

| Token | Valor |
|-------|-------|
| Background | `#09090B` |
| Surface/Card | `#111113` |
| Border | `#1C1C1E` |
| Accent/Primary | `#1DB954` |
| Text primary | `#FFFFFF` |
| Text secondary | `#71717A` |
| Text muted | `#3F3F46` |
| Border radius card | `14px` |
| Border radius button | `12px` |
| Font | Inter |

---

## Layout

```
┌─────────────────────────────────────────────────┐
│  Sidebar (230px)  │  Content (fill)              │
│                   │  ┌────────────────────────┐  │
│  Logo             │  │ Search bar + btn        │  │
│  ─────            │  │ Stats (4 cards)         │  │
│  Home ●           │  │ Recently Downloaded     │  │
│  Search           │  │ Album grid (5)          │  │
│  Playlists        │  └────────────────────────┘  │
│  Downloads [3]    ├─────────────────────────────  │
│  Library          │  Player bar (88px)            │
│  History          │  Art | Controls | Volume      │
│  ─────            └─────────────────────────────  │
│  ● Spotify        │                               │
│  Settings         │                               │
└─────────────────────────────────────────────────┘
```

---

## Views a implementar

### 1. Home (dashboard)
- Search bar + botão Search verde
- 4 stat cards (tracks, a descarregar, playlists, storage)
- Grid "Recently Downloaded" (5 álbuns com cover art)
- Player bar no fundo

### 2. Search Results
- Input activo, resultados em lista
- Track row: cover | título | artista | duração | botão Download
- Estados: loading, vazio, erro

### 3. Downloads Queue
- Lista de tracks em fila com progress bar por track
- Estados: pending, downloading, done, error
- Botão cancelar por track + cancelar tudo
- Auto-scroll para track activa

### 4. Playlists
- Grid de playlists do Spotify
- Click → lista de tracks da playlist
- Download all button

### 5. Library
- Scan da pasta local `~/Music/SONGER/`
- Árvore Artist → Album → Tracks
- Filtro por nome/artista
- Play button por track

### 6. History
- Lista de downloads anteriores (max 200)
- Re-download button
- Clear history

### 7. Settings (modal/overlay)
- Spotify credentials
- Soulseek URL + credentials
- Download path
- Format (FLAC, MP3 320/256/128)
- Source (YT / SL / Both)

---

## Arquitectura Flask

```
server.py              # Entry point, rotas principais
core/                  # Backends existentes (sem alterações)
web/
  index.html           # Setup Spotify (já existe)
  app.html             # Shell da app (sidebar + content + player)
  static/
    css/
      app.css          # Estilos globais + design tokens
      components.css   # Sidebar, player, cards, etc.
    js/
      app.js           # Estado global, navegação entre views
      views/
        home.js
        search.js
        queue.js
        library.js
        history.js
      api.js           # Fetch wrapper para Flask endpoints
```

### Endpoints Flask novos

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/app` | Shell HTML da app |
| GET | `/api/stats` | Stats para os 4 cards |
| GET | `/api/search?q=` | Pesquisa Spotify |
| POST | `/api/download` | Adicionar à fila |
| GET | `/api/queue` | Estado da fila (SSE ou polling) |
| DELETE | `/api/queue/<id>` | Cancelar download |
| GET | `/api/playlists` | Playlists do user |
| GET | `/api/library` | Scan biblioteca local |
| GET | `/api/history` | Histórico |
| DELETE | `/api/history` | Limpar histórico |
| GET | `/api/status` | Estado Spotify + Soulseek |
| POST | `/api/settings` | Guardar settings |

### Updates em tempo real

Usar **Server-Sent Events (SSE)** para:
- Progresso de downloads (%)
- Estado da fila
- Notificação de conclusão

---

## Player

- `<audio>` element HTML5 nativo
- Serve ficheiros locais via `/stream/<path>`
- Controlos: play/pause, prev/next (histórico), seek, volume, mute, shuffle, repeat

---

## Fluxo de arranque

```
python server.py
  → abre browser em localhost:8888
  → se token Spotify existe → redireciona para /app
  → se não → página de setup OAuth
```

---

## O que NÃO muda

- `core/` inteiro — spotify.py, youtube.py, soulseek.py, downloader.py, etc.
- `~/.songer/config.json` — formato de config
- `~/Music/SONGER/` — estrutura de ficheiros de output
- OAuth flow — server.py já funciona
