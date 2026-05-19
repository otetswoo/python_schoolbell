#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QListWidgetItem, QDialogButtonBox, QTabWidget, QWidget, QLabel,
    QMessageBox
)

from src.lesson_dialog import LessonDialog
from src.config import WEEK_DAYS


class TemplatesEditorDialog(QDialog):
    """Диалог редактирования шаблонов расписания (обычное и сокращённое)"""
    
    def __init__(self, parent, schedule_variants, config):
        super().__init__(parent)
        self.setWindowTitle("📚 Редактирование шаблонов расписания")
        self.resize(600, 500)
        
        self.schedule_variants = schedule_variants
        self.config = config
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Редактирование шаблонов расписания.\nИзменения применятся ко всем дням недели.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Вкладки для разных типов расписания
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Создаем вкладки для обычного и сокращённого расписания
        self.usual_widget = self.create_template_tab("usual", "Обычное расписание")
        self.short_widget = self.create_template_tab("short", "Сокращённое расписание")
        
        self.tabs.addTab(self.usual_widget, "📅 Обычное")
        self.tabs.addTab(self.short_widget, "⏱️ Сокращённое")
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("OK")
        bb.button(QDialogButtonBox.Cancel).setText("Отмена")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
    
    def create_template_tab(self, template_type, title):
        """Создает вкладку для редактирования шаблона"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        # Загружаем текущий шаблон
        lessons = []
        for key in WEEK_DAYS:
            if key in self.schedule_variants and template_type in self.schedule_variants[key]:
                lessons = self.schedule_variants[key][template_type]
                break
        
        self.lessons_data = {template_type: [dict(l) for l in lessons]}
        self.refresh_list(template_type, list_widget)
        
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Добавить урок")
        add_btn.clicked.connect(lambda checked=False, t=template_type, lw=list_widget: self.add_lesson(t, lw))
        btn_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("✏️ Изменить")
        edit_btn.clicked.connect(lambda checked=False, t=template_type, lw=list_widget: self.edit_lesson(t, lw))
        btn_layout.addWidget(edit_btn)
        
        del_btn = QPushButton("🗑️ Удалить")
        del_btn.clicked.connect(lambda checked=False, t=template_type, lw=list_widget: self.delete_lesson(t, lw))
        btn_layout.addWidget(del_btn)
        
        clear_btn = QPushButton("🧹 Очистить шаблон")
        clear_btn.clicked.connect(lambda checked=False, t=template_type: self.clear_template(t))
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Сохраняем виджет списка в атрибуте для доступа из других методов
        setattr(self, f"list_widget_{template_type}", list_widget)
        
        return widget
    
    def refresh_list(self, template_type, list_widget=None):
        """Обновляет список уроков для шаблона"""
        if list_widget is None:
            list_widget = getattr(self, f"list_widget_{template_type}", None)
        if list_widget is None:
            return
        
        list_widget.clear()
        
        lessons = self.lessons_data.get(template_type, [])
        for i, l in enumerate(lessons):
            item = QListWidgetItem(f"{l.get('num', i+1):>2d} — {l.get('start','--:--')} → {l.get('end','--:--')}")
            list_widget.addItem(item)
    
    def add_lesson(self, template_type, list_widget=None):
        dlg = LessonDialog(self)
        if dlg.exec() == QDialog.Accepted:
            if template_type not in self.lessons_data:
                self.lessons_data[template_type] = []
            self.lessons_data[template_type].append(dlg.get_data())
            self.renumber(template_type)
            self.refresh_list(template_type, list_widget)
    
    def edit_lesson(self, template_type, list_widget=None):
        if list_widget is None:
            list_widget = getattr(self, f"list_widget_{template_type}", None)
        if list_widget is None:
            return
        
        idx = list_widget.currentRow()
        if idx < 0 or template_type not in self.lessons_data:
            return
        
        lessons = self.lessons_data[template_type]
        if idx >= len(lessons):
            return
        
        dlg = LessonDialog(self, lessons[idx])
        if dlg.exec() == QDialog.Accepted:
            lessons[idx] = dlg.get_data()
            self.renumber(template_type)
            self.refresh_list(template_type, list_widget)
    
    def delete_lesson(self, template_type, list_widget=None):
        if list_widget is None:
            list_widget = getattr(self, f"list_widget_{template_type}", None)
        if list_widget is None:
            return
        
        idx = list_widget.currentRow()
        if idx < 0 or template_type not in self.lessons_data:
            return
        
        lessons = self.lessons_data[template_type]
        if idx >= len(lessons):
            return
        
        lessons.pop(idx)
        self.renumber(template_type)
        self.refresh_list(template_type, list_widget)
    
    def clear_template(self, template_type):
        reply = QMessageBox.question(self, "Подтверждение", 
                                    f"Вы уверены, что хотите очистить '{'Обычное' if template_type == 'usual' else 'Сокращённое'}' расписание?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.lessons_data[template_type] = []
            self.refresh_list(template_type)
    
    def renumber(self, template_type):
        lessons = self.lessons_data.get(template_type, [])
        for i, l in enumerate(lessons):
            l["num"] = i + 1
    
    def get_templates(self):
        """Возвращает словрь с шаблонами"""
        return self.lessons_data
