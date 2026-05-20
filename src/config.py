#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path

# Version of the application
VERSION = "1.0.0"

# Handle PyInstaller frozen application paths
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_PATH = Path(sys._MEIPASS)
else:
    # Running as script
    BASE_PATH = Path(__file__).resolve().parent.parent

ROOT = BASE_PATH

SCHEDULE_PATH = ROOT / "schedule.yml"
PREFERENCES_FILE = ROOT / "preferences.yml"
SOUNDS_DIR = ROOT / "sounds"

# For installed system packages, use user-writable directories for data
# Check if running from system installation path
if str(ROOT).startswith("/usr/lib"):
    # System installation - use user data directories
    HOME = Path.home()
    DATA_ROOT = HOME / ".local" / "share" / "school-bell"
    MUSIC_DIR = DATA_ROOT / "music"
    LOGS_DIR = DATA_ROOT / "logs"
    # For preferences and schedule in system install, also use user directory
    PREFERENCES_FILE = DATA_ROOT / "preferences.yml"
    SCHEDULE_PATH = DATA_ROOT / "schedule.yml"
else:
    # Development/standalone mode - use local directories
    MUSIC_DIR = ROOT / "music"
    LOGS_DIR = ROOT / "logs"

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
    "announcement": {
        "enabled": False,
        "file": "",
        "date": "",
        "time": "08:30",
        "played": False
    },
    "holidays": [],
    "profiles": {
        "default": {
            "name": "Стандартное"
        }
    },
    "current_profile": "default",
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
