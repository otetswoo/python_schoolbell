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
    
    def get_locale(self):
        return self.preferences.get("locale", "ru")
    
    def set_locale(self, locale):
        self.preferences["locale"] = locale
    
    def get_theme(self):
        return self.preferences.get("theme", "light")
    
    def set_theme(self, theme):
        self.preferences["theme"] = theme
