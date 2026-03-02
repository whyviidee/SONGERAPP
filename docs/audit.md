# SONGER — Audit de Features

> Última actualização: 2026-03-02 (v1.3.0)
> Estado geral: **Funcional, em maturação**

---

## FEATURES IMPLEMENTADAS ✅

### Core — Downloads
- [x] Parse URLs Spotify (playlist, album, track, artist)
- [x] Pesquisa texto livre Spotify
- [x] Download via YouTube (yt-dlp, search automática)
- [x] Download via Soulseek (slskd REST API)
- [x] Modo híbrido — Soulseek primeiro, fallback YouTube
- [x] Formatos: FLAC, MP3 320/256/128, raw fallback
- [x] Embed metadata — ID3v2 (MP3), FLAC tags, cover art
- [x] Organização automática: Artist/Album/Track
- [x] Concorrência — ThreadPool (6 workers), UI não bloqueia
- [x] OAuth2 Spotify com cache de token

### UI
- [x] Dark theme estilo Spotify
- [x] Sidebar navegação (Pesquisar, Playlists, Downloads, Biblioteca, Histórico)
- [x] Search View — input URL ou texto, resultados dinâmicos
- [x] Playlists View — load playlists do user
- [x] Queue/Downloads View — fila em tempo real
- [x] Library View — scan local Artist/Album
- [x] History View — histórico persistente, re-download
- [x] Bottom bar — stats + preview player + abrir pasta
- [x] Settings dialog — Spotify, Soulseek, Download path, format, source
- [x] FFmpeg setup wizard

### Sistema
- [x] ffmpeg bundled (imageio-ffmpeg)
- [x] Logging centralizado (arquivo + console)
- [x] Scoring inteligente ficheiros Soulseek (matcher)
- [x] Persistência de histórico (max 200 entradas)
- [x] AppState singleton — estado global partilhado via Qt signals

### UX Polish (v1.1.0)
- [x] Badge ● verde/vermelho na sidebar — estado Spotify em tempo real
- [x] Banner onboarding na Search View quando Spotify não configurado
- [x] Loading bar indeterminada ao pesquisar/carregar playlists
- [x] Botão ✕ por track na fila — cancelar download individual
- [x] Botão "Cancelar tudo" no header da view Downloads
- [x] Windows toast notification quando batch de downloads termina

### Web App v1.3.0
- [x] Artist detail page — top tracks + discografia + header com imagem
- [x] Album detail page — tracklist + "Download All" + header com capa
- [x] Search limit 9 por categoria + "See all" com paginação
- [x] Download state tracking — Play button para tracks já baixadas
- [x] Persistent downloaded map (sobrevive restarts)
- [x] Home: Quick Actions, Top Artists com fotos, Recommendations, Clear recent
- [x] Soundwave loading animation ao mudar de tab
- [x] Cover art auto-preenchida no histórico via Spotify search
- [x] Stats: playlists count real do Spotify
- [x] `_wireDownloadButtons()` partilhado em todas as views

### Player + Home (v1.2.0)
- [x] Home View — dashboard com saudação, quick actions, stats, histórico recente
- [x] Player embutido — QMediaPlayer local com play/pause, stop, seek, volume, mute
- [x] Badges Spotify/Soulseek na bottom bar
- [x] Botão ▶ play em cada track da biblioteca e da fila
- [x] Double-click em qualquer track para fazer play
- [x] Stop button + volume slider + toggle mute no player
- [x] Botão "Limpar" nos Recentes da Home
- [x] Filtro por artista/nome na Biblioteca
- [x] Verificação de duplicados antes de download
- [x] Auto-scroll na fila de downloads
- [x] Tooltips em todos os botões de ícone
- [x] Rendering Windows — todos os caracteres Unicode problemáticos corrigidos

---

## FEATURES EM FALTA / MELHORIAS ❌

### UX — Alta Prioridade
- [x] **Feedback visual no arranque** — badges Spotify/Soulseek na bottom bar, verificação em background ao arrancar
- [x] **Mensagem de boas-vindas / onboarding** — banner na Search View quando Spotify não configurado
- [x] **Notificação de download concluído** — Windows toast notification quando batch termina
- [x] **Botão cancelar download individual** — botão ✕ por track na fila
- [x] **Botão cancelar tudo / limpar fila** — botão "Cancelar tudo" no header de Downloads
- [x] **Estado visual do Soulseek** — badge ● Sl na bottom bar (verde/cinza)

### Pesquisa — Média Prioridade
- [x] **Pesquisa de artistas** — página de artista com top tracks e discografia navegável
- [x] **Paginação de resultados** — search paginado com "See all" e "Load more"
- [x] **Preview de áudio funcional** — QMediaPlayer local a funcionar, play de ficheiros descarregados
- [x] **Scroll para track a descarregar** — auto-scroll na fila ao adicionar nova track

### Download — Média Prioridade
- [ ] **Retomar downloads interrompidos** — se app fechar a meio, downloads perdem-se. Devia persistir queue.
- [x] **Verificar duplicados** — verifica se ficheiro já existe antes de descarregar, skip automático.
- [ ] **Qualidade automática** — modo "best available" que adapta formato ao que Soulseek encontra.
- [ ] **Download de artista completo** — via URL artista, opção "Download discografia".
- [ ] **Rate limiting / throttle** — sem controlo de velocidade de download.

### Biblioteca — Média Prioridade
- [x] **Reprodutor integrado** — Library View com botão ▶ por track + double-click para play
- [x] **Filtros na biblioteca** — filtro por artista ou nome em tempo real
- [ ] **Contagem correcta de tracks** — Library pode não reflectir ficheiros novos sem re-scan manual.
- [x] **Botão refresh scan** — botão "Atualizar" no header da biblioteca

### Técnico — Baixa Prioridade
- [ ] **Testes automatizados** — zero unit tests ou integration tests.
- [ ] **Ícone da aplicação** — `icon=None` no spec. App sem ícone próprio.
- [ ] **Auto-updater** — sem mecanismo de update automático.
- [ ] **Crash reporter** — erros inesperados não são reportados de forma útil ao user.
- [ ] **Modo portable** — config em `~/.songer/` — não funciona como app totalmente portable (config junto ao .exe).
- [ ] **Changelog in-app** — sem "What's new" visível dentro da app.
- [ ] **Keyboard shortcuts** — sem atalhos de teclado documentados ou implementados.

### Windows Específico — Média Prioridade
- [ ] **Integração com Windows Notifications** — usar Windows toast notifications nativas.
- [ ] **Associação de ficheiros** — abrir `.songer` links directamente (protocolo custom).
- [ ] **Inicializar com Windows** — opção de startup automático.
- [ ] **Tray icon** — minimizar para system tray em vez de fechar.

---

## BUGS CONHECIDOS 🐛

- [ ] **Preview player no Windows** — QMediaPlayer pode requerer codecs adicionais (K-Lite ou Windows Media codecs). A testar.
- [ ] **ffmpeg PATH no Windows** — se user tem ffmpeg no PATH do sistema, pode conflituar com o bundled.
- [ ] **Soulseek timeout** — se slskd não responde, app pode ficar bloqueada em polling sem timeout claro.
- [ ] **Token Spotify expira silenciosamente** — em alguns casos o refresh falha sem indicar ao user.
- [ ] **Unicode em paths Windows** — artistas com caracteres especiais (japonês, árabe) podem falhar ao criar pastas.

---

## MELHORIAS VISUAIS 🎨

- [x] **Animações de loading** — soundwave animation ao mudar de tab enquanto carrega dados.
- [ ] **Progress bar global** — barra de progresso geral na bottom bar (ex: "3/10 tracks feitas").
- [ ] **Cores de status** — verde/amarelo/vermelho mais consistentes nas tracks da fila.
- [ ] **Modo fullscreen** — app não tira partido de ecrãs grandes.
- [ ] **Tamanho mínimo da janela** — resize pode quebrar layout em janelas pequenas.

---

## PRIORIDADE DE IMPLEMENTAÇÃO

| # | Feature | Impacto | Esforço |
|---|---------|---------|---------|
| 1 | Feedback estado Spotify na UI | Alto | Baixo |
| 2 | Onboarding primeiro uso | Alto | Baixo |
| 3 | Notificação download concluído | Alto | Baixo |
| 4 | Cancelar download individual/todos | Alto | Médio |
| 5 | Verificar duplicados antes de download | Alto | Médio |
| 6 | Retomar queue após fechar app | Médio | Alto |
| 7 | Tray icon Windows | Médio | Médio |
| 8 | Ícone da aplicação | Baixo | Baixo |
| 9 | Filtros na biblioteca | Médio | Médio |
| 10 | Testes automatizados | Alto (long term) | Alto |
