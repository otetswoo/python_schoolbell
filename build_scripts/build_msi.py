#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build script for creating MSI installer on Windows.
Uses cx_Freeze to create executable and WiX/Heat for MSI package.
"""

import sys
import os
from pathlib import Path

from cx_Freeze import setup, Executable

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.absolute()

# Build version from git or use default
try:
    import subprocess
    version_output = subprocess.check_output(['git', 'describe', '--tags', '--always'], 
                                     stderr=subprocess.DEVNULL).decode().strip()
    # Convert git describe output to valid version (e.g., "1.0.0-5-g9cd1587" -> "1.0.0.5")
    if '-' in version_output:
        parts = version_output.split('-')
        if len(parts) >= 3 and parts[0].startswith('v'):
            version = f"{parts[0][1:]}.{parts[1]}"  # v1.0.0-5 -> 1.0.0.5
        else:
            version = "1.0.0"
    else:
        # Short commit hash like "9cd1587" - convert to date-based version
        version = f"0.0.{len(version_output)}"  # Simple fallback
except:
    version = "1.0.0"

# Dependencies are automatically detected, but some modules need help
build_exe_options = {
    "packages": [
        "PySide6",
        "yaml",
        "src",
        "src.config",
        "src.config_manager",
        "src.sound_player",
        "src.music_player",
        "src.lesson_dialog",
        "src.music_settings_dialog",
        "src.schedule_editor_dialog",
        "src.gui",
        "src.gui.localization",
        "src.event_logger",
        "src.volume_control",
    ],
    "include_files": [
        (os.path.join(ROOT_DIR, "sounds/"), "sounds/"),
        (os.path.join(ROOT_DIR, "schedule.yml"), "schedule.yml"),
        (os.path.join(ROOT_DIR, "preferences.yml"), "preferences.yml"),
        (os.path.join(ROOT_DIR, "README.md"), "README.md"),
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "email",
        "http",
        "xml",
        "pydoc",
    ],
    "optimize": 2,
}

# GUI applications require different base on Windows
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="School Bell",
    version=version,
    description="School Bell Automation System / Автоматизация школьных звонков",
    author="otetswoo",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            os.path.join(ROOT_DIR, "school_bell.py"),
            base=base,
            target_name="SchoolBell.exe",
            icon=None,  # Add your icon path here: icon="icon.ico"
            shortcut_name="School Bell",
            shortcut_dir="DesktopFolder",
        )
    ],
)
