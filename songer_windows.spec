# PyInstaller spec -- Windows
import os
block_cipher = None

_version = open('VERSION').read().strip()

_datas = [
    ('VERSION', '.'),
    ('frontend/dist', 'frontend/dist'),
    ('web', 'web'),
    ('tools/trending', 'tools/trending'),
]
if os.path.exists('assets/logo.png'):
    _datas.append(('assets/logo.png', 'assets'))

a = Analysis(
    ['songer.py'],
    pathex=['.'],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'flask', 'webview',
        'spotipy', 'spotipy.oauth2',
        'mutagen', 'mutagen.id3', 'mutagen.flac', 'mutagen.mp3',
        'yt_dlp', 'imageio_ffmpeg', 'requests',
        'core.config', 'core.spotify', 'core.youtube', 'core.ytdlp',
        'core.soulseek', 'core.downloader', 'core.metadata',
        'core.matcher', 'core.library', 'core.history',
        'core.ffmpeg_manager', 'core.logger', 'core.app_state',
    ],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PyQt6'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='SONGER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='assets/icon.ico',
    version_file=None,
)
