# PyInstaller spec — macOS
# Uso: pyinstaller songer_mac.spec

import os
block_cipher = None

_datas = []
if os.path.exists('assets/logo.png'):
    _datas.append(('assets/logo.png', 'assets'))

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'spotipy',
        'spotipy.oauth2',
        'mutagen',
        'mutagen.id3',
        'mutagen.flac',
        'mutagen.oggvorbis',
        'mutagen.mp3',
        'yt_dlp',
        'imageio_ffmpeg',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtMultimedia',
        'PyQt6.QtNetwork',
        'core.logger',
        'core.config',
        'core.app_state',
        'core.spotify',
        'core.youtube',
        'core.downloader',
        'core.ffmpeg_manager',
        'core.history',
        'core.library',
        'core.metadata',
        'core.matcher',
        'core.soulseek',
        'ui.theme',
        'ui.main_window',
        'ui.settings_dialog',
        'ui.ffmpeg_dialog',
        'ui.widgets.sidebar',
        'ui.widgets.track_list',
        'ui.widgets.album_header',
        'ui.widgets.bottom_bar',
        'ui.views.search_view',
        'ui.views.playlists_view',
        'ui.views.queue_view',
        'ui.views.library_view',
        'ui.views.history_view',
        'ui.views.home_view',
        'ui.about_dialog',
        'ui.splash',
        'ui.disclaimer_dialog',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SONGER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    argv_emulation=True,    # Importante no macOS
    target_arch='arm64',    # Apple Silicon (M1/M2/M3)
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Mete 'assets/icon.icns' quando tiveres o icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SONGER',
)

app = BUNDLE(
    coll,
    name='SONGER.app',
    icon=None,
    bundle_identifier='com.songer.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleShortVersionString': '1.0.0',
    },
)
