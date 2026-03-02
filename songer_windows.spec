# PyInstaller spec — Windows
# Uso: pyinstaller songer_windows.spec

import os
block_cipher = None

_datas = [('assets/icon.ico', 'assets')]
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
        'ui.views.home_view',
        'ui.views.search_view',
        'ui.views.playlists_view',
        'ui.views.queue_view',
        'ui.views.library_view',
        'ui.views.history_view',
        'ui.about_dialog',
        'ui.splash',
        'ui.disclaimer_dialog',
        'winotify',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SONGER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,              # UPX desactivado — reduz falsos positivos no Defender
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version='file_version_info.txt',
)
