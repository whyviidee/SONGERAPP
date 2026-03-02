# UX Polish — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implementar 6 melhorias UX no SONGER: AppState central, badge Spotify na sidebar, onboarding primeiro uso, cancelar downloads, loading spinners, e Windows toast notifications.

**Architecture:** Foundation First — criar `core/app_state.py` como singleton QObject primeiro, integrá-lo em `spotify.py` e `downloader.py`, depois construir todas as features de UI em cima desse estado partilhado.

**Tech Stack:** Python 3.11, PyQt6 6.6+, winotify 1.1+ (nova dep), sem outros packages novos.

**Root:** `e:\CODING\CLAUDECODEHOUSE\PROJECTOS\music-tools\SONGER\`

---

## Task 1: Criar `core/app_state.py`

**Files:**
- Create: `core/app_state.py`

**Step 1: Criar o ficheiro**

```python
# core/app_state.py
from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal


class AppState(QObject):
    """Estado global da app. Singleton. Subscrevem via sinais Qt."""

    spotify_status_changed = pyqtSignal(bool, str)      # (conectado, username)
    download_stats_changed = pyqtSignal(int, int, int)  # (done, fail, pending)

    _instance: AppState | None = None

    def __init__(self):
        super().__init__()
        self._spotify_connected = False
        self._spotify_username = ""

    @classmethod
    def instance(cls) -> "AppState":
        if cls._instance is None:
            cls._instance = AppState()
        return cls._instance

    def set_spotify_connected(self, connected: bool, username: str = "") -> None:
        self._spotify_connected = connected
        self._spotify_username = username
        self.spotify_status_changed.emit(connected, username)

    def is_spotify_connected(self) -> bool:
        return self._spotify_connected

    def get_spotify_username(self) -> str:
        return self._spotify_username

    def update_download_stats(self, done: int, fail: int, pending: int) -> None:
        self.download_stats_changed.emit(done, fail, pending)
```

**Step 2: Verificar que o ficheiro existe sem erros de sintaxe**

```bash
cd "e:\CODING\CLAUDECODEHOUSE\PROJECTOS\music-tools\SONGER"
python -c "from core.app_state import AppState; s = AppState.instance(); print('AppState OK:', s)"
```

Esperado: `AppState OK: <core.app_state.AppState object at ...>`

**Step 3: Commit**

```bash
git add core/app_state.py
git commit -m "feat: add AppState singleton for shared app state"
```

---

## Task 2: Integrar AppState em `spotify.py`

**Files:**
- Modify: `core/spotify.py` — métodos `connect`, `connect_with_code`, `logout`

**Step 1: Adicionar import no topo de `core/spotify.py`**

Após a linha `from core.logger import get_logger`:
```python
from core.app_state import AppState
```

**Step 2: Modificar `connect()` — emitir estado após auth**

Substituir o método `connect()` existente (linhas 52-63):
```python
def connect(self) -> bool:
    token_data = self._load_token()
    if not token_data:
        AppState.instance().set_spotify_connected(False)
        return False
    if time.time() > token_data.get("expires_at", 0) - 60:
        try:
            token_data = self._refresh_token(token_data["refresh_token"])
            self._save_token(token_data)
        except Exception:
            AppState.instance().set_spotify_connected(False)
            return False
    self._sp = spotipy.Spotify(auth=token_data["access_token"])
    try:
        user = self._sp.current_user()
        username = user.get("display_name") or user.get("id", "")
        AppState.instance().set_spotify_connected(True, username)
    except Exception:
        AppState.instance().set_spotify_connected(False)
        return False
    return True
```

**Step 3: Modificar `connect_with_code()` — emitir após login manual**

Substituir o método `connect_with_code()` existente (linhas 42-50):
```python
def connect_with_code(self, pasted_url: str) -> bool:
    code = self._extract_code(pasted_url)
    if not code:
        raise ValueError("Não encontrei o código no URL. Cola o URL completo da barra do browser.")
    token_data = self._exchange_code(code)
    self._save_token(token_data)
    self._sp = spotipy.Spotify(auth=token_data["access_token"])
    user = self._sp.current_user()
    username = user.get("display_name") or user.get("id", "")
    AppState.instance().set_spotify_connected(True, username)
    return True
```

**Step 4: Modificar `logout()` — emitir desconexão**

Substituir o método `logout()` existente (linhas 77-80):
```python
def logout(self):
    self._sp = None
    if CACHE_PATH.exists():
        CACHE_PATH.unlink()
    AppState.instance().set_spotify_connected(False)
```

**Step 5: Verificar importação sem erros**

```bash
python -c "from core.spotify import SpotifyClient; print('spotify.py OK')"
```

Esperado: `spotify.py OK`

**Step 6: Commit**

```bash
git add core/spotify.py
git commit -m "feat: emit AppState spotify status on connect/disconnect"
```

---

## Task 3: Inicializar AppState em `main_window.py`

**Files:**
- Modify: `ui/main_window.py`

**Step 1: Adicionar import no topo**

Após `from core.logger import get_logger`:
```python
from core.app_state import AppState
```

**Step 2: No `__init__` do `MainWindow`, após `self._build_ui()`, inicializar AppState e verificar Spotify**

Após a linha `self._connect_signals()` (linha 52), adicionar:
```python
        self._app_state = AppState.instance()
        self._check_spotify_on_startup()
```

**Step 3: Adicionar o método `_check_spotify_on_startup()`** — inserir após `_connect_signals()`:

```python
    def _check_spotify_on_startup(self):
        """Verifica estado Spotify em background ao arrancar."""
        client_id = self._config.get("spotify", "client_id", default="")
        if not client_id:
            # Sem credenciais — não tenta conectar
            AppState.instance().set_spotify_connected(False)
            return

        from PyQt6.QtCore import QThread
        class _ConnectWorker(QThread):
            def __init__(self, config):
                super().__init__()
                self._config = config
            def run(self):
                try:
                    from core.spotify import SpotifyClient
                    sp = SpotifyClient(
                        self._config.get("spotify", "client_id", default=""),
                        self._config.get("spotify", "client_secret", default=""),
                    )
                    sp.connect()  # emite AppState internamente
                except Exception:
                    AppState.instance().set_spotify_connected(False)

        self._startup_worker = _ConnectWorker(self._config)
        self._startup_worker.start()
```

**Step 4: Verificar arranque sem erros**

```bash
python -c "
import sys
from PyQt6.QtWidgets import QApplication
app = QApplication(sys.argv)
from ui.main_window import MainWindow
w = MainWindow()
print('MainWindow OK')
app.quit()
"
```

Esperado: `MainWindow OK` (sem traceback)

**Step 5: Commit**

```bash
git add ui/main_window.py
git commit -m "feat: check spotify connection on startup via AppState"
```

---

## Task 4: Badge Spotify na Sidebar

**Files:**
- Modify: `ui/widgets/sidebar.py`

**Step 1: Adicionar import AppState no topo**

Após `from ui.theme import BG_SIDEBAR, GREEN, TEXT_DIM, TEXT_SEC`:
```python
from core.app_state import AppState
```

**Step 2: Substituir a construção do logo na `_build()` para incluir o badge**

Substituir o bloco do logo (linhas 82-85):
```python
        # Logo row com badge Spotify
        logo_row = QWidget()
        logo_row.setStyleSheet("background: transparent;")
        logo_row_layout = QHBoxLayout(logo_row)
        logo_row_layout.setContentsMargins(16, 0, 12, 0)
        logo_row_layout.setSpacing(6)

        logo = QLabel("S O N G E R")
        logo.setFixedHeight(44)
        logo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {GREEN}; letter-spacing: 3px; background: transparent;")

        self._spotify_badge = QLabel("●")
        self._spotify_badge.setFixedSize(16, 44)
        self._spotify_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spotify_badge.setStyleSheet("color: #555; font-size: 10px; background: transparent;")
        self._spotify_badge.setToolTip("A verificar Spotify...")
        self._spotify_badge.setCursor(Qt.CursorShape.PointingHandCursor)
        self._spotify_badge.mousePressEvent = lambda _: self.page_changed.emit("settings")

        logo_row_layout.addWidget(logo)
        logo_row_layout.addStretch()
        logo_row_layout.addWidget(self._spotify_badge)

        logo_row.setFixedHeight(44)
        layout.addWidget(logo_row)
```

**Step 3: No final do `__init__` do `Sidebar`, subscrever AppState**

Após `self._build()`:
```python
        AppState.instance().spotify_status_changed.connect(self._on_spotify_status)
```

**Step 4: Adicionar o método `_on_spotify_status()`**

Após `set_active()`:
```python
    def _on_spotify_status(self, connected: bool, username: str):
        if connected:
            self._spotify_badge.setStyleSheet("color: #1DB954; font-size: 10px; background: transparent;")
            tip = f"Spotify: conectado"
            if username:
                tip += f" — {username}"
            self._spotify_badge.setToolTip(tip)
        else:
            self._spotify_badge.setStyleSheet("color: #E53935; font-size: 10px; background: transparent;")
            self._spotify_badge.setToolTip("Spotify: desconectado — clica para configurar")
```

**Step 5: Testar visualmente**

```bash
python main.py
```

Verificar:
- Badge `●` visível junto ao logo SONGER (cinza no arranque)
- Fica verde se Spotify estiver configurado com token válido
- Fica vermelho se não estiver
- Tooltip correcto ao hover
- Click no badge → abre Definições

**Step 6: Commit**

```bash
git add ui/widgets/sidebar.py
git commit -m "feat: spotify status badge in sidebar header"
```

---

## Task 5: Onboarding — Banner na SearchView

**Files:**
- Modify: `ui/views/search_view.py`

**Step 1: Adicionar import AppState no topo**

Após `from ui.theme import TEXT, TEXT_SEC, TEXT_DIM, GREEN, BG_CARD, BG_MAIN`:
```python
from core.app_state import AppState
```

**Step 2: Na `_build()` do `SearchView`, adicionar banner após a search bar**

Após o bloco `layout.addLayout(search_row)` (linha 167):
```python
        # Banner de onboarding (visível quando Spotify não configurado)
        self._onboarding_banner = QFrame()
        self._onboarding_banner.setObjectName("onboarding_banner")
        self._onboarding_banner.setStyleSheet("""
            QFrame#onboarding_banner {
                background: #2a2000;
                border: 1px solid #554400;
                border-radius: 8px;
            }
        """)
        self._onboarding_banner.setFixedHeight(44)
        banner_layout = QHBoxLayout(self._onboarding_banner)
        banner_layout.setContentsMargins(14, 0, 14, 0)

        banner_lbl = QLabel("⚠  Spotify não configurado")
        banner_lbl.setStyleSheet("color: #ffcc00; font-size: 12px; background: transparent;")

        banner_btn = QPushButton("Abrir Definições →")
        banner_btn.setFixedHeight(28)
        banner_btn.setStyleSheet("""
            QPushButton {
                background: #554400;
                color: #ffcc00;
                border: 1px solid #776600;
                border-radius: 4px;
                padding: 0 10px;
                font-size: 11px;
            }
            QPushButton:hover { background: #665500; }
        """)
        banner_btn.clicked.connect(self._on_open_settings)

        banner_layout.addWidget(banner_lbl, stretch=1)
        banner_layout.addWidget(banner_btn)

        layout.addWidget(self._onboarding_banner)
        self._onboarding_banner.hide()  # Escondido por defeito
```

**Step 3: No `__init__` do `SearchView`, subscrever AppState após `self._build()`**

```python
        AppState.instance().spotify_status_changed.connect(self._on_spotify_status)
        # Estado inicial
        if not self._config.get("spotify", "client_id", default=""):
            self._onboarding_banner.show()
```

**Step 4: Adicionar os métodos `_on_spotify_status` e `_on_open_settings`**

```python
    def _on_spotify_status(self, connected: bool, username: str):
        if connected:
            self._onboarding_banner.hide()
        else:
            # Só mostra banner se não tiver credenciais configuradas
            if not self._config.get("spotify", "client_id", default=""):
                self._onboarding_banner.show()

    def _on_open_settings(self):
        # Emite sinal para MainWindow abrir settings
        # Usando parent chain
        parent = self.parent()
        while parent:
            if hasattr(parent, '_open_settings'):
                parent._open_settings()
                return
            parent = parent.parent()
```

**Step 5: Testar visualmente**

```bash
python main.py
```

Verificar:
- Se `client_id` vazio → banner amarelo visível na Search View
- Botão "Abrir Definições →" abre o diálogo
- Após configurar e conectar → banner desaparece

**Step 6: Commit**

```bash
git add ui/views/search_view.py
git commit -m "feat: onboarding banner in search view when spotify not configured"
```

---

## Task 6: Cancelar Downloads — Core

**Files:**
- Modify: `core/downloader.py`

**Step 1: Adicionar `_cancelled` set e thread lock no `__init__`**

Após `self._pool = ThreadPoolExecutor(...)`:
```python
        import threading
        self._cancelled: set[str] = set()
        self._cancel_lock = threading.Lock()
```

**Step 2: Adicionar métodos `cancel_track()` e `cancel_all_pending()`**

Após o método `shutdown()`:
```python
    def cancel_track(self, track_id: str) -> None:
        """Marca track para cancelamento. O worker para antes do próximo step."""
        with self._cancel_lock:
            self._cancelled.add(track_id)
        log.info(f"Track cancelada: {track_id}")

    def cancel_all_pending(self) -> None:
        """Cancela todas as tracks que ainda não começaram ou estão em progresso."""
        log.info("Cancelar todos os downloads pendentes")
        # Não podemos saber quais são pending sem tracking extra,
        # então usamos cancel_futures do pool para os não iniciados
        self._pool.shutdown(wait=False, cancel_futures=True)
        max_workers = self._config.get("download", "max_concurrent", default=2)
        self._pool = ThreadPoolExecutor(max_workers=max_workers)
        with self._cancel_lock:
            self._cancelled.clear()

    def is_cancelled(self, track_id: str) -> bool:
        with self._cancel_lock:
            return track_id in self._cancelled
```

**Step 3: Adicionar verificação de cancelamento no `_worker()`**

No início do método `_worker()`, após a linha `log.info(f"Worker iniciado:...")`:
```python
        track_id = track.get("id", "")
        if self.is_cancelled(track_id):
            log.info(f"Track já cancelada antes de começar: {title}")
            if done_cb:
                done_cb(DownloadResult(track, False, error="Cancelado"))
            return
```

Adicionar também uma verificação antes de `embed_metadata` (antes da linha `embed_metadata(result_path, track)`):
```python
            if self.is_cancelled(track_id):
                log.info(f"Track cancelada após download, antes de metadata: {title}")
                result_path.unlink(missing_ok=True)
                if done_cb:
                    done_cb(DownloadResult(track, False, error="Cancelado"))
                return
```

**Step 4: Verificar que downloader importa sem erros**

```bash
python -c "from core.downloader import Downloader; print('Downloader OK')"
```

Esperado: `Downloader OK`

**Step 5: Commit**

```bash
git add core/downloader.py
git commit -m "feat: add cancel_track and cancel_all_pending to Downloader"
```

---

## Task 7: Cancelar Downloads — UI

**Files:**
- Modify: `ui/views/queue_view.py`
- Modify: `ui/main_window.py`

**Step 1: Adicionar sinal `cancel_requested` ao `QueueItem`**

No `QueueItem`, adicionar sinal após a classe iniciar:
```python
class QueueItem(QFrame):
    cancel_requested = pyqtSignal(str)  # track_id
```

**Step 2: Adicionar botão `✕` no `_build()` do `QueueItem`**

Após `layout.addWidget(self._pct)`:
```python
        self._cancel_btn = QPushButton("✕")
        self._cancel_btn.setFixedSize(22, 22)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #666;
                border: none;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover { color: #E53935; background: #2a2a2a; }
        """)
        self._cancel_btn.clicked.connect(
            lambda: self.cancel_requested.emit(self.track.get("id", ""))
        )
        layout.addWidget(self._cancel_btn)
```

**Step 3: Esconder botão `✕` quando concluído ou falhado**

No `set_done()`, após `self._pct.setText("✓")`:
```python
        self._cancel_btn.hide()
```

No `set_failed()`, após `self._pct.setStyleSheet(...)`:
```python
        self._cancel_btn.hide()
```

Adicionar método `set_cancelled()`:
```python
    def set_cancelled(self):
        self._done = True
        self._timer.stop()
        self._icon.setText("–")
        self._icon.setStyleSheet("color: #888; font-size: 15px; background: transparent;")
        self._bar.setValue(0)
        self._pct.setText("–")
        self._pct.setStyleSheet("font-size: 11px; color: #888; background: transparent;")
        self._cancel_btn.hide()
```

**Step 4: Adicionar sinal `cancel_track` ao `QueueView` e botão "Cancelar tudo"**

Adicionar sinal na classe `QueueView`:
```python
class QueueView(QWidget):
    cancel_track = pyqtSignal(str)      # track_id
    cancel_all = pyqtSignal()
```

No `_build()` do `QueueView`, no bloco do header, após o `self._clear_btn`:
```python
        self._cancel_all_btn = QPushButton("✕  Cancelar tudo")
        self._cancel_all_btn.setObjectName("secondary")
        self._cancel_all_btn.setFixedHeight(32)
        self._cancel_all_btn.clicked.connect(self.cancel_all.emit)
        header.addWidget(self._cancel_all_btn)
```

**Step 5: Ao adicionar item na `add_item()`, conectar o sinal cancel**

No método `add_item()`, após `item = QueueItem(track)`:
```python
        item.cancel_requested.connect(self.cancel_track.emit)
```

**Step 6: Expor `set_cancelled()` a partir de `get_item()` — já existe, sem alteração**

**Step 7: Ligar sinais de cancelamento em `main_window.py`**

Em `_connect_signals()`, após os sinais de search/playlists/history existentes:
```python
        # Cancel signals
        self._queue_view.cancel_track.connect(self._on_cancel_track)
        self._queue_view.cancel_all.connect(self._on_cancel_all)
```

Adicionar os métodos em `MainWindow`:
```python
    def _on_cancel_track(self, track_id: str):
        if self._downloader:
            self._downloader.cancel_track(track_id)
        item = self._queue_view.get_item(track_id)
        if item:
            item.set_cancelled()
        if self._pending_dl > 0:
            self._pending_dl -= 1
        self._bottom_bar.update_stats(
            self._done_count, self._fail_count,
            self._pending_dl, self._total_dl
        )

    def _on_cancel_all(self):
        if self._downloader:
            self._downloader.cancel_all_pending()
        # Marcar todos os itens não concluídos como cancelados
        for tid, item in self._queue_view._items.items():
            if not item._done and not item._failed:
                item.set_cancelled()
        self._pending_dl = 0
        self._bottom_bar.update_stats(
            self._done_count, self._fail_count, 0, self._total_dl
        )
```

**Step 8: Testar visualmente**

```bash
python main.py
```

Verificar:
- Cada item na fila tem botão `✕` discreto à direita
- Click em `✕` → item mostra `–` (cancelado)
- Botão "Cancelar tudo" no header da view Downloads cancela todos os pendentes
- Botões `✕` somem após concluído/falhado

**Step 9: Commit**

```bash
git add ui/views/queue_view.py ui/main_window.py
git commit -m "feat: cancel individual and all downloads from queue view"
```

---

## Task 8: Loading Spinners

**Files:**
- Modify: `ui/views/search_view.py`
- Modify: `ui/views/playlists_view.py`

### SearchView

**Step 1: Adicionar `QProgressBar` indeterminado na `_build()` do `SearchView`**

Após `layout.addLayout(search_row)` (e após o banner de onboarding se já adicionado):
```python
        # Loading spinner (indeterminate progress bar)
        self._loading_bar = QProgressBar()
        self._loading_bar.setMinimum(0)
        self._loading_bar.setMaximum(0)  # modo indeterminado
        self._loading_bar.setFixedHeight(3)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #2a2a2a;
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background: {GREEN};
                border-radius: 1px;
            }}
        """)
        self._loading_bar.hide()
        layout.addWidget(self._loading_bar)
```

**Step 2: Mostrar/esconder spinner nos workers**

No `_load_url()`, após `self._status.setText("A carregar...")`:
```python
        self._loading_bar.show()
```

No `_search_text()`, após `self._status.setText(f"A pesquisar...")`:
```python
        self._loading_bar.show()
```

No `_on_tracks_loaded()`, após `self._search_btn.setText("Pesquisar")`:
```python
        self._loading_bar.hide()
```

No `_on_search_results()`, após `self._search_btn.setText("Pesquisar")`:
```python
        self._loading_bar.hide()
```

No `_on_error()`, após `self._search_btn.setText("Pesquisar")`:
```python
        self._loading_bar.hide()
```

### PlaylistsView

**Step 3: Adicionar `QProgressBar` na `_build()` do `PlaylistsView`**

Após `layout.addWidget(self._status)`:
```python
        self._loading_bar = QProgressBar()
        self._loading_bar.setMinimum(0)
        self._loading_bar.setMaximum(0)
        self._loading_bar.setFixedHeight(3)
        self._loading_bar.setTextVisible(False)
        self._loading_bar.setStyleSheet(f"""
            QProgressBar {{
                background: #2a2a2a;
                border: none;
                border-radius: 1px;
            }}
            QProgressBar::chunk {{
                background: {GREEN};
                border-radius: 1px;
            }}
        """)
        self._loading_bar.hide()
        layout.addWidget(self._loading_bar)
```

**Step 4: Mostrar/esconder nos métodos do `PlaylistsView`**

No `refresh()`, após `self._refresh_btn.setEnabled(False)`:
```python
        self._loading_bar.show()
```

No `_on_loaded()`, após `self._refresh_btn.setEnabled(True)`:
```python
        self._loading_bar.hide()
```

No `_on_error()`, após `self._refresh_btn.setEnabled(True)`:
```python
        self._loading_bar.hide()
```

**Step 5: Testar visualmente**

```bash
python main.py
```

Verificar:
- Barra verde animada aparece sob a search bar ao pesquisar/carregar
- Desaparece quando resultados chegam
- Mesma barra na view Playlists ao carregar

**Step 6: Commit**

```bash
git add ui/views/search_view.py ui/views/playlists_view.py
git commit -m "feat: indeterminate loading bar for search and playlists"
```

---

## Task 9: Windows Toast Notifications

**Files:**
- Modify: `requirements.txt`
- Modify: `ui/main_window.py`

**Step 1: Adicionar `winotify` às dependências**

Em `requirements.txt`, adicionar no final:
```
winotify>=1.1.0
```

**Step 2: Instalar**

```bash
pip install winotify
```

Esperado: `Successfully installed winotify-...`

**Step 3: Criar helper `_notify_batch_done()` em `main_window.py`**

Adicionar método em `MainWindow`:
```python
    def _notify_batch_done(self, done: int, fail: int):
        """Envia Windows toast notification quando batch termina."""
        try:
            from winotify import Notification, audio
            msg = f"{done} track{'s' if done != 1 else ''} concluída{'s' if done != 1 else ''}"
            if fail:
                msg += f"  ({fail} falhada{'s' if fail != 1 else ''})"
            toast = Notification(
                app_id="SONGER",
                title="Download concluído",
                msg=msg,
                duration="short",
            )
            toast.set_audio(audio.Default, loop=False)
            toast.show()
        except Exception:
            pass  # winotify não disponível ou erro — silencioso
```

**Step 4: Chamar `_notify_batch_done()` em `_on_done()`**

No `_on_done()`, dentro do bloco `if self._pending_dl == 0 and self._total_dl > 0:`, após guardar no histórico:
```python
            self._notify_batch_done(self._done_count, self._fail_count)
```

**Step 5: Testar**

```bash
python main.py
```

Verificar:
- Descarrega 1-2 tracks
- Quando acabam, aparece toast nativo do Windows no canto inferior direito
- Click no toast foca a janela (comportamento default do winotify)
- Se `winotify` não estiver instalado → nenhum crash, silencioso

**Step 6: Commit**

```bash
git add requirements.txt ui/main_window.py
git commit -m "feat: windows toast notification when download batch completes"
```

---

## Task 10: Actualizar Docs

**Files:**
- Modify: `docs/audit.md`
- Modify: `docs/changelog.md`

**Step 1: Em `docs/audit.md`, mover as 6 features para "IMPLEMENTADAS"**

Features a mover de `❌` para `✅`:
- [x] Badge estado Spotify na sidebar
- [x] Onboarding primeiro uso (banner + auto-open settings)
- [x] Notificação Windows toast ao concluir batch
- [x] Cancelar download individual (botão ✕ na fila)
- [x] Cancelar todos os downloads (botão "Cancelar tudo")
- [x] Loading spinners indeterminados (Search + Playlists)

**Step 2: Em `docs/changelog.md`, adicionar secção v1.1.0**

```markdown
## v1.1.0 — UX Polish (2026-03-02)
### Adicionado
- AppState singleton (core/app_state.py) para estado global partilhado
- Badge ● verde/vermelho junto ao logo SONGER indicando estado Spotify
- Banner de onboarding na Search View quando Spotify não configurado
- Barra de loading indeterminada ao pesquisar/carregar playlists
- Botão ✕ em cada item da fila para cancelar download individual
- Botão "Cancelar tudo" no header da view Downloads
- Windows toast notification quando batch de downloads termina
```

**Step 3: Commit**

```bash
git add docs/audit.md docs/changelog.md
git commit -m "docs: update audit and changelog for v1.1.0 ux polish"
```

---

## Resumo de Ficheiros Alterados

| Ficheiro | Tipo | Razão |
|---------|------|-------|
| `core/app_state.py` | Criar | Singleton AppState |
| `core/spotify.py` | Modificar | Emitir AppState em connect/disconnect |
| `core/downloader.py` | Modificar | cancel_track, cancel_all_pending |
| `ui/main_window.py` | Modificar | Init AppState, startup check, cancelar, toast |
| `ui/widgets/sidebar.py` | Modificar | Badge Spotify |
| `ui/views/search_view.py` | Modificar | Banner onboarding + loading bar |
| `ui/views/playlists_view.py` | Modificar | Loading bar |
| `ui/views/queue_view.py` | Modificar | Botões cancelar |
| `requirements.txt` | Modificar | + winotify |
| `docs/audit.md` | Modificar | Marcar features concluídas |
| `docs/changelog.md` | Modificar | Adicionar v1.1.0 |

**Total: 10 tasks, ~11 commits**
