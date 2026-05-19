#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QComboBox, QSpinBox
)
from src.config_manager import ConfigManager
from src.config import WEEK_DAYS_RU, WEEK_DAYS
from src.volume_control import VolumeControl


class AnthemSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎼 Гимн")
        self.resize(500, 350)
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Настройка воспроизведения Гимна.\n"
                     "Выберите файл, день недели и время для автоматического воспроизведения.\n"
                     "Гимн будет звучать в указанное время каждый выбранный день.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Выбор файла
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setStyleSheet("font-weight: bold; padding: 10px;")
        file_layout.addWidget(self.file_label)
        
        self.select_file_btn = QPushButton("📁 Выбрать файл")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        layout.addLayout(file_layout)
        
        # Выбор дня недели
        day_layout = QHBoxLayout()
        day_label = QLabel("День недели:")
        day_layout.addWidget(day_label)
        
        self.day_combo = QComboBox()
        for i, day_ru in enumerate(WEEK_DAYS_RU):
            self.day_combo.addItem(day_ru, WEEK_DAYS[i])
        day_layout.addWidget(self.day_combo)
        day_layout.addStretch()
        layout.addLayout(day_layout)
        
        # Выбор времени
        time_layout = QHBoxLayout()
        time_label = QLabel("Время:")
        time_layout.addWidget(time_label)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(8)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(30)
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minute_spin)
        time_layout.addStretch()
        layout.addLayout(time_layout)

        self.volume_control = VolumeControl("Громкость гимна:", self.config.get_volume("anthem"), self)
        self.volume_control.value_changed.connect(lambda v: self.config.set_volume("anthem", v))
        layout.addWidget(self.volume_control)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.clear_btn = QPushButton("❌ Очистить")
        self.clear_btn.clicked.connect(self.clear_settings)
        btn_layout.addWidget(self.clear_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
        
        self.load_current_settings()
    
    def load_current_settings(self):
        anthem = self.config.get_anthem_settings()
        
        file_path = anthem.get("file", "")
        if file_path:
            self.file_label.setText(f"Файл: {file_path}")
        
        day = anthem.get("day", "monday")
        for i in range(self.day_combo.count()):
            if self.day_combo.itemData(i) == day:
                self.day_combo.setCurrentIndex(i)
                break
        
        time_str = anthem.get("time", "08:30")
        try:
            h, m = map(int, time_str.split(":"))
            self.hour_spin.setValue(h)
            self.minute_spin.setValue(m)
        except:
            pass
    
    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл гимна", "", "Audio (*.wav *.mp3)")
        if path:
            self.config.set_anthem_file(path)
            self.file_label.setText(f"Файл: {path}")
    
    def clear_settings(self):
        self.config.set_anthem_file("")
        self.file_label.setText("Файл: не выбран")
    
    def accept(self):
        # Сохраняем настройки
        day = self.day_combo.currentData()
        self.config.set_anthem_day(day)
        
        time_str = f"{self.hour_spin.value():02d}:{self.minute_spin.value():02d}"
        self.config.set_anthem_time(time_str)
        self.config.set_volume("anthem", self.volume_control.value())
        
        super().accept()
