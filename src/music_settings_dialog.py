#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from src.config_manager import ConfigManager


class MusicSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎵 Музыка на переменах")
        self.resize(500, 400)
        self.config = config_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Выберите папку с музыкой для воспроизведения на переменах.\n"
                     "Через 2 минуты после звонка на перемену будет играть случайный трек.\n"
                     "Треки не повторяются в течение дня.")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.folder_label = QLabel("Папка: не выбрана")
        self.folder_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(self.folder_label)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        
        self.select_btn = QPushButton("📁 Выбрать папку")
        self.select_btn.clicked.connect(self.select_folder)
        btn_layout.addWidget(self.select_btn)
        
        self.clear_btn = QPushButton("❌ Очистить")
        self.clear_btn.clicked.connect(self.clear_folder)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)
        
        self.load_current_settings()
    
    def load_current_settings(self):
        music = self.config.get_music_settings()
        folder = music.get("folder", "")
        if folder:
            self.folder_label.setText(f"Папка: {folder}")
            self.update_file_list(folder)
        else:
            self.folder_label.setText("Папка: не выбрана")
            self.file_list.clear()
    
    def update_file_list(self, folder):
        self.file_list.clear()
        from pathlib import Path
        p = Path(folder)
        if not p.exists():
            return
        
        extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma"}
        files = [f.name for f in p.iterdir() if f.is_file() and f.suffix.lower() in extensions]
        
        if not files:
            item = QListWidgetItem("📭 В папке нет аудиофайлов")
            item.setForeground(Qt.gray)
            self.file_list.addItem(item)
        else:
            for f in sorted(files):
                self.file_list.addItem(f"🎵 {f}")
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой")
        if folder:
            self.config.set_music_folder(folder)
            self.folder_label.setText(f"Папка: {folder}")
            self.update_file_list(folder)
    
    def clear_folder(self):
        self.config.set_music_folder("")
        self.folder_label.setText("Папка: не выбрана")
        self.file_list.clear()
        item = QListWidgetItem("✅ Музыка отключена")
        item.setForeground(Qt.green)
        self.file_list.addItem(item)
