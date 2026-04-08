#!/bin/bash
# Arranque rápido para desenvolvimento — sem build, sem assinatura
cd "$(dirname "$0")"

VENV=".venv-arm64"
QT_PLUGINS="$VENV/lib/python3.13/site-packages/PyQt6/Qt6/plugins"

export QT_QPA_PLATFORM_PLUGIN_PATH="$QT_PLUGINS/platforms"
export DYLD_FRAMEWORK_PATH="$VENV/lib/python3.13/site-packages/PyQt6/Qt6/lib"

exec "$VENV/bin/python" main.py "$@"
