#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from copy import deepcopy
from pathlib import Path
import datetime

import yaml

from src.config import DEFAULT_SCHEDULE, SCHEDULE_PATH, PREFERENCES_FILE, WEEK_DAYS

RU_TO_EN_DAYS = {
    "Понедельник": "monday", "Вторник": "tuesday", "Среда": "wednesday",
    "Четверг": "thursday", "Пятница": "friday", "Суббота": "saturday",
    "Воскресенье": "sunday"
}


class ConfigManager:
    def __init__(self):
        self.schedule_data = None
        self.preferences = {}

    def load_schedule(self):
        if SCHEDULE_PATH.exists():
            try:
                with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f) or {}
                if not self._validate_schedule(loaded):
                    print("Warning: schedule.yml has invalid structure, using defaults")
                    self.schedule_data = deepcopy(DEFAULT_SCHEDULE)
                    return False
                self.schedule_data = loaded
                return True
            except Exception as e:
                print(f"Error loading schedule: {e}")
                self.schedule_data = deepcopy(DEFAULT_SCHEDULE)
                return False
        else:
            self.schedule_data = deepcopy(DEFAULT_SCHEDULE)
            return True

    def _validate_schedule(self, data: dict) -> bool:
        """Проверяет базовую структуру данных расписания.
        Возвращает False только при явно некорректной структуре
        (например, если schedules — не словарь, или урок — не словарь).
        Пустые варианты (none: []) считаются допустимыми."""
        if not isinstance(data, dict):
            return False
        schedules = data.get("schedules", {})
        if not isinstance(schedules, dict):
            return False
        for variant_lessons in schedules.values():
            if not isinstance(variant_lessons, list):
                return False
            for lesson in variant_lessons:
                if not isinstance(lesson, dict):
                    return False
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
                
                # Миграция старых русских ключей вариантов дней в английские
                self._migrate_variants()
                
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

                self._migrate_announcement_volume()
                
                return True
            except Exception as e:
                print(f"Error loading preferences: {e}")
                # Пробуем восстановить из бэкапа
                bak_path = Path(PREFERENCES_FILE).with_suffix(".yml.bak")
                if bak_path.exists():
                    try:
                        with open(bak_path, "r", encoding="utf-8") as f:
                            self.preferences = yaml.safe_load(f) or {}
                        print("Preferences restored from backup")
                        self._migrate_variants()
                        self._migrate_announcement_volume()
                        return True
                    except Exception:
                        pass
        self.preferences = {"announcements": []}
        return False
    
    def _migrate_variants(self):
        """Мигрирует русские ключи вариантов дней в английские."""
        variants = self.preferences.get("variants", {})
        if not variants:
            return
        
        migrated = False
        for ru_key, en_key in RU_TO_EN_DAYS.items():
            if ru_key in variants:
                # Копируем значение в английский ключ, если его ещё нет
                if en_key not in variants:
                    variants[en_key] = variants[ru_key]
                # Удаляем русский ключ
                del variants[ru_key]
                migrated = True
        
        if migrated:
            self.preferences["variants"] = variants

    def _migrate_announcement_volume(self):
        """Переносит ошибочно сохранённую громкость из объявлений в общие настройки."""
        announcements = self.preferences.get("announcements", [])
        if not isinstance(announcements, list):
            return

        moved_volume = None
        for ann in announcements:
            if not isinstance(ann, dict) or "volume" not in ann:
                continue
            if moved_volume is None:
                moved_volume = ann.get("volume")
            del ann["volume"]

        if moved_volume is not None:
            if not isinstance(self.preferences.get("volumes"), dict):
                self.preferences["volumes"] = {}
            if "announcement" not in self.preferences["volumes"]:
                try:
                    self.preferences["volumes"]["announcement"] = max(
                        0, min(100, int(moved_volume))
                    )
                except (TypeError, ValueError):
                    pass

    def save_preferences(self, prefs):
        try:
            # Автобэкап перед перезаписью
            pref_path = Path(PREFERENCES_FILE)
            if pref_path.exists():
                bak_path = pref_path.with_suffix(".yml.bak")
                import shutil
                shutil.copy2(pref_path, bak_path)
            
            prefs["last_saved"] = datetime.datetime.now().isoformat()
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                yaml.dump(prefs, f, allow_unicode=True, default_flow_style=False)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False
    
    def restore_from_backup(self):
        """Восстанавливает preferences.yml из .bak если основной файл повреждён."""
        pref_path = Path(PREFERENCES_FILE)
        bak_path = pref_path.with_suffix(".yml.bak")
        if bak_path.exists():
            import shutil
            shutil.copy2(bak_path, pref_path)
            return self.load_preferences()
        return False

    def get_day_variant(self, day_ru):
        day_key = RU_TO_EN_DAYS.get(day_ru, day_ru)
        return self.preferences.get("variants", {}).get(day_key, "usual")

    def set_day_variant(self, day_ru, variant):
        if "variants" not in self.preferences:
            self.preferences["variants"] = {}
        day_key = RU_TO_EN_DAYS.get(day_ru, day_ru)
        self.preferences["variants"][day_key] = variant

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

    def get_announcements(self):
        """Возвращает список всех объявлений"""
        return self.preferences.get("announcements", [])

    def get_active_announcements(self):
        """Возвращает список кортежей (index, dict) активных объявлений.
        Активное = enabled=True и played=False."""
        result = []
        for i, ann in enumerate(self.get_announcements()):
            if ann.get("enabled", True) and not ann.get("played", False):
                result.append((i, ann))
        return result

    def add_announcement(self, file, date, time, repeat_days=None):
        """Добавляет объявление, возвращает его индекс"""
        if "announcements" not in self.preferences:
            self.preferences["announcements"] = []
        ann = {
            "file": file,
            "date": date,
            "time": time,
            "enabled": True,
            "played": False,
            "repeat_days": repeat_days or [],
        }
        self.preferences["announcements"].append(ann)
        return len(self.preferences["announcements"]) - 1

    def update_announcement(self, index, **kwargs):
        """Обновляет поля объявления по индексу"""
        anns = self.preferences.get("announcements", [])
        if 0 <= index < len(anns):
            anns[index].update(kwargs)

    def delete_announcement(self, index):
        """Удаляет объявление по индексу"""
        anns = self.preferences.get("announcements", [])
        if 0 <= index < len(anns):
            anns.pop(index)

    def set_announcement_played_by_index(self, index, played):
        """Помечает объявление как сыгранное или сбрасывает флаг"""
        self.update_announcement(index, played=played)
