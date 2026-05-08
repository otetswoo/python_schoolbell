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
from PySide6.QtGui import QAction, QColor, QFont, QPalette
from PySide6.QtCore import Qt, QTimer

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


COLOR_CURRENT_LIGHT = QColor("#c8e6c9")
COLOR_SOON_LIGHT = QColor("#fff9c4")
COLOR_NORMAL_LIGHT = QColor("#ffffff")

COLOR_CURRENT_DARK = QColor("#2e7d32")
COLOR_SOON_DARK = QColor("#f9a825")
COLOR_NORMAL_DARK = QColor("#3c3c3c")

LOCALIZATION = {
    "ru": {
        "app_title": "Школьные звонки",
        "menu_file": "Файл",
        "menu_settings": "Настройки",
        "menu_edit": "Редактировать",
        "action_load": "Загрузить расписание",
        "action_save": "Сохранить расписание",
        "action_today": "Сегодня",
        "action_exit": "Выход",
        "action_sounds": "Звуки",
        "action_music": "Музыка на переменах",
        "action_theme": "Тема",
        "action_locale_ru": "Русский",
        "action_locale_en": "English",
        "btn_edit": "Редактировать расписание",
        "status_ready": "Готов к работе",
        "chk_bells": "Звонки",
        "chk_music": "Музыка на переменах",
        "btn_today": "📅 Сегодня",
        "btn_bell": "🔔 Звонок",
        "btn_music": "🎵 Музыка",
        "confirm_exit_title": "Подтверждение выхода",
        "confirm_exit_text": "Вы уверены, что хотите выйти из программы?",
    },
    "en": {
        "app_title": "School Bell",
        "menu_file": "File",
        "menu_settings": "Settings",
        "menu_edit": "Edit",
        "action_load": "Load Schedule",
        "action_save": "Save Schedule",
        "action_today": "Today",
        "action_exit": "Exit",
        "action_sounds": "Sounds",
        "action_music": "Break Music",
        "action_theme": "Theme",
        "action_locale_ru": "Русский",
        "action_locale_en": "English",
        "btn_edit": "Edit Schedule",
        "status_ready": "Ready",
        "chk_bells": "Bells",
        "chk_music": "Break Music",
        "btn_today": "📅 Today",
        "btn_bell": "🔔 Bell",
        "btn_music": "🎵 Music",
        "confirm_exit_title": "Confirm Exit",
        "confirm_exit_text": "Are you sure you want to exit the program?",
    }
}


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
        self.music_player = MusicPlayer()
        
        self.schedule_variants = {}
        self.day_variants = {d: "usual" for d in WEEK_DAYS_RU}
        self.current_day = None
        self.current_variant = "usual"
        
        self.scheduled_music = {}
        self.bells_enabled = True
        self.music_enabled = False
        
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
        
        info = QHBoxLayout()
        self.day_label = QLabel("День не выбран")
        self.day_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.variant_label = QLabel("Вариант не выбран")
        info.addWidget(self.day_label)
        info.addStretch()
        info.addWidget(self.variant_label)
        layout.addLayout(info)
        
        self.days_layout = QHBoxLayout()
        self.day_buttons = {}
        for i, (short_ru, short_en) in enumerate(zip(WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN)):
            short = short_ru if self.current_locale == "ru" else short_en
            full = WEEK_DAYS_RU[i]
            btn = QPushButton(short)
            btn.setMinimumHeight(36)
            btn.setToolTip(full)
            btn.clicked.connect(lambda checked=False, d=full: self.select_day(d))
            self.days_layout.addWidget(btn)
            self.day_buttons[full] = btn
        layout.addLayout(self.days_layout)
        
        controls_layout = QHBoxLayout()
        
        self.bells_checkbox = QCheckBox(LOCALIZATION[self.current_locale]["chk_bells"])
        self.bells_checkbox.setChecked(True)
        self.bells_checkbox.stateChanged.connect(self.on_bells_toggled)
        controls_layout.addWidget(self.bells_checkbox)
        
        self.music_checkbox = QCheckBox(LOCALIZATION[self.current_locale]["chk_music"])
        music_settings = self.config.get_music_settings()
        self.music_checkbox.setChecked(music_settings.get("enabled", False))
        self.music_checkbox.stateChanged.connect(self.on_music_toggled)
        controls_layout.addWidget(self.music_checkbox)
        
        controls_layout.addStretch()
        
        self.today_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_today"])
        self.today_btn.clicked.connect(self.set_today_schedule)
        controls_layout.addWidget(self.today_btn)
        
        self.bell_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_bell"])
        self.bell_btn.clicked.connect(self.manual_bell)
        controls_layout.addWidget(self.bell_btn)
        
        self.music_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_music"])
        self.music_btn.clicked.connect(self.manual_music)
        controls_layout.addWidget(self.music_btn)
        
        layout.addLayout(controls_layout)
        
        self.table = QTableWidget(0, 3)
        headers = ["Начало", "Конец", "Урок"] if self.current_locale == "ru" else ["Start", "End", "Lesson"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        edit_layout = QHBoxLayout()
        self.edit_btn = QPushButton(LOCALIZATION[self.current_locale]["btn_edit"])
        self.edit_btn.clicked.connect(self.edit_schedule)
        edit_layout.addWidget(self.edit_btn)
        edit_layout.addStretch()
        layout.addLayout(edit_layout)
        
        self.status_label = QLabel(LOCALIZATION[self.current_locale]["status_ready"])
        self.status_label.setStyleSheet("background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.status_label)
        
        self.setup_menu()
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        file_menu = menubar.addMenu(LOCALIZATION[self.current_locale]["menu_file"])
        
        load_act = QAction(LOCALIZATION[self.current_locale]["action_load"], self)
        load_act.triggered.connect(self.load_schedule)
        file_menu.addAction(load_act)
        
        save_act = QAction(LOCALIZATION[self.current_locale]["action_save"], self)
        save_act.triggered.connect(self.save_schedule)
        file_menu.addAction(save_act)
        
        file_menu.addSeparator()
        
        today_act = QAction(LOCALIZATION[self.current_locale]["action_today"], self)
        today_act.triggered.connect(self.set_today_schedule)
        file_menu.addAction(today_act)
        
        file_menu.addSeparator()
        
        exit_act = QAction(LOCALIZATION[self.current_locale]["action_exit"], self)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)
        
        settings_menu = menubar.addMenu(LOCALIZATION[self.current_locale]["menu_settings"])
        
        sounds_act = QAction(LOCALIZATION[self.current_locale]["action_sounds"], self)
        sounds_act.triggered.connect(self.select_sounds)
        settings_menu.addAction(sounds_act)
        
        music_act = QAction(LOCALIZATION[self.current_locale]["action_music"], self)
        music_act.triggered.connect(self.show_music_settings)
        settings_menu.addAction(music_act)
        
        theme_act = QAction(LOCALIZATION[self.current_locale]["action_theme"], self)
        theme_act.triggered.connect(self.show_theme_dialog)
        settings_menu.addAction(theme_act)
        
        locale_menu = settings_menu.addMenu("Language / Язык")
        
        ru_act = QAction(LOCALIZATION[self.current_locale]["action_locale_ru"], self)
        ru_act.triggered.connect(lambda: self.set_locale("ru"))
        locale_menu.addAction(ru_act)
        
        en_act = QAction(LOCALIZATION[self.current_locale]["action_locale_en"], self)
        en_act.triggered.connect(lambda: self.set_locale("en"))
        locale_menu.addAction(en_act)
    
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
        
        self.day_label.setText(f"📅 {day_ru}")
        variant_names = {"usual": "Обычное", "short": "Сокращённое", "none": "Нет"}
        self.variant_label.setText(f"📋 {variant_names.get(variant, variant)}")
        
        for d, btn in self.day_buttons.items():
            btn.setStyleSheet("background-color: #e8f5e9;" if d == day_ru else "")
    
    def set_today_schedule(self):
        today = datetime.datetime.today()
        idx = today.weekday()
        day_ru = WEEK_DAYS_RU[idx]
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
        
        dlg = ScheduleEditorDialog(self, self.current_day, self.current_variant, lessons)
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
        
        is_dark = self.current_theme == "dark"
        color_current = COLOR_CURRENT_DARK if is_dark else COLOR_CURRENT_LIGHT
        color_soon = COLOR_SOON_DARK if is_dark else COLOR_SOON_LIGHT
        color_normal = COLOR_NORMAL_DARK if is_dark else COLOR_NORMAL_LIGHT
        
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
        
        now_ts = datetime.datetime.now().timestamp()
        event_ts = event_time.timestamp()
        
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
                
                templates = {}
                for key in WEEK_DAYS:
                    for var in ["usual", "short"]:
                        if var not in templates:
                            templates[var] = self.schedule_variants[key].get(var, [])
                
                data = {"days": days_out, "schedules": templates, "sounds": self.sounds}
                with open(fname, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
    
    def select_sounds(self):
        start, _ = QFileDialog.getOpenFileName(self, "Звук начала", "", "Audio (*.wav *.mp3)")
        end, _ = QFileDialog.getOpenFileName(self, "Звук конца", "", "Audio (*.wav *.mp3)")
        
        if start:
            self.sounds["start"] = start
            self.config.set_sound("start", start)
        if end:
            self.sounds["end"] = end
            self.config.set_sound("end", end)
        
        self.config.save_preferences(self.config.preferences)
    
    def show_music_settings(self):
        dlg = MusicSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            music = self.config.get_music_settings()
            if music.get("folder"):
                self.music_player.set_music_folder(music["folder"])
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
                QLabel { color: #ffffff; }
                QMenuBar { background-color: #3c3c3c; color: #ffffff; }
                QMenu { background-color: #3c3c3c; color: #ffffff; }
                QCheckBox { color: #ffffff; }
                QCheckBox::indicator { background-color: #555; border: 1px solid #777; }
                QCheckBox::indicator:checked { background-color: #4caf50; }
                QStatusBar, QLabel#status { background-color: #3c3c3c; color: #ffffff; }
            """)
        else:
            self.setStyleSheet("")
    
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
        self.today_btn.setText(texts["btn_today"])
        
        headers = ["Начало", "Конец", "Урок"] if locale == "ru" else ["Start", "End", "Lesson"]
        self.table.setHorizontalHeaderLabels(headers)
    
    def on_bells_toggled(self, state):
        self.bells_enabled = (state == Qt.Checked)
    
    def on_music_toggled(self, state):
        self.music_enabled = (state == Qt.Checked)
        music_settings = self.config.get_music_settings()
        music_settings["enabled"] = self.music_enabled
        self.config.preferences["music"] = music_settings
        self.config.save_preferences(self.config.preferences)
    
    def manual_bell(self):
        now = datetime.datetime.now()
        self.sound_player.play("start", self.sounds.get("start", ""))
        self.status_label.setText(f"🔔 {LOCALIZATION[self.current_locale]['btn_bell'].replace('🔔', '').strip()}!")
    
    def manual_music(self):
        music_settings = self.config.get_music_settings()
        folder = music_settings.get("folder", "")
        if folder:
            self.music_player.play_random(folder)
            self.status_label.setText(f"🎵 {LOCALIZATION[self.current_locale]['btn_music'].replace('🎵', '').strip()}!")
        else:
            QMessageBox.warning(self, "Ошибка", "Папка с музыкой не выбрана. Выберите в Настройки → Музыка на переменах")
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            LOCALIZATION[self.current_locale]["confirm_exit_title"],
            LOCALIZATION[self.current_locale]["confirm_exit_text"],
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.save_preferences(self.config.preferences)
            event.accept()
        else:
            event.ignore()


class ScheduleEditorDialog(QDialog):
    def __init__(self, parent, day_ru, variant, lessons):
        super().__init__(parent)
        self.setWindowTitle(f"Редактор: {day_ru} ({variant})")
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.list = QListWidget()
        layout.addWidget(self.list)
        
        self.lessons = [dict(l) for l in lessons]
        self.refresh()
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_lesson)
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("Изменить")
        edit_btn.clicked.connect(self.edit_lesson)
        btn_layout.addWidget(edit_btn)
        
        del_btn = QPushButton("Удалить")
        del_btn.clicked.connect(self.delete_lesson)
        btn_layout.addWidget(del_btn)
        
        btn_layout.addStretch()
        
        up_btn = QPushButton("↑")
        up_btn.clicked.connect(self.move_up)
        btn_layout.addWidget(up_btn)
        
        down_btn = QPushButton("↓")
        down_btn.clicked.connect(self.move_down)
        btn_layout.addWidget(down_btn)
        
        layout.addLayout(btn_layout)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
    
    def refresh(self):
        self.list.clear()
        for i, l in enumerate(self.lessons):
            item = QListWidgetItem(f"{l.get('num', i+1):>2d} — {l.get('start','--:--')} → {l.get('end','--:--')}")
            self.list.addItem(item)
    
    def add_lesson(self):
        dlg = LessonDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.lessons.append(dlg.get_data())
            self.renumber()
            self.refresh()
    
    def edit_lesson(self):
        idx = self.list.currentRow()
        if idx < 0:
            return
        dlg = LessonDialog(self, self.lessons[idx])
        if dlg.exec() == QDialog.Accepted:
            self.lessons[idx] = dlg.get_data()
            self.renumber()
            self.refresh()
    
    def delete_lesson(self):
        idx = self.list.currentRow()
        if idx < 0:
            return
        self.lessons.pop(idx)
        self.renumber()
        self.refresh()
    
    def move_up(self):
        idx = self.list.currentRow()
        if idx > 0:
            self.lessons[idx-1], self.lessons[idx] = self.lessons[idx], self.lessons[idx-1]
            self.renumber()
            self.refresh()
            self.list.setCurrentRow(idx-1)
    
    def move_down(self):
        idx = self.list.currentRow()
        if 0 <= idx < len(self.lessons) - 1:
            self.lessons[idx+1], self.lessons[idx] = self.lessons[idx], self.lessons[idx+1]
            self.renumber()
            self.refresh()
            self.list.setCurrentRow(idx+1)
    
    def renumber(self):
        for i, l in enumerate(self.lessons):
            l["num"] = i + 1
    
    def get_lessons(self):
        return self.lessons


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SchoolBell()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
