# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define hidden imports for PySide6 and other modules
hiddenimports = [
    'PySide6.QtMultimedia',
    'PySide6.QtMultimediaWidgets',
    'PySide6.QtSvg',
    'PySide6.QtOpenGL',
    'yaml',
    'pathlib',
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
    'src.profiles_dialog',
    'src.announcement_settings_dialog',
    'src.anthem_settings_dialog',
    'src.gui',
    'src.gui.localization',
    'src.event_logger',
    'src.volume_control',
    'src.log_viewer_dialog',
]

# Data files to include
datas = [
    ('sounds', 'sounds'),
    ('schedule.yml', 'schedule.yml'),
    ('preferences.yml', 'preferences.yml'),
]

# Exclude unnecessary modules
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
]

# Version info for Windows
version_info = {
    'FixedFileVersion': '1.0.0.0',
    'ProductVersion': '1.0.0.0',
    'CompanyName': 'otetswoo',
    'FileDescription': 'School Bell Automation System',
    'LegalCopyright': 'MIT License',
    'ProductName': 'School Bell',
    'InternalName': 'school-bell',
}

a = Analysis(
    ['school_bell.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='school-bell',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application - no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/school_bell.png',
)
