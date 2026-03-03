# SONGER — Audit de Features

> Ultima actualização: 2026-03-03 (v1.4.0)
> Estado geral: **Funcional, quase final**

---

## FEATURES IMPLEMENTADAS

### Core — Downloads
- [x] Parse URLs Spotify (playlist, album, track, artist)
- [x] Pesquisa texto livre Spotify
- [x] Download via YouTube (yt-dlp, search automática)
- [x] Download via Soulseek (slskd REST API)
- [x] Modo híbrido — Soulseek primeiro, fallback YouTube
- [x] Formatos: FLAC, MP3 320/256/128, raw fallback
- [x] Embed metadata — ID3v2 (MP3), FLAC tags, cover art
- [x] Organização automática: Artist/Album/Title.ext
- [x] Concorrência — ThreadPool (workers configuráveis), UI não bloqueia
- [x] OAuth2 Spotify com cache de token
- [x] Verificação de duplicados antes de download
- [x] Nome do ficheiro = título da música (artista/álbum nos metadados)

### Web App — Pesquisa & Navegação
- [x] Search multi-tipo — tracks, artistas, álbuns
- [x] Paginação com "See all" e "Load more"
- [x] Artist detail page — top tracks + discografia + header
- [x] Album detail page — tracklist + "Download All" + header
- [x] Nomes de artistas clicáveis em todas as views (navega para página do artista)
- [x] "In Your Library" section na página de artista (mostra tracks que o user já tem)
- [x] Recomendações personalizadas baseadas nas liked songs

### Web App — Player
- [x] Player embutido com play/pause, seek, volume, mute
- [x] Preview 30s de qualquer track via Spotify (botão headphones)
- [x] Double-click numa track faz play se já estiver downloaded
- [x] Playlist queue com shuffle, next, previous, repeat
- [x] Preview mode visual (borda verde, badge "PREVIEW", progress bar amber)
- [x] Now Playing modal (botão queue) — mostra playlist actual
- [x] Streaming de ficheiros locais via `/stream/` endpoint

### Web App — Home
- [x] Dashboard com stats (tracks, downloading, playlists, storage)
- [x] Quick Actions (sync liked, import URL, open folder, pending downloads)
- [x] Recently Downloaded — cards clicáveis (play/pause no click)
- [x] Top Artists — clicáveis, navegam para página do artista no Spotify
- [x] Recommendations — sugestões personalizadas com download buttons
- [x] Clear history button

### Web App — Library
- [x] Scan recursivo da pasta de downloads
- [x] Sort por: Recently Added (default), Artist A-Z, Year, Genre
- [x] Filtro por artista ou nome da track
- [x] Leitura de metadados (ano, género) via Mutagen
- [x] Play button por track + double-click para play
- [x] Reveal in Explorer por track
- [x] Open Folder + Refresh buttons
- [x] Agrupamento Artist → Album (ou Genre → Artist no modo genre)

### Web App — Downloads & Queue
- [x] Fila em tempo real via SSE (Server-Sent Events)
- [x] Cancelar download individual ou todos
- [x] Download state tracking — Play button para tracks já baixadas
- [x] Persistent downloaded map (`~/.songer/downloaded_map.json`)
- [x] Badge counter no sidebar (+1, +2...) em vez de toasts empilhados
- [x] Reset Download Database nos Settings

### Web App — UI/UX
- [x] Dark theme
- [x] Soundwave loading animation ao mudar de view
- [x] Custom confirm modals (substituem browser confirm/prompt)
- [x] Toast notifications
- [x] Folder picker com opções (Music, Downloads, Desktop)
- [x] Download path migration com legacy_paths support
- [x] Onboarding modal no primeiro uso
- [x] Status dots Spotify/Soulseek no sidebar
- [x] Lucide icons em toda a interface

### Desktop App (Legacy PyQt6)
- [x] UI dark theme com 5 views
- [x] Bottom bar com player QMediaPlayer
- [x] Windows toast notifications (winotify)
- [x] Build via PyInstaller → SONGER.exe

---

## FEATURES EM FALTA / MELHORIAS

### Download
- [ ] Retomar downloads interrompidos (queue perde-se ao fechar)
- [ ] Qualidade automática ("best available")
- [ ] Download de artista completo (discografia)
- [ ] Rate limiting / throttle

### Técnico
- [ ] Testes automatizados
- [ ] Ícone da aplicação
- [ ] Auto-updater
- [ ] Crash reporter
- [ ] Modo portable (config junto ao .exe)
- [ ] Changelog in-app
- [ ] Keyboard shortcuts

### Windows Específico
- [ ] Associação de ficheiros (protocolo custom)
- [ ] Inicializar com Windows
- [ ] Tray icon

### Visual
- [ ] Progress bar global na bottom bar
- [ ] Modo fullscreen
- [ ] Tamanho mínimo da janela (desktop)

---

## BUGS CONHECIDOS

- [ ] ffmpeg PATH no Windows pode conflituar com o bundled
- [ ] Soulseek timeout — se slskd não responde, polling sem timeout claro
- [ ] Token Spotify expira silenciosamente em alguns casos
- [ ] YouTube search ocasionalmente apanha o vídeo errado
