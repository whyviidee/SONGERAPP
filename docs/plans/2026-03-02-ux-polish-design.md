# SONGER — UX Polish Cycle Design

> Data: 2026-03-02
> Abordagem: Foundation First
> Estado: Aprovado

---

## Objectivo

Tornar a app SONGER sentir-se "pronta" e profissional — feedback visual claro, onboarding funcional, controlo de downloads, e indicadores de estado.

## Scope

5 features neste ciclo:
1. AppState Central
2. Badge Spotify na Sidebar
3. Onboarding no primeiro uso
4. Notificação de download concluído (Windows toast)
5. Cancelar downloads (individual + todos)
6. Loading spinners (Search + Playlists)

---

## 1. AppState Central (`core/app_state.py`)

Singleton `QObject` com sinais Qt partilhados por toda a app.

```python
class AppState(QObject):
    spotify_status_changed = pyqtSignal(bool, str)  # (conectado, username)
    download_stats_changed = pyqtSignal(int, int, int)  # (done, fail, pending)

    _instance = None

    @classmethod
    def instance(cls) -> "AppState": ...

    def set_spotify_connected(self, connected: bool, username: str = ""): ...
    def update_download_stats(self, done: int, fail: int, pending: int): ...
```

**Integração:**
- `spotify.py` → chama `AppState.instance().set_spotify_connected(...)` após auth/logout
- `downloader.py` → chama `AppState.instance().update_download_stats(...)` em cada update
- Widgets → subscrevem via `app_state.spotify_status_changed.connect(...)`

**Regra:** não quebra código existente — aditivo puro.

---

## 2. Badge Spotify na Sidebar

**Localização:** `ui/widgets/sidebar.py` — header com logo SONGER

**Visual:**
```
S O N G E R  ●
             └── verde (#1DB954) = conectado
                 vermelho (#E53935) = desconectado
                 cinza = a verificar
```

**Comportamento:**
- Subscreve `app_state.spotify_status_changed`
- Tooltip: `"Spotify: conectado — username"` ou `"Spotify: desconectado — clica para configurar"`
- Click no badge → emite sinal para navegar para Definições

---

## 3. Onboarding Primeiro Uso

**Localização:** `ui/main_window.py` — `on_startup()`

**Fluxo:**
```
App inicia
  └── config.spotify_client_id vazio?
        ├── SIM → abre SettingsDialog (focus tab Spotify) + mostra banner na SearchView
        └── NÃO → tenta refresh token Spotify → emite spotify_status_changed
```

**Banner na SearchView** (quando sem Spotify):
```
┌─────────────────────────────────────────────────┐
│ ⚠ Spotify não configurado  [Abrir Definições →] │
└─────────────────────────────────────────────────┘
```
- Banner desaparece automaticamente quando `spotify_status_changed(True, ...)` for emitido

---

## 4. Notificação Windows Toast

**Biblioteca:** `winotify` (leve, sem dependências pesadas)

**Trigger:** `downloader.py` — quando `pending == 0` e batch tinha > 0 tracks

**Mensagem:**
```
SONGER
✓ 12 tracks concluídas (1 falhada)
```

**Click na notificação:** foca janela + navega para Downloads view

**Fallback:** se `winotify` não instalado → não crashar, silenciosamente ignorar (notificação é nice-to-have)

---

## 5. Cancelar Downloads

**`core/downloader.py`:**
```python
self._cancelled: Set[str] = set()

def cancel_track(self, track_id: str): ...    # cancela uma track
def cancel_all_pending(self): ...             # cancela todos os pending
```

Worker verifica `track_id in self._cancelled` antes de cada step major (search, download, metadata).

**`ui/views/queue_view.py`:**
- Cada row: botão `✕` que chama `downloader.cancel_track(id)`
- Header da view: botão "Limpar fila" que chama `downloader.cancel_all_pending()`
- Status visual da track: `pending → cancelado` (cor cinza, texto "Cancelado")

**Nota:** tracks `in_progress` terminam o step actual antes de parar — sem kills abruptos de threads.

---

## 6. Loading Spinners

**SearchView** (`ui/views/search_view.py`):
- Ao iniciar search/load URL → mostra `QProgressBar` indeterminado no topo da lista
- Remove quando resultados chegam (ou erro)

**PlaylistsView** (`ui/views/playlists_view.py`):
- Ao carregar tracks de playlist → spinner centralizado na área de tracks

**Implementação:** `QProgressBar(minimum=0, maximum=0)` — modo indeterminado nativo PyQt6, zero dependências extras.

---

## Ordem de Implementação

1. `core/app_state.py` — base para tudo
2. Integrar AppState em `spotify.py` + `downloader.py`
3. Badge Spotify na Sidebar
4. Onboarding + Banner SearchView
5. Cancelar downloads (core + UI)
6. Loading spinners
7. Windows toast notifications
8. Actualizar `docs/audit.md` e `docs/changelog.md`

---

## Dependências Novas

| Package | Versão | Motivo |
|---------|--------|--------|
| `winotify` | `>=1.1.0` | Windows toast notifications |

Sem outras dependências novas.

---

## O que NÃO está no scope

- Reprodutor integrado na Biblioteca
- Filtros na biblioteca
- Tray icon
- Testes automatizados
- Auto-updater
