# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

# SPECPATH is provided by PyInstaller and points to this spec's directory.
PROJECT_ROOT = Path(SPECPATH).resolve()

hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtNetwork',
    'PySide6.QtSvg',
    'PySide6.QtOpenGL',
    'yaml',
    'src',
    'src.config',
    'src.config_manager',
    'src.sound_player',
    'src.music_player',
    'src.lesson_dialog',
    'src.music_settings_dialog',
    'src.bell_settings_dialog',
    'src.schedule_editor_dialog',
    'src.templates_dialog',
    'src.announcement_settings_dialog',
    'src.anthem_settings_dialog',
    'src.holiday_settings_dialog',
    'src.gui',
    'src.gui.localization',
    'src.event_logger',
    'src.volume_control',
    'src.log_viewer_dialog',
]

# Only read-only application resources belong here. User settings
# (preferences.yml), logs and music libraries must never be bundled.
datas = [
    (str(PROJECT_ROOT / 'sounds'), 'sounds'),
    (str(PROJECT_ROOT / 'schedule.yml'), '.'),
    (str(PROJECT_ROOT / 'src' / 'school_bell.png'), 'src'),
]

excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'PIL',
    'unittest',
    'email',
    'http',
    'xml',
    'pydoc',
    'PySide6.QtWebEngineCore',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick',
    'PySide6.QtQuick',
    'PySide6.QtQml',
]

a = Analysis(
    [str(PROJECT_ROOT / 'school_bell.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='school-bell',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'src' / 'school_bell.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='school-bell',
)
