"""
logger.py — Log para ~/.songer/songer.log
Usado por todos os módulos core para diagnóstico.
"""

import logging
import sys
from pathlib import Path

LOG_PATH = Path.home() / ".songer" / "songer.log"


def _setup() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("songer")
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)

    # Ficheiro de log
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    logger.addHandler(fh)

    # Console — só quando há terminal (dev mode)
    if sys.stdout and not getattr(sys, "frozen", False):
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(ch)

    return logger


log = _setup()


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"songer.{name}")
