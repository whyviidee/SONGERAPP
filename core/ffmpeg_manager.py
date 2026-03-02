"""
ffmpeg_manager.py
Usa imageio-ffmpeg para obter o binário do ffmpeg.
Copia-o para ~/.songer/tools/ffmpeg.exe para que o yt-dlp o encontre pelo nome certo.
"""

import shutil
from pathlib import Path

import sys

from core.logger import get_logger

log = get_logger("ffmpeg")

FFMPEG_DIR = Path.home() / ".songer" / "tools"
# macOS/Linux: sem .exe
FFMPEG_EXE = FFMPEG_DIR / ("ffmpeg.exe" if sys.platform == "win32" else "ffmpeg")


def _ensure_ffmpeg_copied() -> bool:
    """Copia o ffmpeg do imageio-ffmpeg para ~/.songer/tools/ffmpeg.exe se não existir."""
    if FFMPEG_EXE.exists():
        size = FFMPEG_EXE.stat().st_size
        log.debug(f"ffmpeg.exe já existe em {FFMPEG_EXE} ({size:,} bytes)")
        if size < 1_000_000:
            log.warning(f"ffmpeg.exe parece corrompido ({size} bytes). A re-copiar...")
            FFMPEG_EXE.unlink()
        else:
            return True

    try:
        import imageio_ffmpeg
        src_path = imageio_ffmpeg.get_ffmpeg_exe()
        log.info(f"imageio-ffmpeg fonte: {src_path}")
        src = Path(src_path)

        if not src.exists():
            log.error(f"Binário imageio-ffmpeg não encontrado: {src}")
            return False

        src_size = src.stat().st_size
        log.info(f"A copiar ffmpeg ({src_size:,} bytes) → {FFMPEG_EXE}")
        FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, FFMPEG_EXE)

        if FFMPEG_EXE.exists():
            log.info(f"ffmpeg copiado com sucesso: {FFMPEG_EXE}")
            return True
        else:
            log.error("Cópia falhou — ficheiro não existe após copy2")
            return False

    except ImportError:
        log.error("imageio-ffmpeg não está instalado")
        return False
    except Exception as e:
        log.error(f"Erro ao copiar ffmpeg: {e}", exc_info=True)
        return False


def get_ffmpeg_path() -> str:
    """
    Devolve o diretório com o ffmpeg.exe para passar ao yt-dlp.
    Retorna string vazia se não encontrar (yt-dlp usa o PATH do sistema).
    """
    if _ensure_ffmpeg_copied():
        log.debug(f"Usando ffmpeg em: {FFMPEG_DIR}")
        return str(FFMPEG_DIR)

    # Fallback: sistema
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        log.info(f"Usando ffmpeg do sistema: {sys_ffmpeg}")
        return ""

    log.warning("ffmpeg NÃO encontrado — downloads sem conversão de formato")
    return ""


def ffmpeg_available() -> bool:
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        log.debug(f"ffmpeg_available=True via imageio-ffmpeg: {path}")
        return True
    except Exception:
        result = bool(shutil.which("ffmpeg"))
        log.debug(f"ffmpeg_available={result} via PATH")
        return result
