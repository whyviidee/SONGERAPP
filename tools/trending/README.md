# Trending Tracks Fetcher

Script que vai buscar tracks trending por género ao Spotify e SoundCloud e gera os `.md` usados pela view Trending do SONGER.

> **Nota:** os ficheiros `.md` gerados estão no `.gitignore`. Depois de clonar o repo tens de correr este script manualmente para os gerar.

## Setup (primeira vez)

### 1. Configurar credenciais Spotify

Cria o ficheiro `~/.songer/config.json` (pasta home do teu sistema):

```json
{
  "spotify": {
    "client_id": "SEU_CLIENT_ID",
    "client_secret": "SEU_CLIENT_SECRET"
  }
}
```

Para obter as credenciais: [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) → criar app → copiar Client ID e Client Secret.

### 2. Instalar dependências

Activar o venv do SONGER e instalar:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Instalar (já no requirements.txt)
pip install spotipy requests
```

### 3. Correr o script

Da raiz do SONGER:

```bash
python tools/trending/fetch.py
```

Gera os `.md` em `tools/trending/`. Demora ~30s (faz requests ao Spotify e SoundCloud).

## Actualizar

Correr de novo sempre que quiseres dados frescos. O SONGER lê os `.md` em tempo real — não é preciso reiniciar.

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
