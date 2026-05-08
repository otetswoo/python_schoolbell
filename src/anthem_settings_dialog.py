#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                                QLabel, QFileDialog, QComboBox, QTimeEdit, QCheckBox)
from PySide6.QtCore import Qt, QTime
from src.config_manager import ConfigManager
from src.config import WEEK_DAYS_RU, WEEK_DAYS


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
        
        # Чекбокс включения
        self.enabled_checkbox = QCheckBox("Включить воспроизведение гимна")
        layout.addWidget(self.enabled_checkbox)
        
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
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(8, 30))
        self.time_edit.setDisplayFormat("HH:mm")
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)
        
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
        self.enabled_checkbox.setChecked(anthem.get("enabled", False))
        
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
            self.time_edit.setTime(QTime(h, m))
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
        self.enabled_checkbox.setChecked(False)
    
    def accept(self):
        # Сохраняем настройки
        self.config.set_anthem_file(self.config.get_anthem_settings().get("file", ""))
        
        day = self.day_combo.currentData()
        self.config.set_anthem_day(day)
        
        time_str = self.time_edit.time().toString("HH:mm")
        self.config.set_anthem_time(time_str)
        
        anthem = self.config.get_anthem_settings()
        anthem["enabled"] = self.enabled_checkbox.isChecked()
        self.config.preferences["anthem"] = anthem
        
        super().accept()
