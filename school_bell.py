#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMenu, QFileDialog, QMessageBox,
    QHeaderView, QMenuBar, QDialog, QListWidget, QListWidgetItem, QCheckBox,
    QFormLayout, QSpinBox, QComboBox, QDialogButtonBox, QGroupBox
)
from PySide6.QtGui import QAction, QColor, QFont, QPalette, QKeySequence
from PySide6.QtCore import Qt, QTimer, QEvent

from src.config import (
    WEEK_DAYS, WEEK_DAYS_RU, WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN,
    DEFAULT_SCHEDULE, SCHEDULE_PATH, PREFERENCES_FILE, ensure_dirs
)
from src.config_manager import ConfigManager
from src.sound_player import SoundPlayer
from src.music_player import MusicPlayer
from src.lesson_dialog import LessonDialog
from src.music_settings_dialog import MusicSettingsDialog
from src.theme_dialog import ThemeDialog
from src.schedule_editor_dialog import ScheduleEditorDialog
from src.gui.localization import LOCALIZATION


COLOR_CURRENT_LIGHT = QColor("#c8e6c9")
COLOR_SOON_LIGHT = QColor("#fff9c4")
COLOR_NORMAL_LIGHT = QColor("#ffffff")

COLOR_CURRENT_DARK = QColor("#2e7d32")
COLOR_SOON_DARK = QColor("#f9a825")
COLOR_NORMAL_DARK = QColor("#3c3c3c")


class SchoolBell(QMainWindow):
    def __init__(self):
        super().__init__()
        
        ensure_dirs()
        
        self.config = ConfigManager()
        self.config.load_schedule()
        self.config.load_preferences()
        
        self.current_locale = self.config.get_locale()
        self.current_theme = self.config.get_theme()
        
        self.sound_player = SoundPlayer()
        self.music_player = MusicPlayer(sound_player=self.sound_player)
        
        self.schedule_variants = {}
        self.day_variants = {d: "usual" for d in WEEK_DAYS_RU}
        self.current_day = None
        self.current_variant = "usual"
        
        self.scheduled_music = {}
        self.bells_enabled = True
        
        music_settings = self.config.get_music_settings()
        self.music_enabled = music_settings.get("enabled", False)
        
        anthem_settings = self.config.get_anthem_settings()
        self.anthem_enabled = anthem_settings.get("enabled", False)
        
        self.init_ui()
        self.load_data()
        self.apply_theme()
        self.set_today_schedule()
        
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)
        
        self.bell_timer = QTimer()
        self.bell_timer.timeout.connect(self.check_bells)
        self.bell_timer.start(500)
    
    def init_ui(self):
        self.setWindowTitle(LOCALIZATION[self.current_locale]["app_title"])
        self.resize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Верхняя панель: дни недели слева, чекбоксы справа
        top_layout = QHBoxLayout()
        
        # Дни недели
        self.days_layout = QHBoxLayout()
        self.day_buttons = {}
        for i, (short_ru, short_en) in enumerate(zip(WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN)):
            short = short_ru if self.current_locale == "ru" else short_en
            full = WEEK_DAYS_RU[i]
            
            btn = QPushButton(short)
            btn.setMinimumHeight(36)
            btn.setToolTip(full + "\nЛКМ - выбрать день\nПКМ - переключить вариант расписания")
            btn.clicked.connect(lambda checked=False, d=full: self.select_day(d))
            # Добавляем обработчик для переключения варианта по правому клику
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, d=full: self.on_day_clicked(d))
            btn.setCheckable(True)
            self.days_layout.addWidget(btn)
            self.day_buttons[full] = btn
            
        top_layout.addLayout(self.days_layout)
        top_layout.addStretch()
        
        # Чекбоксы справа
        self.bells_checkbox = QCheckBox(LOCALIZATION[self.current_locale]["chk_bells"])
        self.bells_checkbox.setChecked(True)
        self.bells_checkbox.stateChanged.connect(self.on_bells_toggled)
        top_layout.addWidget(self.bells_checkbox)
        
        self.music_checkbox = QCheckBox(LOCALIZATION[self.current_locale]["chk_music"])
        music_settings = self.config.get_music_settings()
        self.music_checkbox.setChecked(music_settings.get("enabled", False))
        self.music_checkbox.stateChanged.connect(self.on_music_toggled)
        top_layout.addWidget(self.music_checkbox)
        
        self.anthem_checkbox = QCheckBox(LOCALIZATION[self.current_locale]["chk_anthem"])
        anthem_settings = self.config.get_anthem_settings()
        self.anthem_checkbox.setChecked(anthem_settings.get("enabled", False))
        self.anthem_checkbox.stateChanged.connect(self.on_anthem_toggled)
        top_layout.addWidget(self.anthem_checkbox)
        
        layout.addLayout(top_layout)
        
        # Таблица расписания (компактная)
        self.table = QTableWidget(0, 3)
        headers = ["Начало", "Конец", "Урок"] if self.current_locale == "ru" else ["Start", "End", "Lesson"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        # Уменьшаем высоту строк для компактности
        self.table.verticalHeader().setDefaultSectionSize(28)
        layout.addWidget(self.table)
        
        # Нижняя панель: кнопка редактирования и кнопки управления
        bottom_layout = QHBoxLayout()
        
        self.edit_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_edit"])
        self.edit_btn.clicked.connect(self.edit_schedule)
        bottom_layout.addWidget(self.edit_btn)
        
        # Кнопки управления правее
        self.today_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_today"])
        self.today_btn.clicked.connect(self.set_today_schedule)
        self.today_btn.setToolTip("Нажмите для перехода на текущий день")
        bottom_layout.addWidget(self.today_btn)
        
        bottom_layout.addStretch()
        
        self.bell_btn = QPushButton("▶️ " + LOCALIZATION[self.current_locale]["btn_bell"].replace("🔔", "").strip())
        self.bell_btn.clicked.connect(self.manual_bell)
        bottom_layout.addWidget(self.bell_btn)
        
        self.music_btn = QPushButton("▶️ " + LOCALIZATION[self.current_locale]["btn_music"].replace("🎵", "").strip())
        self.music_btn.clicked.connect(self.manual_music)
        bottom_layout.addWidget(self.music_btn)
        
        self.anthem_btn = QPushButton(self._get_anthem_button_text())
        self.anthem_btn.clicked.connect(self.manual_anthem)
        bottom_layout.addWidget(self.anthem_btn)
        
        self.stop_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_stop"])
        self.stop_btn.clicked.connect(self.manual_stop)
        bottom_layout.addWidget(self.stop_btn)
        
        layout.addLayout(bottom_layout)
        
        self.status_label = QLabel(LOCALIZATION[self.current_locale]["status_ready"])
        self.status_label.setStyleSheet("background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        self.setup_menu()
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu(LOCALIZATION[self.current_locale]["menu_file"])
        
        load_act = QAction(LOCALIZATION[self.current_locale]["action_load"], self)
        load_act.triggered.connect(self.load_schedule)
        load_act.setShortcut(QKeySequence("Ctrl+O"))
        file_menu.addAction(load_act)
        
        save_act = QAction(LOCALIZATION[self.current_locale]["action_save"], self)
        save_act.triggered.connect(self.save_schedule)
        save_act.setShortcut(QKeySequence("Ctrl+S"))
        file_menu.addAction(save_act)
        
        file_menu.addSeparator()
        
        exit_act = QAction(LOCALIZATION[self.current_locale]["action_exit"], self)
        exit_act.triggered.connect(self.close)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        file_menu.addAction(exit_act)
        
        settings_menu = menubar.addMenu(LOCALIZATION[self.current_locale]["menu_settings"])
        
        sounds_menu = settings_menu.addMenu(LOCALIZATION[self.current_locale]["menu_sounds"])
        
        sounds_start_act = QAction(LOCALIZATION[self.current_locale]["action_sounds_start"], self)
        sounds_start_act.triggered.connect(lambda: self.select_sounds("start"))
        sounds_menu.addAction(sounds_start_act)
        
        sounds_end_act = QAction(LOCALIZATION[self.current_locale]["action_sounds_end"], self)
        sounds_end_act.triggered.connect(lambda: self.select_sounds("end"))
        sounds_menu.addAction(sounds_end_act)
        
        music_act = QAction(LOCALIZATION[self.current_locale]["action_music"], self)
        music_act.triggered.connect(self.show_music_settings)
        settings_menu.addAction(music_act)
        
        anthem_act = QAction(LOCALIZATION[self.current_locale]["action_anthem"], self)
        anthem_act.triggered.connect(self.show_anthem_settings)
        settings_menu.addAction(anthem_act)
        
        theme_act = QAction(LOCALIZATION[self.current_locale]["action_theme"], self)
        theme_act.triggered.connect(self.show_theme_dialog)
        settings_menu.addAction(theme_act)
        
        # Добавляем пункт "Редактировать шаблоны"
        templates_act = QAction("📚 Редактировать шаблоны", self)
        templates_act.triggered.connect(self.show_templates_editor)
        settings_menu.addAction(templates_act)
        
        locale_menu = settings_menu.addMenu("Language / Язык")
        
        ru_act = QAction(LOCALIZATION[self.current_locale]["action_locale_ru"], self)
        ru_act.triggered.connect(lambda: self.set_locale("ru"))
        locale_menu.addAction(ru_act)
        
        en_act = QAction(LOCALIZATION[self.current_locale]["action_locale_en"], self)
        en_act.triggered.connect(lambda: self.set_locale("en"))
        locale_menu.addAction(en_act)
        
        # Добавляем меню "Справка"
        help_menu = menubar.addMenu(LOCALIZATION[self.current_locale]["menu_help"])
        
        about_act = QAction(LOCALIZATION[self.current_locale]["action_about"], self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)
        
        # Добавляем действие для кнопки "Сегодня" с горячей клавишей Ctrl+T
        today_act = QAction(LOCALIZATION[self.current_locale]["btn_today"], self)
        today_act.setShortcut(QKeySequence("Ctrl+T"))
        today_act.triggered.connect(self.set_today_schedule)
        self.addAction(today_act)
    
    def show_about(self):
        """Показать диалог 'О программе'"""
        QMessageBox.about(self, LOCALIZATION[self.current_locale]["about_title"], 
                          LOCALIZATION[self.current_locale]["about_text"])
    
    def show_templates_editor(self):
        """Открыть диалог редактирования шаблонов расписания"""
        from src.templates_dialog import TemplatesEditorDialog
        dlg = TemplatesEditorDialog(self, self.schedule_variants, self.config)
        if dlg.exec() == QDialog.Accepted:
            new_templates = dlg.get_templates()
            # Обновляем шаблоны для всех дней
            for key in WEEK_DAYS:
                for variant in ["usual", "short"]:
                    if variant in new_templates:
                        self.schedule_variants[key][variant] = list(new_templates[variant])
            QMessageBox.information(self, "OK", "Шаблоны обновлены")
    
    def load_data(self):
        prefs = self.config.preferences
        
        variants = prefs.get("variants", {})
        for day_ru in WEEK_DAYS_RU:
            if day_ru in variants:
                self.day_variants[day_ru] = variants[day_ru]
        
        sounds = prefs.get("sounds", {})
        if not sounds:
            sounds = DEFAULT_SCHEDULE["sounds"]
        self.sounds = sounds
        
        music = prefs.get("music", {})
        if music.get("enabled") and music.get("folder"):
            self.music_player.set_music_folder(music["folder"])
        
        templates = self.config.schedule_data.get("schedules", DEFAULT_SCHEDULE["schedules"])
        for key in WEEK_DAYS:
            self.schedule_variants[key] = {
                "usual": list(templates.get("usual", [])),
                "short": list(templates.get("short", [])),
                "none": []
            }
    
    def select_day(self, day_ru):
        self.current_day = day_ru
        variant = self.day_variants.get(day_ru, "usual")
        self.current_variant = variant
        
        idx = WEEK_DAYS_RU.index(day_ru)
        key = WEEK_DAYS[idx]
        
        lessons = self.schedule_variants.get(key, {}).get(variant, [])
        
        self.table.setRowCount(0)
        for l in lessons:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(l.get("start", "")))
            self.table.setItem(row, 1, QTableWidgetItem(l.get("end", "")))
            self.table.setItem(row, 2, QTableWidgetItem(str(l.get("num", ""))))
        
        self._update_day_buttons_style()
    
    def _update_day_buttons_style(self):
        """Обновляет стиль кнопок дней недели: выделяет текущий день и показывает варианты"""
        for day_ru, btn in self.day_buttons.items():
            variant = self.day_variants.get(day_ru, "usual")
            
            if day_ru == self.current_day:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
            
            # Меняем текст кнопки в зависимости от варианта
            idx = WEEK_DAYS_RU.index(day_ru)
            short = WEEK_DAYS_SHORT[idx] if self.current_locale == "ru" else WEEK_DAYS_SHORT_EN[idx]
            
            if variant == "short":
                btn.setText(short + " (К)")
            elif variant == "none":
                btn.setText(short + " (X)")
            else:
                btn.setText(short)
    
    def on_day_clicked(self, day_ru):
        """Обработчик клика на день недели - переключает вариант расписания"""
        current_variant = self.day_variants.get(day_ru, "usual")
        # Циклическое переключение: usual -> short -> none -> usual
        next_variant = {"usual": "short", "short": "none", "none": "usual"}[current_variant]
        self.day_variants[day_ru] = next_variant
        self.config.set_day_variant(day_ru, next_variant)
        self.config.save_preferences(self.config.preferences)
        
        self._update_day_buttons_style()
        
        # Если клик был на текущем дне, обновляем таблицу
        if day_ru == self.current_day:
            self.select_day(day_ru)
    
    def set_today_schedule(self):
        today = datetime.datetime.today()
        idx = today.weekday()
        day_ru = WEEK_DAYS_RU[idx]
        # Обновляем текст кнопки Сегодня (только надпись, без даты)
        self.today_btn.setText(LOCALIZATION[self.current_locale]['btn_today'])
        self.music_player.reset_daily()
        self.scheduled_music.clear()
        self.select_day(day_ru)
    
    def edit_schedule(self):
        if not self.current_day:
            QMessageBox.warning(self, "Ошибка", "Выберите день")
            return
        
        idx = WEEK_DAYS_RU.index(self.current_day)
        key = WEEK_DAYS[idx]
        lessons = self.schedule_variants.get(key, {}).get(self.current_variant, [])
        
        dlg = ScheduleEditorDialog(self, self.current_day, self.current_variant, lessons, self.schedule_variants)
        if dlg.exec() == QDialog.Accepted:
            new_lessons = dlg.get_lessons()
            self.schedule_variants[key][self.current_variant] = new_lessons
            self.select_day(self.current_day)
            QMessageBox.information(self, "OK", "Расписание обновлено")
    
    def update_ui(self):
        now = datetime.datetime.now()
        
        day_names_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_name = day_names_ru[now.weekday()] if self.current_locale == "ru" else day_names_en[now.weekday()]
        
        month_names_ru = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        month_names_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_name = month_names_ru[now.month - 1] if self.current_locale == "ru" else month_names_en[now.month - 1]
        
        time_str = now.strftime("%H:%M")
        status = f"{LOCALIZATION[self.current_locale]['btn_today'].replace('📅', '').strip()} {day_name}, {now.day} {month_name} {time_str}"
        
        cur, seconds_left, _ = self.get_current_lesson(now)
        if cur:
            mins = seconds_left // 60
            lesson_text = f"Урок {cur.get('num')}" if self.current_locale == "ru" else f"Lesson {cur.get('num')}"
            status += f"   |   {lesson_text}, {mins} мин" if self.current_locale == "ru" else f"   |   {lesson_text}, {mins} min"
        
        self.status_label.setText(status)
        self.highlight_table(now)
    
    def get_current_lesson(self, now):
        if not self.current_day:
            return None, None, None
        
        idx = WEEK_DAYS_RU.index(self.current_day)
        key = WEEK_DAYS[idx]
        lessons = self.schedule_variants.get(key, {}).get(self.current_variant, [])
        
        today = now.date()
        parsed = []
        for l in lessons:
            try:
                s = datetime.datetime.combine(today, datetime.time.fromisoformat(l["start"].replace(":", ":00")))
                e = datetime.datetime.combine(today, datetime.time.fromisoformat(l["end"].replace(":", ":00")))
                parsed.append((s, e, l))
            except:
                continue
        
        for s, e, l in parsed:
            if s <= now <= e:
                return l, int((e - now).total_seconds()), None
        
        for s, e, l in parsed:
            if now < s:
                return None, None, int((s - now).total_seconds())
        
        return None, None, None
    
    def highlight_table(self, now):
        rows = self.table.rowCount()
        today = now.date()
        
        # Выбираем цвета в зависимости от темы
        if self.current_theme == "dark":
            color_current = COLOR_CURRENT_DARK
            color_soon = COLOR_SOON_DARK
            color_normal = COLOR_NORMAL_DARK
        else:
            color_current = COLOR_CURRENT_LIGHT
            color_soon = COLOR_SOON_LIGHT
            color_normal = COLOR_NORMAL_LIGHT
        
        for r in range(rows):
            try:
                start_str = self.table.item(r, 0).text()
                end_str = self.table.item(r, 1).text()
                
                start = datetime.datetime.combine(today, datetime.time.fromisoformat(start_str.replace(":", ":00")))
                end = datetime.datetime.combine(today, datetime.time.fromisoformat(end_str.replace(":", ":00")))
                
                bg = color_normal
                if start <= now <= end:
                    bg = color_current
                elif 0 <= (start - now).total_seconds() <= 120:
                    bg = color_soon
                
                for c in range(3):
                    item = self.table.item(r, c)
                    if item:
                        item.setBackground(bg)
                
                if 0 <= (now - start).total_seconds() < 2:
                    self.play_bell("start", start)
                if 0 <= (now - end).total_seconds() < 2:
                    self.play_bell("end", end)
                    
            except:
                continue
    
    def play_bell(self, bell_type, event_time):
        if not self.bells_enabled:
            return
        
        cache_key = f"{bell_type}_{event_time.strftime('%H%M')}"
        if cache_key in self.scheduled_music:
            return
        
        path = self.sounds.get(bell_type)
        if path and self.sound_player.play(path, bell_type):
            self.scheduled_music[cache_key] = True
            
            if bell_type == "end" and self.music_enabled:
                music_time = event_time + datetime.timedelta(minutes=2)
                music_key = f"music_{music_time.strftime('%H%M')}"
                if music_key not in self.scheduled_music:
                    QTimer.singleShot(120000, lambda: self.play_break_music())
    
    def play_break_music(self):
        if not self.music_player.music_folder:
            return
        
        track = self.music_player.get_next_track()
        if track and self.music_player.can_play():
            self.sound_player.play_music(track)
            self.music_player.mark_played()
    
    def check_bells(self):
        now = datetime.datetime.now()
        today_key = WEEK_DAYS[now.weekday()]
        
        if hasattr(self, 'last_day') and self.last_day != today_key:
            self.set_today_schedule()
        self.last_day = today_key
        
        # Проверяем автоматический запуск гимна
        self.check_anthem(now)
    
    def load_schedule(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Загрузить расписание", "", "YAML (*.yml *.yaml)")
        if fname:
            try:
                import yaml
                with open(fname, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                self.config.schedule_data = data
                self.load_data()
                self.set_today_schedule()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def save_schedule(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить расписание", str(SCHEDULE_PATH), "YAML (*.yml *.yaml)")
        if fname:
            try:
                import yaml
                days_out = {}
                for i, key in enumerate(WEEK_DAYS):
                    days_out[key] = self.day_variants.get(WEEK_DAYS_RU[i], "usual")
                
                # Сохраняем шаблоны (берём из первого дня как базовые)
                templates = {}
                first_key = WEEK_DAYS[0]
                for var in ["usual", "short"]:
                    templates[var] = list(self.schedule_variants.get(first_key, {}).get(var, []))
                
                data = {"days": days_out, "schedules": templates, "sounds": self.sounds}
                with open(fname, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def select_sounds(self, bell_type):
        title = "Звук начала урока" if bell_type == "start" else "Звук окончания урока"
        if self.current_locale == "en":
            title = "Start Lesson Sound" if bell_type == "start" else "End Lesson Sound"
        
        path, _ = QFileDialog.getOpenFileName(self, title, "", "Audio (*.wav *.mp3)")
        if path:
            self.sounds[bell_type] = path
            self.config.set_sound(bell_type, path)
            self.config.save_preferences(self.config.preferences)
            
            msg = f"Мелодия '{'начала' if bell_type == 'start' else 'окончания'}' установлена"
            if self.current_locale == "en":
                msg = f"'{'Start' if bell_type == 'start' else 'End'}' bell melody set"
            self.status_label.setText(msg)
    
    def show_music_settings(self):
        dlg = MusicSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            music = self.config.get_music_settings()
            if music.get("folder"):
                self.music_player.set_music_folder(music["folder"])
            self.config.save_preferences(self.config.preferences)
    
    def show_anthem_settings(self):
        """Открыть диалог настройки гимна"""
        from src.anthem_settings_dialog import AnthemSettingsDialog
        dlg = AnthemSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            anthem = self.config.get_anthem_settings()
            self.config.save_preferences(self.config.preferences)
    
    def show_theme_dialog(self):
        dlg = ThemeDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            theme = dlg.get_theme()
            self.current_theme = theme
            self.config.set_theme(theme)
            self.config.save_preferences(self.config.preferences)
            self.apply_theme()
    
    def apply_theme(self):
        if self.current_theme == "dark":
            self.setStyleSheet("""
                QMainWindow { background-color: #2b2b2b; color: #ffffff; }
                QTableWidget { background-color: #3c3c3c; color: #ffffff; gridline-color: #555; }
                QHeaderView::section { background-color: #4a4a4a; color: #ffffff; border: 1px solid #555; padding: 4px; }
                QPushButton { background-color: #4a4a4a; color: #ffffff; border: 1px solid #555; padding: 6px; }
                QPushButton:hover { background-color: #5a5a5a; }
                QPushButton:checked { background-color: #2e7d32; color: #ffffff; font-weight: bold; }
                QLabel { color: #ffffff; }
                QMenuBar { background-color: #3c3c3c; color: #ffffff; }
                QMenu { background-color: #3c3c3c; color: #ffffff; }
                QCheckBox { color: #ffffff; spacing: 4px; }
                QCheckBox::indicator { width: 18px; height: 18px; background-color: #555; border: 1px solid #777; border-radius: 3px; }
                QCheckBox::indicator:checked { background-color: #4caf50; image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik05IDE2LjE3TDQuODMgMTJsLTEuNDIgMS40MUw5IDE5IDIxIDdsLTEuNDEtMS40MXoiLz48L3N2Zz4); }
                QStatusBar, QLabel#status { background-color: #3c3c3c; color: #ffffff; }
                QDialog { background-color: #2b2b2b; color: #ffffff; }
                QDialog QLabel { color: #ffffff; }
                QDialog QPushButton { background-color: #4a4a4a; color: #ffffff; border: 1px solid #555; }
                QDialog QSpinBox, QDialog QLineEdit, QDialog QComboBox { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
                QSpinBox { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
                QLineEdit { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
                QComboBox { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
                QListWidget { background-color: #3c3c3c; color: #ffffff; border: 1px solid #555; }
                QFormLayout QLabel { color: #ffffff; }
            """)
        else:
            # Светлая тема в стиле Adwaita Gnome
            self.setStyleSheet("""
                QMainWindow { background-color: #fafafa; color: #2e3436; }
                QTableWidget { background-color: #ffffff; color: #2e3436; gridline-color: #cdc7c2; }
                QHeaderView::section { background-color: #e8e8e7; color: #2e3436; border: 1px solid #cdc7c2; padding: 4px; font-weight: bold; }
                QPushButton { background-color: #f6f5f4; color: #2e3436; border: 1px solid #cdc7c2; padding: 6px; border-radius: 6px; }
                QPushButton:hover { background-color: #ffffff; border-color: #9a9996; }
                QPushButton:pressed { background-color: #d5d3cf; }
                QPushButton:checked { background-color: #3584e4; color: #ffffff; font-weight: bold; border-color: #1c71d8; }
                QPushButton:checked:hover { background-color: #62a0ea; }
                QLabel { color: #2e3436; }
                QMenuBar { background-color: #f6f5f4; color: #2e3436; border: 1px solid #cdc7c2; }
                QMenuBar::item:selected { background-color: #ffffff; }
                QMenu { background-color: #f6f5f4; color: #2e3436; border: 1px solid #cdc7c2; }
                QMenu::item:selected { background-color: #ffffff; }
                QCheckBox { color: #2e3436; spacing: 4px; }
                QCheckBox::indicator { width: 18px; height: 18px; background-color: #ffffff; border: 1px solid #cdc7c2; border-radius: 3px; }
                QCheckBox::indicator:checked { background-color: #3584e4; border-color: #1c71d8; image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZmlsbD0id2hpdGUiIGQ9Ik05IDE2LjE3TDQuODMgMTJsLTEuNDIgMS40MUw5IDE5IDIxIDdsLTEuNDEtMS40MXoiLz48L3N2Zz4); }
                QStatusBar, QLabel#status { background-color: #f6f5f4; color: #2e3436; border: 1px solid #cdc7c2; }
                QDialog { background-color: #fafafa; color: #2e3436; }
                QDialog QLabel { color: #2e3436; }
                QDialog QPushButton { background-color: #f6f5f4; color: #2e3436; border: 1px solid #cdc7c2; }
                QDialog QSpinBox, QDialog QLineEdit, QDialog QComboBox { background-color: #ffffff; color: #2e3436; border: 1px solid #cdc7c2; }
                QSpinBox { background-color: #ffffff; color: #2e3436; border: 1px solid #cdc7c2; }
                QLineEdit { background-color: #ffffff; color: #2e3436; border: 1px solid #cdc7c2; padding: 4px; }
                QComboBox { background-color: #ffffff; color: #2e3436; border: 1px solid #cdc7c2; padding: 4px; }
                QComboBox::drop-down { border: none; width: 20px; }
                QComboBox::down-arrow { image: none; border-left: 1px solid #cdc7c2; }
                QListWidget { background-color: #ffffff; color: #2e3436; border: 1px solid #cdc7c2; }
                QListWidget::item:selected { background-color: #3584e4; color: #ffffff; }
                QFormLayout QLabel { color: #2e3436; }
            """)
    
    def set_locale(self, locale):
        self.current_locale = locale
        self.config.set_locale(locale)
        self.config.save_preferences(self.config.preferences)
        
        texts = LOCALIZATION[locale]
        self.setWindowTitle(texts["app_title"])
        
        short_names = WEEK_DAYS_SHORT if locale == "ru" else WEEK_DAYS_SHORT_EN
        for btn, short in zip(self.day_buttons.values(), short_names):
            btn.setText(short)
        
        self.edit_btn.setText(texts["btn_edit"])
        self.status_label.setText(texts["status_ready"])
        self.bells_checkbox.setText(texts["chk_bells"])
        self.music_checkbox.setText(texts["chk_music"])
        self.anthem_checkbox.setText(texts["chk_anthem"])
        # Обновляем текст кнопки Сегодня (только надпись, без даты)
        self.today_btn.setText(texts["btn_today"])
        self.bell_btn.setText("▶️ " + texts["btn_bell"].replace("🔔", "").strip())
        self.music_btn.setText("▶️ " + texts["btn_music"].replace("🎵", "").strip())
        self.anthem_btn.setText(self._get_anthem_button_text())
        self.stop_btn.setText(texts["btn_stop"])
        
        headers = ["Начало", "Конец", "Урок"] if locale == "ru" else ["Start", "End", "Lesson"]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Обновляем меню после смены языка
        self.menuBar().clear()
        self.setup_menu()
    
    def on_bells_toggled(self, state):
        self.bells_enabled = (state == Qt.Checked)
    
    def on_music_toggled(self, state):
        self.music_enabled = (state == Qt.Checked)
        music_settings = self.config.get_music_settings()
        music_settings["enabled"] = self.music_enabled
        self.config.preferences["music"] = music_settings
        self.config.save_preferences(self.config.preferences)
    
    def on_anthem_toggled(self, state):
        self.anthem_enabled = (state == Qt.Checked)
        anthem_settings = self.config.get_anthem_settings()
        anthem_settings["enabled"] = self.anthem_enabled
        self.config.preferences["anthem"] = anthem_settings
        self.config.save_preferences(self.config.preferences)
        self.anthem_btn.setText(self._get_anthem_button_text())
    
    def manual_bell(self):
        path = self.sounds.get("start", "")
        if path:
            # Останавливаем предыдущее воспроизведение перед запуском нового
            self.sound_player.stop_all()
            if self.bells_enabled and self.sound_player.play(path, "start"):
                self.status_label.setText(f"🔔 {LOCALIZATION[self.current_locale]['btn_bell'].replace('🔔', '').strip()}!")
            elif not self.bells_enabled:
                self.status_label.setText(f"⚠️ Звонки отключены")
            else:
                self.status_label.setText(f"⚠️ Звонок уже воспроизводится")
        else:
            QMessageBox.warning(self, "Ошибка", "Мелодия звонка не выбрана. Выберите в Настройки → Мелодии звонков → На урок")

    def manual_music(self):
        music_settings = self.config.get_music_settings()
        folder = music_settings.get("folder", "")
        if folder:
            # Останавливаем предыдущее воспроизведение перед запуском нового
            self.sound_player.stop_all()
            if self.music_enabled and self.music_player.play_random(folder):
                self.status_label.setText(f"🎵 {LOCALIZATION[self.current_locale]['btn_music'].replace('🎵', '').strip()}!")
            elif not self.music_enabled:
                self.status_label.setText(f"⚠️ Музыка отключена")
            else:
                self.status_label.setText(f"⚠️ Музыка уже воспроизводится")
        else:
            QMessageBox.warning(self, "Ошибка", "Папка с музыкой не выбрана. Выберите в Настройки → Музыка на переменах")
    
    def manual_anthem(self):
        anthem_settings = self.config.get_anthem_settings()
        path = anthem_settings.get("file", "")
        if path:
            # Останавливаем предыдущее воспроизведение перед запуском нового
            self.sound_player.stop_all()
            if self.anthem_enabled and self.sound_player.play(path, "anthem"):
                self.status_label.setText(f"🎼 {LOCALIZATION[self.current_locale]['btn_anthem'].replace('🎼', '').strip()}!")
            elif not self.anthem_enabled:
                self.status_label.setText(f"⚠️ Гимн отключен")
            else:
                self.status_label.setText(f"⚠️ Гимн уже воспроизводится")
        else:
            QMessageBox.warning(self, "Ошибка", "Файл гимна не выбран. Выберите в Настройки → Гимн")

    def check_anthem(self, now):
        """Проверяет, нужно ли автоматически запустить гимн"""
        if not self.anthem_enabled:
            return
        
        anthem_settings = self.config.get_anthem_settings()
        file_path = anthem_settings.get("file", "")
        day = anthem_settings.get("day", "")
        time_str = anthem_settings.get("time", "")
        
        if not file_path or not day or not time_str:
            return
        
        # Проверяем день недели
        today_key = WEEK_DAYS[now.weekday()]
        if today_key != day:
            return
        
        # Проверяем время (с точностью до секунды)
        try:
            h, m = map(int, time_str.split(":"))
            anthem_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            
            # Проверяем, что прошло не более 1 секунды с момента времени гимна
            diff = (now - anthem_time).total_seconds()
            if 0 <= diff < 1:
                # Проверяем, не был ли уже сыгран гимн сегодня
                cache_key = f"anthem_{time_str}"
                if cache_key not in self.scheduled_music:
                    self.scheduled_music[cache_key] = True
                    self.sound_player.stop_all()
                    self.sound_player.play(file_path, "anthem")
                    self.status_label.setText("🎼 Гимн!")
        except:
            pass

    def _get_anthem_button_text(self):
        """Возвращает текст кнопки гимна в зависимости от состояния"""
        texts = LOCALIZATION[self.current_locale]
        btn_text = texts["btn_anthem"].replace("🎼", "").strip()
        if self.anthem_enabled:
            return "▶️ " + btn_text
        else:
            return "⏸️ " + btn_text

    def manual_stop(self):
        """Остановка воспроизведения звонка, музыки и гимна"""
        self.sound_player.stop_all()
        self.status_label.setText(f"🛑 {LOCALIZATION[self.current_locale]['btn_stop'].replace('🛑', '').strip()}!")
    
    def closeEvent(self, event):
        """Остановка всего воспроизведения при закрытии программы"""
        self.sound_player.stop_all()
        
        msg_box = QMessageBox(
            QMessageBox.Question,
            LOCALIZATION[self.current_locale]["confirm_exit_title"],
            LOCALIZATION[self.current_locale]["confirm_exit_text"],
            QMessageBox.Yes | QMessageBox.No,
            self
        )
        msg_box.button(QMessageBox.Yes).setText(LOCALIZATION[self.current_locale]["btn_yes"])
        msg_box.button(QMessageBox.No).setText(LOCALIZATION[self.current_locale]["btn_no"])
        msg_box.setDefaultButton(QMessageBox.No)
        
        reply = msg_box.exec()
        if reply == QMessageBox.Yes:
            self.config.save_preferences(self.config.preferences)
            event.accept()
        else:
            event.ignore()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SchoolBell()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
