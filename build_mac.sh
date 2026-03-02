#!/bin/bash
# SONGER — Build script para macOS
# Uso: bash build_mac.sh

set -e

echo "==================================="
echo "  SONGER — Build macOS"
echo "==================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instala com: brew install python@3.11"
    exit 1
fi

echo "✓ Python: $(python3 --version)"

# Instalar dependências
echo ""
echo "→ A instalar dependências..."
pip3 install --upgrade PyQt6 spotipy yt-dlp mutagen imageio-ffmpeg pyinstaller

# Build
echo ""
echo "→ A fazer build..."
cd "$(dirname "$0")"
python3 -m PyInstaller songer_mac.spec --clean --noconfirm

echo ""
echo "==================================="
echo "  ✓ Build concluído!"
echo "  App: dist/SONGER.app"
echo "==================================="
echo ""
echo "Para abrir: open dist/SONGER.app"
echo ""
echo "Se o macOS bloquear, vai a:"
echo "  Sistema → Privacidade → Abrir mesmo assim"
