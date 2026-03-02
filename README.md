# SONGER

Download música do Spotify via YouTube e Soulseek. Corre no browser — sem instalação de app.

---

## Requisitos

- **Python 3.11+**
- **pip**
- Conta **Spotify** gratuita (para ligar à biblioteca)
- Credenciais da **Spotify Developer App** (gratuito, ~5 minutos de setup)

---

## Instalação

```bash
# 1. Clona o repositório
git clone https://github.com/whyviidee/SONGERAPP.git
cd SONGERAPP

# 2. Cria ambiente virtual (recomendado)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Instala dependências
pip install -r requirements.txt
```

---

## Iniciar

```bash
python server.py
```

Abre o browser em **http://localhost:8888**

---

## Setup inicial (primeira vez)

### 1. Credenciais Spotify

Ao abrir o SONGER pela primeira vez, é pedido o **Client ID** e **Client Secret** do Spotify.

Para os obter:

1. Vai a [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) e faz login com a tua conta Spotify
2. Clica **"Create app"**
3. Preenche nome e descrição (qualquer coisa serve)
4. Em **"Redirect URIs"** adiciona exactamente: `http://127.0.0.1:8888/callback`
5. Selecciona **"Web API"** em APIs used e guarda
6. Na página da app → **Settings** → copia o **Client ID** e o **Client Secret**
7. Cola no SONGER e clica **"Ligar ao Spotify"**
8. Faz login na janela que abre e autoriza o acesso

### 2. Pasta de downloads e formato

Depois do Spotify ligado, define:
- **Pasta** onde a música vai ser guardada (ex: `C:\Users\Tu\Music\SONGER`)
- **Formato** — MP3 320kbps é o recomendado para uso geral

> **Nota sobre FLAC:** Se escolheres FLAC com fonte YouTube, o ficheiro é convertido
> de áudio lossy — não é lossless real. Para FLAC verdadeiro (de CD) precisas do
> Soulseek. Ver **Help & FAQ** dentro da app.

---

## Funcionalidades

| Feature | Descrição |
|---|---|
| **Search** | Pesquisa músicas, álbuns e artistas no Spotify |
| **Playlists** | Vê e descarrega as tuas playlists (individual ou ZIP) |
| **Liked Songs** | Acesso directo às tuas músicas guardadas |
| **Downloads** | Fila de downloads em tempo real com progresso |
| **Library** | Biblioteca local das músicas já descarregadas |
| **History** | Histórico completo de downloads |
| **Help & FAQ** | Respostas a todas as dúvidas + aviso legal |

---

## Fontes de download

| Fonte | Qualidade | Requisitos |
|---|---|---|
| **YouTube** | Até 256kbps Opus/AAC | Só internet |
| **Soulseek** | FLAC lossless de CD | Conta Soulseek + slskd |
| **Hybrid** (recomendado) | Soulseek primeiro, YouTube como fallback | Conta Soulseek + slskd |

### Configurar Soulseek (opcional)

Para acesso a FLAC verdadeiro:

1. Cria conta gratuita em [slsknet.org](https://www.slsknet.org/news/node/1)
2. Instala o **slskd** — daemon Soulseek com API REST:
   - Download em [github.com/slskd/slskd/releases](https://github.com/slskd/slskd/releases)
   - Ou via Docker: `docker run -d --name slskd -p 5030:5030 -p 50300:50300 slskd/slskd`
3. Inicia o slskd e configura com o teu username/password Soulseek em `http://localhost:5030`
4. No SONGER → **Settings** → define slskd URL (`http://localhost:5030`) e muda Source para **Hybrid**

---

## Ficheiros de configuração

Tudo fica guardado localmente no teu computador:

| Ficheiro | Conteúdo |
|---|---|
| `~/.songer/config.json` | Configurações (pasta, formato, source) |
| `~/.songer/.spotify_token.json` | Token OAuth Spotify (renovado automaticamente) |
| `~/.songer/history.json` | Histórico de downloads |
| `~/.songer/songer.log` | Logs da aplicação |

---

## Estrutura do projecto

```
SONGER/
├── server.py              # Servidor Flask (entry point web)
├── main.py                # Entry point app desktop (PyQt6)
├── requirements.txt
├── core/
│   ├── spotify.py         # Cliente Spotify (OAuth2, playlists, liked songs)
│   ├── youtube.py         # yt-dlp wrapper (download + conversão ffmpeg)
│   ├── soulseek.py        # slskd REST client
│   ├── downloader.py      # Orquestrador de downloads (ThreadPool)
│   ├── metadata.py        # Tags ID3/FLAC + cover art
│   ├── library.py         # Scan biblioteca local
│   ├── history.py         # Histórico JSON
│   └── ffmpeg_manager.py  # ffmpeg bundled via imageio-ffmpeg
└── web/
    ├── app.html           # SPA principal
    └── static/
        ├── css/app.css
        └── js/
            ├── app.js
            ├── api.js
            ├── player.js
            └── views/     # home, search, playlists, liked, queue, library, history, faq
```

---

## Aviso Legal

O SONGER é uma ferramenta pessoal de código aberto. O utilizador é inteiramente responsável
pelo uso que faz do software e pelo cumprimento das leis de direitos de autor do seu país.
Os criadores do SONGER não têm qualquer responsabilidade por acções legais decorrentes
do uso desta ferramenta. **Use de forma responsável.**
