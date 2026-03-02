#!/usr/bin/env python3
"""SONGER - Build script para macOS Apple Silicon (M1/M2/M3). Uso: python3 build_mac.py"""
import subprocess
import sys
import os
import platform

def run(cmd, check=True):
    print(f"\n> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"ERRO ao correr: {cmd}")
        sys.exit(1)
    return result.returncode == 0

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("===================================")
print("  SONGER - Build macOS")
print("===================================")

arch = platform.machine()
print(f"\nArquitectura: {arch}")

# Verificar se é Apple Silicon
is_apple_silicon = arch == "arm64"
if is_apple_silicon:
    print("Detected: Apple Silicon (M1/M2/M3)")
    python_cmd = "python3"
    pip_cmd = "pip3"
else:
    print("Detected: Intel Mac")
    python_cmd = "python3"
    pip_cmd = "pip3"

# Verificar se Python é arm64 nativo (não Rosetta)
if is_apple_silicon:
    result = subprocess.run("python3 -c \"import platform; print(platform.machine())\"",
                            shell=True, capture_output=True, text=True)
    py_arch = result.stdout.strip()
    if py_arch != "arm64":
        print(f"\n⚠ AVISO: Python a correr como {py_arch} (via Rosetta).")
        print("Instala Python nativo arm64 via Homebrew:")
        print("  brew install python@3.11")
        print("  /opt/homebrew/bin/python3.11 build_mac.py")
        sys.exit(1)
    print(f"Python architecture: {py_arch} OK")

print("\n-> A instalar dependencias...")
run(f"{pip_cmd} install --upgrade PyQt6 spotipy yt-dlp mutagen imageio-ffmpeg pyinstaller")

print("\n-> A fazer build (arm64)...")
run(f"{python_cmd} -m PyInstaller songer_mac.spec --clean --noconfirm")

print("\n-> A remover quarentena (permite abrir sem bloqueio de seguranca)...")
run("xattr -cr dist/SONGER.app", check=False)

print("\n===================================")
print("  Build concluido!")
print("  App: dist/SONGER.app")
print("===================================")
print("\nPara abrir: open dist/SONGER.app")
print("Ou arrasta SONGER.app para /Applications")
