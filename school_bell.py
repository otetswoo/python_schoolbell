#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import yaml
import datetime
import platform
import subprocess
import os
import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMenu, QFileDialog, QMessageBox,
    QStyle, QMenuBar, QHeaderView, QToolButton, QDialog, QDialogButtonBox,
    QFormLayout, QLineEdit, QSpinBox, QListWidget, QListWidgetItem, QAbstractItemView
)
from PySide6.QtGui import QAction, QFont, QColor
from PySide6.QtCore import Qt, QTimer, Signal, QEvent

# ------------------ Константы и пути ------------------
ROOT = Path(__file__).resolve().parent
SCHEDULE_PATH = ROOT / "schedule.yml"
PREFERENCES_FILE = ROOT / "preferences.yml"

# Minimal interval between same sound plays (seconds)
MIN_SOUND_INTERVAL = 60

# Colors
COLOR_CURRENT = QColor("#c8e6c9")  # light green
COLOR_SOON = QColor("#fff9c4")     # light yellow
COLOR_NORMAL = QColor("#ffffff")   # white

# Weekdays
WEEK_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
WEEK_DAYS_RU = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
WEEK_DAYS_SHORT = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"]
WEEK_DAYS_SHORT_EN = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

# Localization dictionaries
LOCALIZATION = {
    "ru": {
        "app_title": "Школьные звонки",
        "current_day_label": "📅 Текущий день: {day}",
        "variant_label": "📋 Вариант: {variant}",
        "no_day_selected": "Не выбран",
        "no_variant_selected": "Не выбран",
        "table_headers": ["Начало", "Конец", "Урок"],
        "btn_edit_schedule": "✏️ Редактировать расписание",
        "btn_edit_all": "✏️ Редактировать все дни",
        "status_ready": "✅ Готов к работе",
        "menu_file": "Файл",
        "menu_settings": "⚙️ Настройки",
        "menu_edit": "✏️ Редактировать",
        "menu_tools": "🛠️ Инструменты",
        "action_load": "📂 Загрузить расписание",
        "action_save": "💾 Сохранить расписание",
        "action_today": "📅 Сегодня",
        "action_exit": "🚪 Выход",
        "action_sounds": "🔊 Настроить звуки",
        "action_edit_current": "Текущий день",
        "action_edit_all": "Все дни недели",
        "action_test_start": "▶️ Тест сигнала начала",
        "action_test_end": "⏹️ Тест сигнала конца",
        "action_restore": "🔄 Восстановить все",
        "action_locale_ru": "🇷🇺 Русский",
        "action_locale_en": "🇬🇧 English",
        "variant_usual": "🏫 Обычное расписание",
        "variant_short": "⏱️ Сокращенное расписание",
        "variant_none": "❌ Нет расписания",
        "day_monday": "Понедельник",
        "day_tuesday": "Вторник",
        "day_wednesday": "Среда",
        "day_thursday": "Четверг",
        "day_friday": "Пятница",
        "day_saturday": "Суббота",
        "day_sunday": "Воскресенье",
        "dlg_lesson_title": "Урок",
        "dlg_lesson_num": "Номер урока:",
        "dlg_lesson_start": "Время начала (HH:MM):",
        "dlg_lesson_end": "Время окончания (HH:MM):",
        "dlg_btn_ok": "OK",
        "dlg_btn_cancel": "Отмена",
        "dlg_btn_save": "Сохранить",
        "dlg_editor_title": "Редактор расписания — {day} ({variant})",
        "dlg_btn_add": "Добавить",
        "dlg_btn_edit": "Редактировать",
        "dlg_btn_delete": "Удалить",
        "dlg_btn_up": "Вверх",
        "dlg_btn_down": "Вниз",
        "dlg_template_load": "Загрузить шаблон",
        "dlg_copy_from": "Копировать из дня",
        "msg_select_day_first": "Сначала выберите день",
        "msg_changes_applied": "Изменения применены (не забудьте сохранить файл)",
        "msg_settings_saved": "Настройки сохранены",
        "msg_error_saving": "Ошибка сохранения настроек: {error}",
        "msg_confirm_delete": "Удалить выбранный урок?",
        "msg_select_lesson_edit": "Выберите урок для редактирования",
        "msg_select_lesson_delete": "Выберите урок для удаления",
        "msg_error_time_format": "Время в формате HH:MM",
        "msg_error_overlap": "Перекрытие уроков: {l1} и {l2}",
        "msg_error_start_end": "Урок {num} начало >= конец",
        "msg_template_loaded": "Шаблон '{name}' загружен",
        "msg_template_missing": "Шаблон '{name}' отсутствует",
        "msg_source_empty": "Источник не содержит расписания",
        "msg_copied_from": "Скопировано из {day}",
        "msg_day_variant_selected": "Для {day} выбран вариант: {variant}",
        "msg_showing": "Показано: {day} — {variant}",
        "msg_edit_all_info": "Откроется редактор для каждого дня по очереди.",
        "msg_edit_all_title": "Редактирование всех дней",
        "msg_sound_start": "Звук начала урока",
        "msg_sound_end": "Звук конца урока",
        "msg_select_sound_file": "Выберите звуковой файл",
        "msg_schedule_loaded": "Расписание загружено",
        "msg_schedule_saved": "Расписание сохранено",
        "msg_schedule_load_error": "Ошибка загрузки расписания: {error}",
        "msg_schedule_save_error": "Ошибка сохранения расписания: {error}",
        "msg_today_set": "Показано расписание на сегодня",
        "msg_all_reset": "Все настройки сброшены",
        "msg_test_play": "Тестовое воспроизведение: {sound}",
        "file_filter_yaml": "YAML файлы (*.yml *.yaml)",
        "file_filter_audio": "Аудио файлы (*.wav *.mp3 *.ogg)",
    },
    "en": {
        "app_title": "School Bell",
        "current_day_label": "📅 Current day: {day}",
        "variant_label": "📋 Variant: {variant}",
        "no_day_selected": "Not selected",
        "no_variant_selected": "Not selected",
        "table_headers": ["Start", "End", "Lesson"],
        "btn_edit_schedule": "✏️ Edit Schedule",
        "btn_edit_all": "✏️ Edit All Days",
        "status_ready": "✅ Ready",
        "menu_file": "File",
        "menu_settings": "⚙️ Settings",
        "menu_edit": "✏️ Edit",
        "menu_tools": "🛠️ Tools",
        "action_load": "📂 Load Schedule",
        "action_save": "💾 Save Schedule",
        "action_today": "📅 Today",
        "action_exit": "🚪 Exit",
        "action_sounds": "🔊 Sound Settings",
        "action_edit_current": "Current Day",
        "action_edit_all": "All Week Days",
        "action_test_start": "▶️ Test Start Bell",
        "action_test_end": "⏹️ Test End Bell",
        "action_restore": "🔄 Reset All",
        "action_locale_ru": "🇷🇺 Русский",
        "action_locale_en": "🇬🇧 English",
        "variant_usual": "🏫 Regular Schedule",
        "variant_short": "⏱️ Short Schedule",
        "variant_none": "❌ No Schedule",
        "day_monday": "Monday",
        "day_tuesday": "Tuesday",
        "day_wednesday": "Wednesday",
        "day_thursday": "Thursday",
        "day_friday": "Friday",
        "day_saturday": "Saturday",
        "day_sunday": "Sunday",
        "dlg_lesson_title": "Lesson",
        "dlg_lesson_num": "Lesson #:",
        "dlg_lesson_start": "Start time (HH:MM):",
        "dlg_lesson_end": "End time (HH:MM):",
        "dlg_btn_ok": "OK",
        "dlg_btn_cancel": "Cancel",
        "dlg_btn_save": "Save",
        "dlg_editor_title": "Schedule Editor — {day} ({variant})",
        "dlg_btn_add": "Add",
        "dlg_btn_edit": "Edit",
        "dlg_btn_delete": "Delete",
        "dlg_btn_up": "Up",
        "dlg_btn_down": "Down",
        "dlg_template_load": "Load Template",
        "dlg_copy_from": "Copy from Day",
        "msg_select_day_first": "Please select a day first",
        "msg_changes_applied": "Changes applied (remember to save the file)",
        "msg_settings_saved": "Settings saved",
        "msg_error_saving": "Error saving settings: {error}",
        "msg_confirm_delete": "Delete selected lesson?",
        "msg_select_lesson_edit": "Select a lesson to edit",
        "msg_select_lesson_delete": "Select a lesson to delete",
        "msg_error_time_format": "Time must be in HH:MM format",
        "msg_error_overlap": "Lessons overlap: {l1} and {l2}",
        "msg_error_start_end": "Lesson {num} start >= end",
        "msg_template_loaded": "Template '{name}' loaded",
        "msg_template_missing": "Template '{name}' not found",
        "msg_source_empty": "Source has no schedule",
        "msg_copied_from": "Copied from {day}",
        "msg_day_variant_selected": "Variant selected for {day}: {variant}",
        "msg_showing": "Showing: {day} — {variant}",
        "msg_edit_all_info": "Editor will open for each day sequentially.",
        "msg_edit_all_title": "Edit All Days",
        "msg_sound_start": "Start bell sound",
        "msg_sound_end": "End bell sound",
        "msg_select_sound_file": "Select sound file",
        "msg_schedule_loaded": "Schedule loaded",
        "msg_schedule_saved": "Schedule saved",
        "msg_schedule_load_error": "Error loading schedule: {error}",
        "msg_schedule_save_error": "Error saving schedule: {error}",
        "msg_today_set": "Today's schedule is shown",
        "msg_all_reset": "All settings reset",
        "msg_test_play": "Test playing: {sound}",
        "file_filter_yaml": "YAML files (*.yml *.yaml)",
        "file_filter_audio": "Audio files (*.wav *.mp3 *.ogg)",
    }
}

# Default YAML structure (variant A)
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
            {"num":10, "start": "16:30", "end": "17:10"},
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
        "start": str(ROOT / "start_bell.wav"),
        "end": str(ROOT / "end_bell.wav")
    }
}

# ------------------ Утилиты ------------------
def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def human_date(now: datetime.datetime) -> str:
    months = ["января","февраля","марта","апреля","мая","июня","июля","августа","сентября","октября","ноября","декабря"]
    days = ["Понедельник","Вторник","Среда","Четверг","Пятница","Суббота","Воскресенье"]
    return f"{days[now.weekday()]} {now.day} {months[now.month-1]}, {now:%H:%M}"

def parse_time(t: str) -> datetime.time:
    return datetime.datetime.strptime(t, "%H:%M").time()

def time_to_dt(today: datetime.date, t: str) -> datetime.datetime:
    hh, mm = map(int, t.split(":"))
    return datetime.datetime.combine(today, datetime.time(hh, mm))

# ------------------ CheckableMenu (from your file) ------------------
class CheckableMenu(QMenu):
    optionSelected = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.actions_group = []
        self.current_action = None
        
    def add_checkable_action(self, text, icon=None):
        action = QAction(text, self)
        if icon:
            action.setIcon(icon)
        action.setCheckable(True)
        action.triggered.connect(lambda: self.on_action_triggered(action))
        self.addAction(action)
        self.actions_group.append(action)
        return action
        
    def on_action_triggered(self, triggered_action):
        if triggered_action.isChecked():
            # Снимаем галочки с других действий
            for action in self.actions_group:
                if action != triggered_action:
                    action.setChecked(False)
            self.current_action = triggered_action
            # Определяем вариант по тексту
            txt = triggered_action.text()
            if "Обычное" in txt:
                variant = "usual"
            elif "Сокращенное" in txt or "Сокращённое" in txt:
                variant = "short"
            elif "Нет" in txt:
                variant = "none"
            else:
                variant = "usual"
            self.optionSelected.emit(variant)
        else:
            # Не позволяем снять галочку с выбранного действия
            triggered_action.setChecked(True)
            
    def set_checked(self, variant):
        """Установить выбранный вариант"""
        for action in self.actions_group:
            action_text = action.text()
            if variant == "usual" and "Обычное" in action_text:
                action.setChecked(True)
                self.current_action = action
            elif variant == "short" and ("Сокращенное" in action_text or "Сокращённое" in action_text):
                action.setChecked(True)
                self.current_action = action
            elif variant == "none" and "Нет" in action_text:
                action.setChecked(True)
                self.current_action = action

# ------------------ SingleLessonDialog and ScheduleEditorDialog (variant C) ------------------
class SingleLessonDialog(QDialog):
    def __init__(self, parent, lesson):
        super().__init__(parent)
        self.setWindowTitle("Урок")
        self.resize(320, 140)
        layout = QVBoxLayout()
        form = QFormLayout()
        layout.addLayout(form)

        self.num_spin = QSpinBox()
        self.num_spin.setMinimum(1)
        self.num_spin.setMaximum(99)
        self.start_edit = QLineEdit()
        self.end_edit = QLineEdit()

        form.addRow("Номер урока:", self.num_spin)
        form.addRow("Время начала (HH:MM):", self.start_edit)
        form.addRow("Время окончания (HH:MM):", self.end_edit)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        self.setLayout(layout)

        if lesson:
            self.num_spin.setValue(lesson.get("num",1))
            self.start_edit.setText(lesson.get("start",""))
            self.end_edit.setText(lesson.get("end",""))

    def accept(self):
        s = self.start_edit.text().strip()
        e = self.end_edit.text().strip()
        try:
            datetime.datetime.strptime(s, "%H:%M")
            datetime.datetime.strptime(e, "%H:%M")
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Время в формате HH:MM")
            return
        super().accept()

    def get_data(self):
        return {"num": self.num_spin.value(), "start": self.start_edit.text().strip(), "end": self.end_edit.text().strip()}

class ScheduleEditorDialog(QDialog):
    def __init__(self, parent, day_name_ru: str, current_variant: str, parent_ref):
        super().__init__(parent)
        self.setWindowTitle(f"Редактор расписания — {day_name_ru} ({current_variant})")
        self.resize(600, 420)
        self.parent = parent_ref
        self.current_day = self.parent.current_day  # english key
        self.current_variant = current_variant

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # top controls
        ctrl_layout = QHBoxLayout()
        self.layout.addLayout(ctrl_layout)

        self.template_tool = QToolButton()
        self.template_tool.setText("Загрузить шаблон")
        self.template_tool.setPopupMode(QToolButton.InstantPopup)
        template_menu = QMenu()
        template_menu.addAction("Обычное (usual)", lambda: self.load_template("usual"))
        template_menu.addAction("Сокращённое (short)", lambda: self.load_template("short"))
        template_menu.addAction("Нет уроков (none)", lambda: self.load_template("none"))
        self.template_tool.setMenu(template_menu)
        ctrl_layout.addWidget(self.template_tool)

        self.copy_tool = QToolButton()
        self.copy_tool.setText("Копировать из дня")
        self.copy_tool.setPopupMode(QToolButton.InstantPopup)
        copy_menu = QMenu()
        for i, d in enumerate(WEEK_DAYS_RU):
            key = WEEK_DAYS[i]
            copy_menu.addAction(d, lambda checked=False, k=key: self.copy_from_day(k))
        self.copy_tool.setMenu(copy_menu)
        ctrl_layout.addWidget(self.copy_tool)

        # list of lessons
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.layout.addWidget(self.list)

        # buttons
        btns = QHBoxLayout()
        self.layout.addLayout(btns)
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_lesson)
        btns.addWidget(self.add_btn)
        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_lesson)
        btns.addWidget(self.edit_btn)
        self.del_btn = QPushButton("Удалить")
        self.del_btn.clicked.connect(self.delete_lesson)
        btns.addWidget(self.del_btn)
        self.up_btn = QPushButton("Вверх")
        self.up_btn.clicked.connect(self.move_up)
        btns.addWidget(self.up_btn)
        self.down_btn = QPushButton("Вниз")
        self.down_btn.clicked.connect(self.move_down)
        btns.addWidget(self.down_btn)

        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        self.layout.addWidget(bb)

        # internal data
        self.lessons = []
        self.load_current()

    def load_current(self):
        # load lessons for day/variant
        try:
            self.lessons = [dict(l) for l in self.parent.schedule_variants[self.current_day][self.current_variant]]
        except Exception:
            self.lessons = []
        self.refresh()

    def refresh(self):
        self.list.clear()
        for idx, l in enumerate(self.lessons):
            item = QListWidgetItem(f"{l.get('num', idx+1):>2d} — {l.get('start','--:--')} → {l.get('end','--:--')}")
            self.list.addItem(item)

    def add_lesson(self):
        dlg = SingleLessonDialog(self, None)
        if dlg.exec() == QDialog.Accepted:
            lesson = dlg.get_data()
            lesson["num"] = lesson.get("num") or (len(self.lessons)+1)
            self.lessons.append(lesson)
            self.renumber()
            self.refresh()

    def edit_lesson(self):
        idx = self.list.currentRow()
        if idx < 0:
            self.parent.show_notification("Выберите урок для редактирования")
            return
        dlg = SingleLessonDialog(self, self.lessons[idx])
        if dlg.exec() == QDialog.Accepted:
            self.lessons[idx] = dlg.get_data()
            self.renumber()
            self.refresh()

    def delete_lesson(self):
        idx = self.list.currentRow()
        if idx < 0:
            self.parent.show_notification("Выберите урок для удаления")
            return
        ok = QMessageBox.question(self, "Подтвердите удаление", "Удалить выбранный урок?", QMessageBox.Yes | QMessageBox.No)
        if ok == QMessageBox.Yes:
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
        if idx < len(self.lessons)-1 and idx >= 0:
            self.lessons[idx+1], self.lessons[idx] = self.lessons[idx], self.lessons[idx+1]
            self.renumber()
            self.refresh()
            self.list.setCurrentRow(idx+1)

    def renumber(self):
        for i, l in enumerate(self.lessons):
            l["num"] = i+1

    def load_template(self, name):
        templates = self.parent.templates
        if name in templates:
            self.lessons = [dict(l) for l in templates[name]]
            self.renumber()
            self.refresh()
            self.parent.show_notification(f"Шаблон '{name}' загружен")
        else:
            self.parent.show_notification(f"Шаблон '{name}' отсутствует")

    def copy_from_day(self, day_key):
        src_variant = self.parent.day_variants.get(day_key, "usual")
        src = self.parent.schedule_variants.get(day_key, {}).get(src_variant, [])
        if not src:
            self.parent.show_notification("Источник не содержит расписания")
            return
        self.lessons = [dict(l) for l in src]
        self.renumber()
        self.refresh()
        self.parent.show_notification(f"Скопировано из {day_key}")

    def accept(self):
        # validation: times format and overlaps
        try:
            parsed = []
            for l in self.lessons:
                s = parse_time(l["start"])
                e = parse_time(l["end"])
                if s >= e:
                    QMessageBox.warning(self, "Ошибка", f"Урок {l.get('num')} начало >= конец")
                    return
                parsed.append((s,e,l["num"]))
            parsed_sorted = sorted(parsed, key=lambda x: x[0])
            for i in range(len(parsed_sorted)-1):
                if parsed_sorted[i][1] > parsed_sorted[i+1][0]:
                    QMessageBox.warning(self, "Ошибка", f"Перекрытие уроков: {parsed_sorted[i][2]} и {parsed_sorted[i+1][2]}")
                    return
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Неверный формат времени: {e}")
            return
        # write back
        self.parent.schedule_variants[self.current_day][self.current_variant] = [dict(l) for l in self.lessons]
        super().accept()

# ------------------ Main Window (integrates your UI and features) ------------------
class SchoolBell(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load locale from preferences or default to Russian
        self.current_locale = self.load_locale_preference()
        
        self.update_locale(self.current_locale)
        self.resize(800, 600)

        # state
        self.config = {}
        self.sounds = DEFAULT_SCHEDULE["sounds"].copy()
        self.templates = DEFAULT_SCHEDULE["schedules"].copy()
        # schedule_variants: day_key -> {"usual": [...], "short": [...], "none": []}
        self.schedule_variants = {}
        # mapping day->variant
        self.day_variants = {d: "usual" for d in WEEK_DAYS}
        self.current_day = None  # russian name as in your UI
        self.current_variant = "usual"
        self.last_played = {"start": 0.0, "end": 0.0}
        self.last_checked_day = None

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Info layout (as in your file)
        info_layout = QHBoxLayout()
        self.current_day_label = QLabel(self.tr("current_day_label").format(day=self.t("no_day_selected")))
        self.current_day_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        self.variant_label = QLabel(self.tr("variant_label").format(variant=self.t("no_variant_selected")))
        self.variant_label.setStyleSheet("font-size: 11pt; color: #666;")
        info_layout.addWidget(self.current_day_label)
        info_layout.addStretch()
        info_layout.addWidget(self.variant_label)
        main_layout.addLayout(info_layout)

        # Days buttons (short)
        self.days_layout = QHBoxLayout()
        main_layout.addLayout(self.days_layout)
        self.day_buttons = {}
        self.day_menus = {}
        self.setup_day_buttons()

        # Table
        self.table = QTableWidget(0, 3)
        headers = self.t("table_headers")
        self.table.setHorizontalHeaderLabels(headers)
        # initial column widths similar to your file, but will be stretchable
        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 400)
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.table)

        # Edit buttons area (kept visually as in your original)
        edit_layout = QHBoxLayout()
        self.edit_btn = QPushButton(self.t("btn_edit_schedule"))
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                color: #0d47a1;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #bbdefb;
            }
        """)
        self.edit_btn.clicked.connect(self.edit_current_schedule)
        edit_layout.addWidget(self.edit_btn)

        self.reset_btn = QPushButton("🔄 Восстановить")
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffebee;
                border: 2px solid #f44336;
                border-radius: 6px;
                padding: 8px;
                font-weight: bold;
                color: #c62828;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #ffcdd2;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_to_default)
        self.reset_btn.setToolTip("Восстановить обычное расписание для текущего дня")
        edit_layout.addWidget(self.reset_btn)

        edit_layout.addStretch()
        main_layout.addLayout(edit_layout)

        # Status panel (adapted)
        status_panel = QWidget()
        status_layout = QVBoxLayout()
        status_panel.setLayout(status_layout)
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
                font-size: 11pt;
                min-height: 36px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        # Notifications below status (Variant B)
        self.notifications_label = QLabel("")
        self.notifications_label.setStyleSheet("color: #444; font-size: 11pt; padding:4px;")
        status_layout.addWidget(self.notifications_label)
        main_layout.addWidget(status_panel)

        # Menu
        self.setup_menu()

        # Timers
        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)

        self.bell_timer = QTimer()
        self.bell_timer.timeout.connect(self.check_bells)
        self.bell_timer.start(500)

        # Load config and preferences
        self.load_config()
        self.load_preferences()

        # init table header behavior: make columns relative to width
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        # Set today's schedule on start
        self.set_today_schedule()

        # adjust button colors
        self.update_button_colors()

        # respond to resize for status wrapping
        self.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if ev.type() == QEvent.Resize:
            self.status_label.adjustSize()
        return super().eventFilter(obj, ev)

    # ---------- Menu setup ----------
    def setup_menu(self):
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)

        file_menu = self.menu_bar.addMenu(self.t("menu_file"))
        load_action = QAction(self.t("action_load"), self)
        load_action.triggered.connect(self.load_schedule_dialog)
        load_action.setShortcut("Ctrl+O")
        file_menu.addAction(load_action)

        save_action = QAction(self.t("action_save"), self)
        save_action.triggered.connect(self.save_schedule_dialog)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)

        file_menu.addSeparator()
        today_action = QAction(self.t("action_today"), self)
        today_action.triggered.connect(self.set_today_schedule)
        today_action.setShortcut("Ctrl+T")
        file_menu.addAction(today_action)
        file_menu.addSeparator()
        exit_action = QAction(self.t("action_exit"), self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)

        settings_menu = self.menu_bar.addMenu(self.t("menu_settings"))
        sound_action = QAction(self.t("action_sounds"), self)
        sound_action.triggered.connect(self.select_sounds)
        settings_menu.addAction(sound_action)
        
        # Locale submenu
        locale_menu = settings_menu.addMenu("🌐 Language / Язык")
        locale_ru_action = QAction(self.t("action_locale_ru"), self)
        locale_ru_action.triggered.connect(lambda: self.set_locale("ru"))
        locale_menu.addAction(locale_ru_action)
        locale_en_action = QAction(self.t("action_locale_en"), self)
        locale_en_action.triggered.connect(lambda: self.set_locale("en"))
        locale_menu.addAction(locale_en_action)

        edit_menu = self.menu_bar.addMenu(self.t("menu_edit"))
        edit_current_action = QAction(self.t("action_edit_current"), self)
        edit_current_action.triggered.connect(self.edit_current_schedule)
        edit_current_action.setShortcut("Ctrl+E")
        edit_menu.addAction(edit_current_action)
        edit_all_action = QAction(self.t("action_edit_all"), self)
        edit_all_action.triggered.connect(self.edit_all_schedules)
        edit_menu.addAction(edit_all_action)

        tools_menu = self.menu_bar.addMenu(self.t("menu_tools"))
        test_start = QAction(self.t("action_test_start"), self)
        test_start.triggered.connect(lambda: self.play_sound("start", reason="test"))
        test_start.setShortcut("F1")
        tools_menu.addAction(test_start)
        test_end = QAction(self.t("action_test_end"), self)
        test_end.triggered.connect(lambda: self.play_sound("end", reason="test"))
        test_end.setShortcut("F2")
        tools_menu.addAction(test_end)
        tools_menu.addSeparator()
        restore_all_action = QAction(self.t("action_restore"), self)
        restore_all_action.triggered.connect(self.reset_all_to_default)
        tools_menu.addAction(restore_all_action)

    # ---------- Day buttons ----------
    def setup_day_buttons(self):
        # create compact day buttons with CheckableMenu
        short_names = WEEK_DAYS_SHORT if self.current_locale == "ru" else WEEK_DAYS_SHORT_EN
        full_names = WEEK_DAYS_RU if self.current_locale == "ru" else [LOCALIZATION["en"][f"day_{d}"] for d in WEEK_DAYS]
        
        for i, (short_name, full_name) in enumerate(zip(short_names, full_names)):
            btn = QPushButton(short_name)
            btn.setMinimumHeight(36)
            btn.setMinimumWidth(48)
            btn.setToolTip(full_name)

            menu = CheckableMenu(self)
            normal_action = menu.add_checkable_action(self.t("variant_usual"))
            short_action = menu.add_checkable_action(self.t("variant_short"))
            none_action = menu.add_checkable_action(self.t("variant_none"))
            menu.optionSelected.connect(lambda variant, d=full_name: self.on_day_variant_selected(d, variant))
            btn.setMenu(menu)
            btn.clicked.connect(lambda checked=False, d=full_name: self.on_day_button_clicked(d))
            self.days_layout.addWidget(btn)
            self.day_buttons[full_name] = btn
            self.day_menus[full_name] = menu

    def on_day_button_clicked(self, day_full_name):
        # show that day's schedule
        # convert to english key
        idx = WEEK_DAYS_RU.index(day_full_name)
        key = WEEK_DAYS[idx]
        # set current and display
        self.select_schedule(day_full_name, self.day_variants.get(day_full_name, "usual"))

    def on_day_variant_selected(self, day_full_name, variant):
        # called when user selects variant in menu; day_full_name from lambda above is full Russian name
        # map day_full_name -> english key
        if day_full_name in WEEK_DAYS_RU:
            idx = WEEK_DAYS_RU.index(day_full_name)
            key = WEEK_DAYS[idx]
            # set variant for that day (store per-Russian name to match original)
            self.day_variants[day_full_name] = variant
            # also update internal schedule_variants mapping uses english keys
            # ensure schedule_variants[english] exists
            eng = key
            if eng not in self.schedule_variants:
                self.schedule_variants[eng] = {"usual": [], "short": [], "none": []}
            # apply template copy for variant
            # If template exists, copy it
            tpl = self.templates.get(variant, [])
            self.schedule_variants[eng][variant] = [dict(l) for l in tpl]
            # update UI (if currently showing that day)
            if self.current_day and self.current_day == day_full_name:
                self.select_schedule(day_full_name, variant)
            self.show_notification(f"Для {day_full_name} выбран вариант: {variant}")
            

    def select_schedule(self, day_full_name: str, variant: str):
        # day_full_name is Russian full name (or English if locale is en)
        day_names_ru = WEEK_DAYS_RU if self.current_locale == "ru" else [LOCALIZATION["en"][f"day_{d}"] for d in WEEK_DAYS]
        if day_full_name not in day_names_ru:
            return
        idx = day_names_ru.index(day_full_name)
        key = WEEK_DAYS[idx]  # english key for internal schedules
        self.current_day = day_full_name
        self.current_variant = variant
        # update labels (we keep these as in your UI)
        self.current_day_label.setText(self.tr("current_day_label").format(day=day_full_name))
        variant_names = {
            "usual": self.t("variant_usual"), 
            "short": self.t("variant_short"), 
            "none": self.t("variant_none")
        }
        self.variant_label.setText(self.tr("variant_label").format(variant=variant_names.get(variant, variant)))
        # ensure schedule_variants has data
        if key not in self.schedule_variants:
            # fill from templates
            self.schedule_variants[key] = {
                "usual": [dict(l) for l in self.templates.get("usual",[])],
                "short": [dict(l) for l in self.templates.get("short",[])],
                "none": []
            }
        lessons = self.schedule_variants[key].get(variant, [])
        # fill table
        self.table.setRowCount(0)
        for l in lessons:
            r = self.table.rowCount()
            self.table.insertRow(r)
            item_start = QTableWidgetItem(l.get("start",""))
            item_end = QTableWidgetItem(l.get("end",""))
            item_num = QTableWidgetItem(str(l.get("num","")))
            item_start.setTextAlignment(Qt.AlignCenter)
            item_end.setTextAlignment(Qt.AlignCenter)
            item_num.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r,0,item_start)
            self.table.setItem(r,1,item_end)
            self.table.setItem(r,2,item_num)
        self.update_button_text(day_full_name, variant)
        self.update_button_colors()
        self.show_notification(self.t("msg_showing").format(day=day_full_name, variant=variant))
        

    def update_button_text(self, day_full_name, variant):
        # set small indicator on button text, keep short name but add dot or small mark
        btn = self.day_buttons.get(day_full_name)
        if not btn:
            return
        marks = {"usual": "●", "short": "○", "none": "✖"}
        day_names_ru = WEEK_DAYS_RU if self.current_locale == "ru" else [LOCALIZATION["en"][f"day_{d}"] for d in WEEK_DAYS]
        idx = day_names_ru.index(day_full_name)
        short_names = WEEK_DAYS_SHORT if self.current_locale == "ru" else WEEK_DAYS_SHORT_EN
        short = short_names[idx]
        btn.setText(f"{short} {marks.get(variant,'')}")
        # set menu checked appropriately
        menu = self.day_menus.get(day_full_name)
        if menu:
            menu.set_checked(variant)

    def update_button_colors(self):
        # optional: color current day's button differently
        for full_name, btn in self.day_buttons.items():
            if full_name == self.current_day:
                btn.setStyleSheet("background-color: #e8f5e9;")
            else:
                btn.setStyleSheet("")

    # ---------- Load / Save config ----------
    def load_config(self):
        if SCHEDULE_PATH.exists():
            try:
                with open(SCHEDULE_PATH, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                days_section = data.get("days", {})
                schedules_section = data.get("schedules", {})
                sounds_section = data.get("sounds", {})

                if schedules_section:
                    self.templates = schedules_section
                if days_section:
                    # days_section keys are english weekday names
                    for i, key in enumerate(WEEK_DAYS):
                        val = days_section.get(key, None)
                        if val in ("usual","short","none"):
                            # map to russian day name storage too
                            self.day_variants[WEEK_DAYS_RU[i]] = val
                # build schedule_variants from templates
                for key in WEEK_DAYS:
                    self.schedule_variants[key] = {
                        "usual": [dict(l) for l in self.templates.get("usual",[])],
                        "short": [dict(l) for l in self.templates.get("short",[])],
                        "none": []
                    }
                # sounds
                if sounds_section.get("start"):
                    self.sounds["start"] = sounds_section["start"]
                if sounds_section.get("end"):
                    self.sounds["end"] = sounds_section["end"]

                self.show_notification("Конфигурация загружена")
                
            except Exception as e:
                self.show_notification(f"Ошибка загрузки schedule.yml: {e}")
                
                # fallback to defaults
                self.templates = DEFAULT_SCHEDULE["schedules"].copy()
                for k in WEEK_DAYS:
                    self.schedule_variants[k] = {"usual": [dict(l) for l in self.templates["usual"]], "short": [dict(l) for l in self.templates["short"]], "none": []}
        else:
            # create defaults
            self.templates = DEFAULT_SCHEDULE["schedules"].copy()
            for k in WEEK_DAYS:
                self.schedule_variants[k] = {"usual": [dict(l) for l in self.templates["usual"]], "short": [dict(l) for l in self.templates["short"]], "none": []}
            self.sounds = DEFAULT_SCHEDULE["sounds"].copy()
            self.show_notification("Созданы настройки по умолчанию")
            

    def save_schedule_dialog(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить расписание как YAML", str(SCHEDULE_PATH), "YAML Files (*.yml *.yaml)")
        if not fname:
            return
        try:
            # build data in variant A structure
            days_out = {}
            for i, key in enumerate(WEEK_DAYS):
                # map from russian day variants if exist, else default
                ru = WEEK_DAYS_RU[i]
                days_out[key] = self.day_variants.get(ru, "usual")
            data = {"days": days_out, "schedules": self.templates, "sounds": self.sounds}
            with open(fname, "w", encoding="utf-8") as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            self.show_notification(f"Расписание сохранено в {os.path.basename(fname)}")
            
        except Exception as e:
            self.show_notification(f"Ошибка сохранения: {e}")
            

    def load_schedule_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Выбрать YAML файл расписания", "", "YAML Files (*.yml *.yaml);;All Files (*.*)")
        if not fname:
            return
        try:
            with open(fname, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            days_section = data.get("days", {})
            schedules_section = data.get("schedules", {})
            sounds_section = data.get("sounds", {})
            if schedules_section:
                self.templates = schedules_section
            if days_section:
                for i, key in enumerate(WEEK_DAYS):
                    val = days_section.get(key)
                    if val:
                        self.day_variants[WEEK_DAYS_RU[i]] = val
            # rebuild schedule_variants
            for k in WEEK_DAYS:
                self.schedule_variants[k] = {"usual": [dict(l) for l in self.templates.get("usual",[])], "short": [dict(l) for l in self.templates.get("short",[])], "none": []}
            if sounds_section.get("start"):
                self.sounds["start"] = sounds_section["start"]
            if sounds_section.get("end"):
                self.sounds["end"] = sounds_section["end"]
            self.show_notification(f"Расписание загружено из {os.path.basename(fname)}")
            
            # refresh display
            if self.current_day:
                self.select_schedule(self.current_day, self.day_variants.get(self.current_day, "usual"))
        except Exception as e:
            self.show_notification(f"Ошибка загрузки: {e}")
            

    # ---------- Preferences ----------
    def load_locale_preference(self):
        """Load locale from preferences file, default to 'ru'"""
        if Path(PREFERENCES_FILE).exists():
            try:
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    prefs = yaml.safe_load(f) or {}
                return prefs.get("locale", "ru")
            except Exception:
                pass
        return "ru"

    def load_preferences(self):
        if Path(PREFERENCES_FILE).exists():
            try:
                with open(PREFERENCES_FILE, "r", encoding="utf-8") as f:
                    prefs = yaml.safe_load(f) or {}
                variants = prefs.get("variants", {})
                sounds = prefs.get("sounds", {})
                for i, key in enumerate(WEEK_DAYS_RU):
                    if variants.get(key):
                        self.day_variants[key] = variants[key]
                if sounds.get("start"):
                    self.sounds["start"] = sounds["start"]
                if sounds.get("end"):
                    self.sounds["end"] = sounds["end"]
            except Exception as e:
                pass

    def save_preferences(self, silent=True):
        try:
            prefs = {
                "locale": self.current_locale,
                "variants": self.day_variants, 
                "sounds": self.sounds, 
                "last_saved": datetime.datetime.now().isoformat()
            }
            with open(PREFERENCES_FILE, "w", encoding="utf-8") as f:
                yaml.dump(prefs, f, allow_unicode=True, default_flow_style=False)
            if not silent:
                self.show_notification(self.t("msg_settings_saved"))
        except Exception as e:
            self.show_notification(self.t("msg_error_saving").format(error=e))

    # ---------- Edit actions ----------
    def edit_current_schedule(self):
        if not self.current_day:
            self.show_notification("Сначала выберите день")
            return
        dlg = ScheduleEditorDialog(self, self.current_day, self.current_variant, self)
        if dlg.exec() == QDialog.Accepted:
            self.show_notification("Изменения применены (не забудьте сохранить файл)")
            
            # refresh display
            self.select_schedule(self.current_day, self.current_variant)

    def edit_all_schedules(self):
        # open editor for each day sequentially? Simpler: open editor for Monday and inform user
        QMessageBox.information(self, "Редактирование всех дней", "Откроется редактор для каждого дня по очереди.")
        for i, ru in enumerate(WEEK_DAYS_RU):
            key = WEEK_DAYS[i]
            # open dialog for each day
            dlg = ScheduleEditorDialog(self, ru, "usual", self)
            if dlg.exec() == QDialog.Accepted:
                pass
        self.show_notification("Редактирование всех дней завершено")

    def reset_to_default(self):
        # restore default template for current day/variant
        if not self.current_day:
            self.show_notification(self.t("msg_select_day_first"))
            return
        i = WEEK_DAYS_RU.index(self.current_day)
        eng = WEEK_DAYS[i]
        variant = self.current_variant
        tpl = self.templates.get(variant, [])
        self.schedule_variants[eng][variant] = [dict(l) for l in tpl]
        self.select_schedule(self.current_day, variant)
        self.show_notification("Восстановлено по шаблону для текущего дня")

    def reset_all_to_default(self):
        for k in WEEK_DAYS:
            self.schedule_variants[k]["usual"] = [dict(l) for l in self.templates.get("usual",[])]
            self.schedule_variants[k]["short"] = [dict(l) for l in self.templates.get("short",[])]
            self.schedule_variants[k]["none"] = []
        self.show_notification(self.t("msg_all_reset"))
        
        if self.current_day:
            self.select_schedule(self.current_day, self.day_variants.get(self.current_day, "usual"))

    # ---------- Sounds ----------
    def select_sounds(self):
        start, _ = QFileDialog.getOpenFileName(self, self.t("msg_sound_start"), "", self.t("file_filter_audio"))
        end, _ = QFileDialog.getOpenFileName(self, self.t("msg_sound_end"), "", self.t("file_filter_audio"))
        if start:
            self.sounds["start"] = start
        if end:
            self.sounds["end"] = end
        self.save_preferences(silent=True)
        self.show_notification("Звуки обновлены")
        

    def play_sound(self, typ: str, reason: str="auto"):
        path = self.sounds.get(typ)
        if not path:
            self.show_notification(f"Звук {typ} не задан")
            return False
        if not os.path.exists(path):
            self.show_notification(f"Файл звука не найден: {os.path.basename(path)}")
            return False
        now_ts = time.time()
        last_ts = self.last_played.get(typ, 0.0)
        if now_ts - last_ts < MIN_SOUND_INTERVAL and reason != "test":
            return False
        try:
            if platform.system() == "Windows":
                try:
                    from PySide6.QtMultimedia import QSound
                    QSound.play(path)
                except Exception:
                    subprocess.Popen(["powershell", "-Command", f'(New-Object Media.SoundPlayer "{path}").PlaySync()'])
            else:
                ext = path.lower().split('.')[-1]
                if ext == "wav":
                    subprocess.Popen(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif ext in ("mp3","ogg","flac"):
                    subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.last_played[typ] = now_ts
            return True
        except Exception as e:
            self.show_notification(f"Ошибка воспроизведения: {e}")
            return False

    # ---------- Timers and bell checks ----------
    def update_ui(self):
        now = datetime.datetime.now()
        status = human_date(now)
        cur, seconds_left, next_break = self.get_current_and_next(now)
        if cur:
            mins = seconds_left // 60
            status += f"   —   Идет урок {cur.get('num')}, до конца {mins} мин"
        elif next_break is not None:
            status += f"   —   Перемена, следующая через {next_break//60} мин"
        else:
            status += "   —   Сегодня уроков больше нет"
        self.status_label.setText(status)
        # clear notifications older than some time handled by show_notification via QTimer
        # adjust table highlights
        self.update_table_highlight(now)

    def check_bells(self):
        # called often to detect bell times; main checks are done in update_table_highlight for exact moments
        # Also handle day change
        now = datetime.datetime.now()
        today_key = WEEK_DAYS[now.weekday()]
        if self.last_checked_day is None:
            self.last_checked_day = today_key
        elif self.last_checked_day != today_key:
            # day changed
            self.set_today_schedule()
            self.last_checked_day = today_key
            self.show_notification(f"День сменился: {WEEK_DAYS_RU[WEEK_DAYS.index(today_key)]}")
            

    def get_current_and_next(self, now_dt: datetime.datetime):
        if not self.current_day:
            return (None, None, None)
        idx = WEEK_DAYS_RU.index(self.current_day)
        eng = WEEK_DAYS[idx]
        variant = self.current_variant
        lessons = self.schedule_variants.get(eng, {}).get(variant, [])
        today = now_dt.date()
        parsed = []
        for l in lessons:
            try:
                s = time_to_dt(today, l["start"])
                e = time_to_dt(today, l["end"])
                parsed.append((s,e,l))
            except Exception:
                continue
        for s,e,l in parsed:
            if s <= now_dt <= e:
                return (l, int((e-now_dt).total_seconds()), None)
        for s,e,l in parsed:
            if now_dt < s:
                return (None, None, int((s-now_dt).total_seconds()))
        return (None, None, None)

    def update_table_highlight(self, now_dt: datetime.datetime):
        rows = self.table.rowCount()
        today = now_dt.date()
        for r in range(rows):
            try:
                st = self.table.item(r,0).text()
                en = self.table.item(r,1).text()
                start_dt = time_to_dt(today, st)
                end_dt = time_to_dt(today, en)
                bg = COLOR_NORMAL
                # current
                if start_dt <= now_dt <= end_dt:
                    bg = COLOR_CURRENT
                elif 0 <= (start_dt - now_dt).total_seconds() <= 120:
                    bg = COLOR_SOON
                elif 0 <= (end_dt - now_dt).total_seconds() <= 120:
                    bg = COLOR_SOON
                for c in range(self.table.columnCount()):
                    item = self.table.item(r,c)
                    if item:
                        item.setBackground(bg)
                # automatic play triggers around exact start/end moments
                # start trigger
                if 0 <= (now_dt - start_dt).total_seconds() < 2:
                    self.play_sound_if_needed("start", start_dt)
                # end trigger
                if 0 <= (now_dt - end_dt).total_seconds() < 2:
                    self.play_sound_if_needed("end", end_dt)
            except Exception:
                continue

    def play_sound_if_needed(self, typ: str, event_dt: datetime.datetime):
        now_ts = time.time()
        last_ts = self.last_played.get(typ, 0.0)
        if now_ts - last_ts < MIN_SOUND_INTERVAL:
            return
        ok = self.play_sound(typ, reason="auto")
        if ok:
            self.show_notification(f"Сигнал {'начало' if typ=='start' else 'конец'}")

    # ---------- Notifications ----------
    def show_notification(self, text: str, timeout_ms: int = 4000):
        self.notifications_label.setText(text)
        # schedule clear
        QTimer.singleShot(timeout_ms, lambda: self.notifications_label.setText(""))

    # ---------- Helpers ----------
    def set_today_schedule(self):
        idx = datetime.datetime.today().weekday()
        ru = WEEK_DAYS_RU[idx]
        variant = self.day_variants.get(ru, "usual")
        self.select_schedule(ru, variant)
        self.last_checked_day = WEEK_DAYS[idx]

    def closeEvent(self, event):
        try:
            self.save_preferences(silent=True)
        except Exception as e:
            pass
        super().closeEvent(event)

# ------------------ main ------------------
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SchoolBell()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
