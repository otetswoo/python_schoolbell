#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from src.config_manager import ConfigManager


class ThemeDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎨 Тема оформления")
        self.resize(300, 150)
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Приложение использует светлую тему оформления в стиле GNOME Adwaita.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
    
    def get_theme(self):
        return "light"
