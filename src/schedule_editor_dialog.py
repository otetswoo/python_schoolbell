#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QDialogButtonBox, QMenu, QMessageBox
)

from src.lesson_dialog import LessonDialog
from src.config import WEEK_DAYS_RU, WEEK_DAYS


class ScheduleEditorDialog(QDialog):
    def __init__(self, parent, day_ru, variant, lessons, schedule_variants=None):
        super().__init__(parent)
        variant_ru = {"usual": "обычное", "short": "сокращённое", "none": "нет занятий"}.get(variant, variant)
        self.setWindowTitle(f"Редактор: {day_ru} ({variant_ru})")
        self.resize(500, 400)
        
        self.parent_window = parent
        self.schedule_variants = schedule_variants or {}
        
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
        
        clear_btn = QPushButton("🗑️ Очистить день")
        clear_btn.clicked.connect(self.clear_day)
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        
        # Кнопка "Вставить из" с меню
        paste_btn = QPushButton("📋 Вставить из")
        paste_menu = QMenu(self)
        
        # Шаблоны
        templates_menu = paste_menu.addMenu("📚 Шаблоны")
        if "usual" in self.schedule_variants.get(WEEK_DAYS[0], {}):
            templates_menu.addAction("Обычное расписание").triggered.connect(lambda: self.paste_from_template("usual"))
        if "short" in self.schedule_variants.get(WEEK_DAYS[0], {}):
            templates_menu.addAction("Сокращённое расписание").triggered.connect(lambda: self.paste_from_template("short"))
        
        paste_menu.addSeparator()
        
        # Дни недели
        days_menu = paste_menu.addMenu("📅 Дни недели")
        for i, day in enumerate(WEEK_DAYS_RU):
            days_menu.addAction(day).triggered.connect(lambda checked=False, d=day: self.paste_from_day(d))
        
        paste_btn.setMenu(paste_menu)
        btn_layout.addWidget(paste_btn)
        
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
        next_num = (max((l.get("num", 0) for l in self.lessons), default=0) + 1)
        dlg = LessonDialog(self, {"num": next_num, "start": "08:00", "end": "08:40"})
        if dlg.exec() == QDialog.Accepted:
            new_lesson = dlg.get_data()
            existing = next((i for i, l in enumerate(self.lessons) if l.get("num") == new_lesson["num"]), None)
            if existing is not None:
                existing_start = self.lessons[existing].get("start", "00:00")
                action = "ниже" if new_lesson["start"] >= existing_start else "выше"
                reply = QMessageBox.question(
                    self,
                    "Номер уже существует",
                    f"Урок №{new_lesson['num']} уже задан.\n"
                    f"Заменить существующий урок или вставить {action} него?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.lessons[existing] = new_lesson
                else:
                    self.lessons.append(new_lesson)
            else:
                self.lessons.append(new_lesson)
            self.lessons.sort(key=lambda l: l.get("start", "99:99"))
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
    
    def clear_day(self):
        reply = QMessageBox.question(self, "Подтверждение", 
                                    "Вы уверены, что хотите очистить расписание этого дня?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.lessons = []
            self.refresh()
    
    def paste_from_template(self, template_name):
        """Вставить расписание из шаблона"""
        # Берем шаблон из любого дня (они одинаковые)
        for key in WEEK_DAYS:
            if key in self.schedule_variants and template_name in self.schedule_variants[key]:
                template = self.schedule_variants[key][template_name]
                self.lessons = [dict(l) for l in template]
                self.renumber()
                self.refresh()
                return
        QMessageBox.warning(self, "Ошибка", "Шаблон не найден")
    
    def paste_from_day(self, day_ru):
        """Вставить расписание из другого дня"""
        if day_ru not in WEEK_DAYS_RU:
            return
        
        idx = WEEK_DAYS_RU.index(day_ru)
        key = WEEK_DAYS[idx]
        
        # Получаем вариант для этого дня из родительского окна
        if hasattr(self.parent_window, 'day_variants'):
            variant = self.parent_window.day_variants.get(day_ru, "usual")
        else:
            variant = "usual"
        
        source_lessons = self.schedule_variants.get(key, {}).get(variant, [])
        if not source_lessons:
            QMessageBox.information(self, "Информация", f"Расписание для {day_ru} пустое")
            return
        
        self.lessons = [dict(l) for l in source_lessons]
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
