#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Version of the application
VERSION = "1.0.5"

IS_FROZEN = getattr(sys, "frozen", False)

# Handle PyInstaller frozen application paths
if IS_FROZEN:
    # Running as compiled executable (PyInstaller onedir/onefile)
    ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
else:
    # Running as a script from the project tree
    ROOT = Path(__file__).resolve().parent.parent

# Read-only bundled resources (sounds, default schedule, icon).
RESOURCE_ROOT = ROOT
DEFAULT_SCHEDULE_PATH = RESOURCE_ROOT / "schedule.yml"
SOUNDS_DIR = RESOURCE_ROOT / "sounds"

# Writable user data. Installed packages and AppImage must never write
# settings next to read-only application resources.
INSTALLED = IS_FROZEN or str(ROOT).startswith(("/usr/lib", "/usr/share", "/opt"))
if INSTALLED:
    xdg_data_home = os.environ.get("XDG_DATA_HOME", "")
    if xdg_data_home and os.path.isabs(xdg_data_home):
        DATA_ROOT = Path(xdg_data_home) / "school-bell"
    else:
        DATA_ROOT = Path.home() / ".local" / "share" / "school-bell"
    MUSIC_DIR = DATA_ROOT / "music"
    LOGS_DIR = DATA_ROOT / "logs"
    PREFERENCES_FILE = DATA_ROOT / "preferences.yml"
    SCHEDULE_PATH = DATA_ROOT / "schedule.yml"
else:
    # Development/standalone mode - use local directories
    DATA_ROOT = ROOT
    MUSIC_DIR = ROOT / "music"
    LOGS_DIR = ROOT / "logs"
    PREFERENCES_FILE = ROOT / "preferences.yml"
    SCHEDULE_PATH = ROOT / "schedule.yml"

WEEK_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEK_DAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
WEEK_DAYS_SHORT = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
WEEK_DAYS_SHORT_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

BREAK_DURATIONS = [5, 10, 15, 20, 25, 30]

DEFAULT_SCHEDULE = {
    "days": {
        "monday": "usual", "tuesday": "usual", "wednesday": "usual",
        "thursday": "usual", "friday": "usual", "saturday": "none", "sunday": "none"
    },
    "schedules": {
        "usual": [
            {"num": 1, "start": "08:30", "end": "09:10"},
            {"num": 2, "start": "09:20", "end": "10:00"},
            {"num": 3, "start": "10:15", "end": "10:55"},
            {"num": 4, "start": "11:10", "end": "11:50"},
            {"num": 5, "start": "12:10", "end": "12:50"},
            {"num": 6, "start": "13:10", "end": "13:50"},
            {"num": 7, "start": "14:00", "end": "14:40"},
            {"num": 8, "start": "14:50", "end": "15:30"},
            {"num": 9, "start": "15:40", "end": "16:20"},
            {"num": 10, "start": "16:30", "end": "17:10"},
        ],
        "short": [
            {"num": 1, "start": "08:30", "end": "09:00"},
            {"num": 2, "start": "09:05", "end": "09:35"},
            {"num": 3, "start": "09:40", "end": "10:10"},
            {"num": 4, "start": "10:15", "end": "10:45"},
            {"num": 5, "start": "10:50", "end": "11:20"},
            {"num": 6, "start": "11:25", "end": "11:55"},
            {"num": 7, "start": "12:00", "end": "12:30"},
        ],
        "none": []
    },
    "sounds": {
        "start": str(SOUNDS_DIR / "Ringin.wav"),
        "end": str(SOUNDS_DIR / "Ringinout.wav")
    },
    "music": {
        "enabled": False,
        "folder": str(MUSIC_DIR),
        "delay_minutes": 2
    },
    "volumes": {
        "start": 100,
        "end": 100,
        "anthem": 100,
        "announcement": 100,
        "music": 50
    }
}


def ensure_dirs():
    for d in [MUSIC_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    # SOUNDS_DIR is read-only in system installation, don't try to create it
