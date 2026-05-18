#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFormLayout, QLineEdit, QSpinBox, QComboBox, QListWidget, QListWidgetItem, QMessageBox, QDialogButtonBox
from PySide6.QtCore import Qt
from src.config import BREAK_DURATIONS


class LessonDialog(QDialog):
    def __init__(self, parent, lesson=None, next_start=None):
        super().__init__(parent)
        self.setWindowTitle("Урок")
        self.resize(350, 200)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        form = QFormLayout()
        layout.addLayout(form)
        
        self.num_spin = QSpinBox()
        self.num_spin.setMinimum(1)
        self.num_spin.setMaximum(99)
        form.addRow("Номер урока:", self.num_spin)
        
        self.start_edit = QLineEdit()
        self.start_edit.setPlaceholderText("HH:MM")
        form.addRow("Время начала:", self.start_edit)
        
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(20)
        self.duration_spin.setMaximum(120)
        self.duration_spin.setValue(40)
        self.duration_spin.setSuffix(" мин")
        form.addRow("Длительность урока:", self.duration_spin)
        
        self.break_combo = QComboBox()
        for b in BREAK_DURATIONS:
            self.break_combo.addItem(f"{b} мин", b)
        self.break_combo.setCurrentIndex(1)
        form.addRow("Перемена после урока:", self.break_combo)
        
        self.end_label = QLabel("--:--")
        self.end_label.setStyleSheet("font-weight: bold; color: #2196f3;")
        form.addRow("Окончание урока:", self.end_label)
        
        self.start_edit.textChanged.connect(self.update_end_time)
        self.duration_spin.valueChanged.connect(self.update_end_time)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.validate_and_accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        
        if lesson:
            self.num_spin.setValue(lesson.get("num", 1))
            self.start_edit.setText(lesson.get("start", ""))
            if "end" in lesson and "start" in lesson:
                try:
                    from datetime import datetime
                    start = datetime.strptime(lesson["start"], "%H:%M")
                    end = datetime.strptime(lesson["end"], "%H:%M")
                    duration = int((end - start).total_seconds() / 60)
                    self.duration_spin.setValue(duration)
                except:
                    pass
        
        self.update_end_time()
    
    def update_end_time(self):
        start_text = self.start_edit.text().strip()
        try:
            from datetime import datetime, timedelta
            start = datetime.strptime(start_text, "%H:%M")
            duration = self.duration_spin.value()
            end = start + timedelta(minutes=duration)
            self.end_label.setText(end.strftime("%H:%M"))
        except:
            self.end_label.setText("--:--")
    
    def validate_and_accept(self):
        start_text = self.start_edit.text().strip()
        try:
            from datetime import datetime
            datetime.strptime(start_text, "%H:%M")
        except:
            QMessageBox.warning(self, "Ошибка", "Время в формате HH:MM")
            return
        super().accept()
    
    def get_data(self):
        from datetime import datetime, timedelta
        start = datetime.strptime(self.start_edit.text().strip(), "%H:%M")
        duration = self.duration_spin.value()
        end = start + timedelta(minutes=duration)
        break_duration = self.break_combo.currentData()
        
        return {
            "num": self.num_spin.value(),
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "break": break_duration
        }
