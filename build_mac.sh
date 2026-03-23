#!/bin/bash
set -e
echo "=== SONGER 2.0 — Build macOS ==="
echo ""

cd "$(dirname "$0")"

# Build React frontend
echo "→ Building frontend..."
cd frontend && npm run build && cd ..

# Install Python deps
echo "→ Installing Python dependencies..."
pip3 install --upgrade pyinstaller pywebview flask spotipy yt-dlp mutagen imageio-ffmpeg requests

# Build Mac app
echo "→ Building .app..."
python3 -m PyInstaller songer_mac.spec --clean --noconfirm

echo ""
echo "=== Done! ==="
echo "App: dist/SONGER.app"
echo "Run: open dist/SONGER.app"
