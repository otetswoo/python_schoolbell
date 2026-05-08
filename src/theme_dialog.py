#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QRadioButton, QLabel, QButtonGroup
from src.config_manager import ConfigManager


class ThemeDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎨 Тема оформления")
        self.resize(300, 200)
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Выберите тему оформления приложения:")
        layout.addWidget(info)
        
        self.theme_group = QButtonGroup(self)
        
        self.light_radio = QRadioButton("☀️ Светлая тема")
        self.light_radio.setChecked(True)
        self.theme_group.addButton(self.light_radio)
        layout.addWidget(self.light_radio)
        
        self.dark_radio = QRadioButton("🌙 Тёмная тема")
        self.theme_group.addButton(self.dark_radio)
        layout.addWidget(self.dark_radio)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        current_theme = self.config.get_theme()
        if current_theme == "dark":
            self.dark_radio.setChecked(True)
        else:
            self.light_radio.setChecked(True)
    
    def get_theme(self):
        if self.dark_radio.isChecked():
            return "dark"
        return "light"
