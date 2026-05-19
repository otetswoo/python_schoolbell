#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFormLayout, QSpinBox, QComboBox, QMessageBox, QDialogButtonBox, QWidget, QHBoxLayout
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
        
        time_widget = QWidget()
        time_layout = QHBoxLayout(time_widget)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.start_hour = QSpinBox()
        self.start_hour.setRange(0, 23)
        self.start_minute = QSpinBox()
        self.start_minute.setRange(0, 59)
        time_layout.addWidget(self.start_hour)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.start_minute)
        time_layout.addStretch()
        form.addRow("Время начала:", time_widget)
        
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
        
        self.start_hour.valueChanged.connect(self.update_end_time)
        self.start_minute.valueChanged.connect(self.update_end_time)
        self.duration_spin.valueChanged.connect(self.update_end_time)
        
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("OK")
        bb.button(QDialogButtonBox.Cancel).setText("Отмена")
        bb.accepted.connect(self.validate_and_accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)
        
        self.start_hour.setValue(8)
        self.start_minute.setValue(0)
        if lesson:
            self.num_spin.setValue(lesson.get("num", 1))
            start_text = lesson.get("start", "08:00")
            h, m = map(int, start_text.split(":"))
            self.start_hour.setValue(h)
            self.start_minute.setValue(m)
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
    
    def _start_text(self):
        return f"{self.start_hour.value():02d}:{self.start_minute.value():02d}"

    def update_end_time(self):
        from datetime import datetime, timedelta
        start = datetime.strptime(self._start_text(), "%H:%M")
        duration = self.duration_spin.value()
        end = start + timedelta(minutes=duration)
        self.end_label.setText(end.strftime("%H:%M"))
    
    def validate_and_accept(self):
        super().accept()
    
    def get_data(self):
        from datetime import datetime, timedelta
        start = datetime.strptime(self._start_text(), "%H:%M")
        duration = self.duration_spin.value()
        end = start + timedelta(minutes=duration)
        break_duration = self.break_combo.currentData()
        
        return {
            "num": self.num_spin.value(),
            "start": start.strftime("%H:%M"),
            "end": end.strftime("%H:%M"),
            "break": break_duration
        }
