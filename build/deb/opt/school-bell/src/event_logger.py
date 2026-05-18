#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Модуль логирования событий для приложения School Bell"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from src.config import LOGS_DIR


class EventLogger:
    """Класс для ведения лога событий
    
    Логи хранятся в файлах вида bell_YYYY-MM-DD.log
    Автоматически удаляются логи старше 3 дней
    """
    
    def __init__(self):
        self.current_log_file = None
        self._cleanup_old_logs()
    
    def _get_log_filename(self, date=None):
        """Возвращает имя файла лога для указанной даты"""
        if date is None:
            date = datetime.now().date()
        return f"bell_{date.strftime('%Y-%m-%d')}.log"
    
    def _get_current_log_path(self):
        """Возвращает путь к текущему файлу лога"""
        return LOGS_DIR / self._get_log_filename()
    
    def _cleanup_old_logs(self):
        """Удаляет логи старше 3 дней"""
        if not LOGS_DIR.exists():
            return
        
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=3)
        
        for log_file in LOGS_DIR.glob("bell_*.log"):
            try:
                # Извлекаем дату из имени файла
                date_str = log_file.stem.replace("bell_", "")
                log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if log_date < cutoff_date:
                    log_file.unlink()
            except (ValueError, OSError):
                continue
    
    def log_event(self, event_type, message):
        """Записывает событие в лог
        
        Args:
            event_type: Тип события (bell, music, anthem, error, info)
            message: Сообщение
        """
        log_path = self._get_current_log_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Форматируем сообщение с иконкой в зависимости от типа
        icons = {
            "bell": "🔔",
            "music": "🎵",
            "anthem": "🎼",
            "error": "❌",
            "info": "ℹ️",
            "start": "▶️",
            "stop": "⏹️"
        }
        icon = icons.get(event_type, "•")
        
        log_entry = f"[{timestamp}] {icon} [{event_type.upper()}] {message}\n"
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log: {e}")
    
    def get_today_events(self):
        """Возвращает список событий за сегодня"""
        log_path = self._get_current_log_path()
        events = []
        
        if not log_path.exists():
            return events
        
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    events.append(line.strip())
        except Exception:
            pass
        
        return events
    
    def get_recent_errors(self, days=1):
        """Возвращает список ошибок за последние N дней"""
        errors = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            log_path = LOGS_DIR / self._get_log_filename(date)
            
            if not log_path.exists():
                continue
            
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if "[ERROR]" in line:
                            errors.append(line.strip())
            except Exception:
                continue
        
        return errors
