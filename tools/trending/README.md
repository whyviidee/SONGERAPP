# Trending Tracks Fetcher

Script que vai buscar tracks trending por género ao Spotify e SoundCloud e gera os `.md` usados pela view Trending do SONGER.

## Requisitos

Credenciais Spotify em `~/.songer/config.json`:
```json
{
  "spotify": {
    "client_id": "...",
    "client_secret": "..."
  }
}
```

Dependências (já incluídas no `requirements.txt` do SONGER):
- `spotipy`
- `requests`

## Como correr

```bash
python tools/trending/fetch.py
```

Os ficheiros `.md` são gerados na mesma pasta (`tools/trending/`).

## Géneros gerados

| Ficheiro | Fonte |
|---|---|
| `portugal-top50.md` | Spotify |
| `funk-brasil.md` | Spotify |
| `reggaeton.md` | Spotify |
| `house.md` | Spotify |
| `amapiano.md` | Spotify |
| `afro-house-electronic.md` | SoundCloud |
| `afro-house-african.md` | SoundCloud |
| `underground-remixes.md` | SoundCloud |
