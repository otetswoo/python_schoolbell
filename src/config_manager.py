#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy
from pathlib import Path
import datetime

import yaml

from src.config import DEFAULT_SCHEDULE, SCHEDULE_PATH, PREFERENCES_FILE, WEEK_DAYS


class ConfigManager:
    def __init__(self):
        self.schedule_data = None
        self.preferences = {}

    def load_schedule(self):
        if SCHEDULE_PATH.exists():
            try:
                with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
                    self.schedule_data = yaml.safe_load(f) or {}
                return True
            except Exception as e:
                print(f"Error loading schedule: {e}")
                self.schedule_data = deepcopy(DEFAULT_SCHEDULE)
                return False
        else:
            self.schedule_data = deepcopy(DEFAULT_SCHEDULE)
            return True

    def save_schedule(self, data, path=None):
        path = path or SCHEDULE_PATH
        try:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving schedule: {e}")
            return False

    def load_preferences(self):
        if Path(PREFERENCES_FILE).exists():
            try:
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    self.preferences = yaml.safe_load(f) or {}
                
                # Миграция старого формата объявлений в новый
                old = self.preferences.get("announcement")
                has_new = "announcements" in self.preferences and self.preferences["announcements"]

                if old and isinstance(old, dict) and not has_new:
                    # мигрируем только если новый список пустой или отсутствует
                    if old.get("file"):
                        self.preferences["announcements"] = [
                            {**old, "enabled": not old.get("played", False)}
                        ]
                    else:
                        self.preferences["announcements"] = []
                    del self.preferences["announcement"]
                elif "announcements" not in self.preferences:
                    self.preferences["announcements"] = []
                # Удаляем старый ключ если он есть и новый уже есть
                if "announcement" in self.preferences and "announcements" in self.preferences:
                    del self.preferences["announcement"]
                
                return True
            except Exception as e:
                print(f"Error loading preferences: {e}")
        self.preferences = {"announcements": []}
        return False

    def save_preferences(self, prefs):
        try:
            prefs["last_saved"] = datetime.datetime.now().isoformat()
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                yaml.dump(prefs, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False

    def get_day_variant(self, day_ru):
        return self.preferences.get("variants", {}).get(day_ru, "usual")

    def set_day_variant(self, day_ru, variant):
        if "variants" not in self.preferences:
            self.preferences["variants"] = {}
        self.preferences["variants"][day_ru] = variant

    def get_sounds(self):
        sounds = self.preferences.get("sounds", {})
        if not sounds:
            sounds = DEFAULT_SCHEDULE["sounds"].copy()
        return sounds

    def set_sound(self, sound_type, path):
        if "sounds" not in self.preferences:
            self.preferences["sounds"] = {}
        self.preferences["sounds"][sound_type] = path

    def get_music_settings(self):
        music = DEFAULT_SCHEDULE["music"].copy()
        music.update(self.preferences.get("music", {}))
        if "folders" not in music:
            folder = music.get("folder", "")
            music["folders"] = [folder] if folder else []
        if "selected_tracks" not in music:
            music["selected_tracks"] = []
        return music

    def set_music_folder(self, folder):
        self.set_music_folders([folder] if folder else [])

    def set_music_folders(self, folders):
        if "music" not in self.preferences:
            self.preferences["music"] = {}
        clean = [f for f in (folders or []) if f]
        self.preferences["music"]["folders"] = clean
        self.preferences["music"]["folder"] = clean[0] if clean else ""
        self.preferences["music"]["enabled"] = bool(clean)

    def get_anthem_settings(self):
        anthem = self.preferences.get("anthem", {})
        if not anthem:
            anthem = {"enabled": False, "file": "", "day": "monday", "time": "08:30"}
        return anthem

    def set_anthem_file(self, file_path):
        if "anthem" not in self.preferences:
            self.preferences["anthem"] = {}
        self.preferences["anthem"]["file"] = file_path

    def set_anthem_day(self, day):
        if "anthem" not in self.preferences:
            self.preferences["anthem"] = {}
        self.preferences["anthem"]["day"] = day

    def set_anthem_time(self, time_str):
        if "anthem" not in self.preferences:
            self.preferences["anthem"] = {}
        self.preferences["anthem"]["time"] = time_str

    def get_locale(self):
        return self.preferences.get("locale", "ru")

    def set_locale(self, locale):
        self.preferences["locale"] = locale

    # Методы для работы с профилями расписания
    def get_profiles(self):
        """Возвращает словарь профилей расписания"""
        if self.schedule_data and "profiles" in self.schedule_data:
            return self.schedule_data.get("profiles", {})
        return DEFAULT_SCHEDULE.get("profiles", {})

    def get_current_profile(self):
        """Возвращает имя текущего профиля"""
        if self.schedule_data:
            return self.schedule_data.get("current_profile", "default")
        return "default"

    def set_current_profile(self, profile_name):
        """Устанавливает текущий профиль"""
        if self.schedule_data is None:
            self.schedule_data = {}
        self.schedule_data["current_profile"] = profile_name

    def add_profile(self, profile_name, name_display, schedules):
        """Добавляет новый профиль расписания"""
        if self.schedule_data is None:
            self.schedule_data = {}
        if "profiles" not in self.schedule_data:
            self.schedule_data["profiles"] = {}
        self.schedule_data["profiles"][profile_name] = {
            "name": name_display,
            "schedules": schedules
        }

    def delete_profile(self, profile_name):
        """Удаляет профиль (кроме default)"""
        if profile_name == "default":
            return False
        if self.schedule_data and "profiles" in self.schedule_data:
            if profile_name in self.schedule_data["profiles"]:
                del self.schedule_data["profiles"][profile_name]
                return True
        return False

    def get_profile_schedules(self, profile_name):
        """Возвращает расписание для указанного профиля"""
        profiles = self.get_profiles()
        if profile_name in profiles:
            return profiles[profile_name].get("schedules", {})
        return {}

    # Методы для работы с громкостью
    def get_volumes(self):
        """Возвращает настройки громкости для разных типов звуков"""
        volumes = DEFAULT_SCHEDULE.get("volumes", {}).copy()
        volumes.update(self.preferences.get("volumes", {}))
        return volumes
    
    def set_volume(self, sound_type, volume):
        """Устанавливает громкость для указанного типа звука (0-100)"""
        if "volumes" not in self.preferences:
            self.preferences["volumes"] = {}
        self.preferences["volumes"][sound_type] = max(0, min(100, volume))

    def get_volume(self, sound_type):
        """Возвращает громкость для указанного типа звука"""
        volumes = self.get_volumes()
        return volumes.get(sound_type, 50)
