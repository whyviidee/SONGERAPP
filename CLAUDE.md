# SONGER — Ponto de referência (2026-04-08, actualizado 2026-04-08)

## Arquitectura actual

**NÃO é PyQt6.** A app actual é:
- **Backend:** Flask (`server.py`) — porta 8888, serve API + React build
- **Frontend:** React + Vite (`frontend/src/`) — compilado para `frontend/dist/`
- **Entry point:** `songer.py` — inicia Flask + abre PyWebView com `http://127.0.0.1:8888/app`
- **Versão:** 2.2.27

O código PyQt6 antigo está em `_legacy_pyqt6/` — NÃO usar, NÃO editar.

---

## Downloads — estado actual (FUNCIONANDO ✓)

### YouTube (fonte principal do flow Spotify)
- **Funciona:** sim, desde 2026-04-08
- **Ficheiro:** `core/youtube.py`
- **Fix crítico 1 — formato:** usar `"bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best"` em vez de `"bestaudio/best"`. Sem `extractor_args` de client (ios/android bloqueavam formatos).
- **Fix crítico 2 — detecção de ficheiro:** usar `postprocessor_hooks` para capturar o path exacto após conversão ffmpeg. Não usar scan por stem — o yt-dlp sanitiza nomes de forma diferente da nossa.

```python
final_path_holder = {}
def pp_hook(d):
    if d.get("status") == "finished":
        fp = (d.get("info_dict") or {}).get("filepath") or d.get("filepath", "")
        if fp:
            final_path_holder["path"] = fp

opts["postprocessor_hooks"] = [pp_hook]
```

### Soulseek
- **Estado:** não funcional (slskd não está a correr)
- **Ficheiro:** `core/soulseek.py`

### URL Directo (novo — 2026-04-08)
- **Funciona:** sim
- **Fontes:** SoundCloud, Bandcamp, Mixcloud, YouTube, 1000+ sites via yt-dlp
- **Ficheiro backend:** `core/ytdlp.py`
- **View React:** `frontend/src/views/UrlDownloadView.jsx`
- **Rota Flask:** `POST /api/url-info` → extrai metadata | `POST /api/download` com `_source: "direct"`
- **Flow:** cola URL → preview → download → fila normal

---

## Build de teste rápido (sem assinatura de developer)

```bash
cd PROJECTOS/music-tools/SONGER

# 1. Build frontend React
cd frontend && npm run build && cd ..

# 2. Build app (PyInstaller)
.venv-arm64/bin/python -m PyInstaller songer_mac.spec --noconfirm

# 3. Limpar resource forks (Sequoia xattr issue) + assinar ad-hoc
dot_clean -m dist/SONGER.app
xattr -cr dist/SONGER.app
codesign --force --deep --sign - dist/SONGER.app

# 4. Abrir
open dist/SONGER.app
```

**Nota Sequoia:** O build em `~/Documents` adiciona `com.apple.provenance` xattr que bloqueia o codesign. O `dot_clean + xattr -cr` resolve para builds de teste. Para builds de produção (notarização), usar `--distpath /tmp/songer_build` no PyInstaller.

---

## Estrutura de ficheiros importantes

```
songer.py               ← entry point da app
server.py               ← Flask API (todas as rotas)
songer_mac.spec         ← PyInstaller spec arm64
songer_mac_x86.spec     ← PyInstaller spec x86_64 (Intel)
songer_windows.spec     ← PyInstaller spec Windows
release.sh              ← release completo Mac (arm64 + x86_64 + sign + notarize + deploy)
.github/workflows/
  build-windows.yml     ← CI automático Windows (corre após cada release)
core/
  youtube.py            ← download YouTube via ytsearch
  ytdlp.py              ← download URL directo (SoundCloud, Bandcamp, etc.)
  downloader.py         ← orchestrador (sources: youtube, soulseek, direct)
  spotify.py            ← metadata + auth Spotify
  tidal.py              ← metadata + auth Tidal
landing/
  index.html            ← songerapp.me — detecção OS (Mac Silicon/Intel/Windows)
frontend/src/
  App.jsx               ← router + views
  views/
    SearchView.jsx      ← pesquisa Spotify/Tidal
    UrlDownloadView.jsx ← download URL directo (novo)
    QueueView.jsx       ← fila de downloads
    SettingsView.jsx    ← settings + auth Spotify/Tidal
  components/
    NavDock.jsx         ← navegação bottom
  lib/api.js            ← todas as chamadas à API Flask
_legacy_pyqt6/          ← código antigo PyQt6, IGNORAR
```

---

## Fonte de download — flow completo

```
[Spotify URL] → SearchView → api.download(track) → POST /api/download
                                                    → _run_download()
                                                    → Downloader.submit(track, fmt, source)
                                                    → source = config["download"]["source"] (default: "youtube")
                                                    → YouTubeClient.download(track, path, fmt)
                                                    → ytsearch1:{artist} - {title}
                                                    → postprocessor_hook captura path
                                                    → ficheiro em ~/Music/SONGER/Artist/Album/Title.mp3

[URL directo] → UrlDownloadView → api.downloadDirect(track) → POST /api/download com _source:"direct"
                                                             → YtDlpClient.download(track, path, fmt)
                                                             → yt-dlp baixa URL directamente
```

---

## Auth Spotify — IMPORTANTE

O Spotify bloqueia OAuth dentro de WebViews (PyWebView). O fluxo correcto:
1. Botão Reconfigure → abre formulário inline com Client ID + Secret
2. "Authorize in browser" → chama `/api/spotify/auth-url` (POST JSON) → devolve `auth_url`
3. Abre no browser do sistema via `/api/open-url`
4. Utilizador autoriza no Safari/Chrome → callback `http://127.0.0.1:8888/callback` guarda token
5. Frontend faz polling a `/api/status` cada 3s até `spotify === "ok"`
6. Callback mostra página "Connected! You can close this tab." (NÃO redireciona para `/app`)

**NUNCA** redirecionar o PyWebView para `accounts.spotify.com` — será bloqueado.

## Auth Tidal

Usa device flow — abre URL de verificação no browser do sistema. Polling até completar. Funciona correctamente. Botão Reconfigure em Settings → disconnect session → re-login.

## Auto-update — detecção de arquitectura

O `/api/check-update` detecta `platform.machine()` e devolve o DMG correcto:
- `arm64` → `SONGER-x.y.z-arm64.dmg`
- `x86_64` → `SONGER-x.y.z-x86_64.dmg`

Bug antigo: pegava sempre no primeiro `.dmg` da lista (arm64), partido no Intel. Corrigido.

## Build Windows (automático via CI)

Não é necessário ter Windows. O GitHub Actions (`build-windows.yml`) corre automaticamente após cada release publicado:
1. Runner `windows-latest` faz build com `songer_windows.spec`
2. Cria `SONGER-x.y.z-windows.zip`
3. Anexa à GitHub Release
4. Faz deploy Vercel com o zip (landing serve `/SONGER-windows.zip`)

Secrets necessários no repo: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (já configurados).

## Landing page (songerapp.me)

Detecção automática de OS:
- Windows → "Download for Windows" → `/SONGER-windows.zip`
- Mac Apple Silicon → "Download for Mac — Apple Silicon" → `/SONGER-arm64.dmg`
- Mac Intel → "Download for Mac — Intel" → `/SONGER-x86_64.dmg`

## Intel Mac (macOS 12 Monterey) — CRÍTICO

O Python 3.11/3.12 do Homebrew foi compilado com macOS 13 SDK → usa `_mkfifoat` → crash em Monterey.
**Fix:** usar python.org Python 3.11 (`python-3.11.9-macos11.pkg`) que compila com macOS 11 SDK.

```bash
# Instalar (uma vez)
curl -O https://www.python.org/ftp/python/3.11.9/python-3.11.9-macos11.pkg
sudo installer -pkg python-3.11.9-macos11.pkg -target /

# Recriar venv x86
rm -rf .venv-x86
arch -x86_64 /Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11 -m venv .venv-x86
arch -x86_64 .venv-x86/bin/pip install flask spotipy yt-dlp mutagen imageio-ffmpeg pywebview requests "pyinstaller==6.19.0"
```

`release.sh` já aponta para `/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11`.

## Dependências principais (venv arm64)

- `yt-dlp`
- `flask`
- `spotipy`
- `tidalapi`
- `mutagen`
- `pywebview`
- `imageio-ffmpeg`
- `pyinstaller==6.19.0`
