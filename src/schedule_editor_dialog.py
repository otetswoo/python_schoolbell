#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QDialogButtonBox, QMessageBox
)
from src.lesson_dialog import LessonDialog


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
