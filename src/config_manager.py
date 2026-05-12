#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.config import (
    WEEK_DAYS, WEEK_DAYS_RU, WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN,
    DEFAULT_SCHEDULE, SCHEDULE_PATH, PREFERENCES_FILE
)
import yaml
from pathlib import Path
import datetime


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
                self.schedule_data = DEFAULT_SCHEDULE.copy()
                return False
        else:
            self.schedule_data = DEFAULT_SCHEDULE.copy()
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
                return True
            except Exception:
                pass
        self.preferences = {}
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
        music = self.preferences.get("music", {})
        if not music:
            music = DEFAULT_SCHEDULE["music"].copy()
        return music
    
    def set_music_folder(self, folder):
        if "music" not in self.preferences:
            self.preferences["music"] = {}
        self.preferences["music"]["folder"] = folder
        self.preferences["music"]["enabled"] = bool(folder)
    
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
    
    def get_theme(self):
        return self.preferences.get("theme", "light")
    
    def set_theme(self, theme):
        self.preferences["theme"] = theme
    
    # Методы для работы с праздничными днями
    def get_holidays(self):
        """Возвращает список праздничных дат (строки формата YYYY-MM-DD)"""
        if self.schedule_data and "holidays" in self.schedule_data:
            return self.schedule_data.get("holidays", [])
        return DEFAULT_SCHEDULE.get("holidays", [])
    
    def set_holidays(self, holidays_list):
        """Устанавливает список праздничных дат"""
        if self.schedule_data is None:
            self.schedule_data = {}
        self.schedule_data["holidays"] = holidays_list
    
    def is_holiday(self, date_obj):
        """Проверяет, является ли дата праздничным днём"""
        holidays = self.get_holidays()
        date_str = date_obj.strftime("%Y-%m-%d")
        return date_str in holidays
    
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
        if self.preferences and "volumes" in self.preferences:
            return self.preferences.get("volumes", DEFAULT_SCHEDULE.get("volumes", {}))
        return DEFAULT_SCHEDULE.get("volumes", {})
    
    def set_volume(self, sound_type, volume):
        """Устанавливает громкость для указанного типа звука (0-100)"""
        if "volumes" not in self.preferences:
            self.preferences["volumes"] = {}
        self.preferences["volumes"][sound_type] = max(0, min(100, volume))
    
    def get_volume(self, sound_type):
        """Возвращает громкость для указанного типа звука"""
        volumes = self.get_volumes()
        return volumes.get(sound_type, 50)
