# PyInstaller spec — macOS (Liquid Redesign)
import os
block_cipher = None

# Read version from VERSION file
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
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'PyQt6', 'winotify'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='SONGER',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name='SONGER')

app = BUNDLE(
    coll,
    name='SONGER.app',
    icon='assets/icon.icns',
    bundle_identifier='com.songer.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': _version,
    },
)
