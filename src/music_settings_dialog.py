#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QListWidget, QListWidgetItem
)

from src.config_manager import ConfigManager


class MusicSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎵 Музыка на переменах")
        self.resize(620, 500)
        self.config = config_manager

        self.music_folders = []
        self.track_items = []

        layout = QVBoxLayout(self)

        info = QLabel(
            "Выберите одну или несколько папок с музыкой для воспроизведения на переменах.\n"
            "Через 2 минуты после звонка на перемену будет играть случайный трек.\n"
            "Можно исключить композиции из воспроизведения, сняв галочку."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.folder_label = QLabel("Папки: не выбраны")
        self.folder_label.setStyleSheet("font-weight: bold; padding: 6px;")
        layout.addWidget(self.folder_label)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        controls = QHBoxLayout()
        self.select_btn = QPushButton("📁 Выбрать папки")
        self.select_btn.clicked.connect(self.select_folders)
        controls.addWidget(self.select_btn)

        self.select_all_btn = QPushButton("✅ Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all_tracks)
        controls.addWidget(self.select_all_btn)

        self.clear_btn = QPushButton("❌ Очистить")
        self.clear_btn.clicked.connect(self.clear_folders)
        controls.addWidget(self.clear_btn)

        controls.addStretch()
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        controls.addWidget(self.ok_btn)
        layout.addLayout(controls)

        self.load_current_settings()

    def _audio_files(self):
        extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma"}
        files = []
        for folder in self.music_folders:
            p = Path(folder)
            if not p.exists():
                continue
            for f in p.iterdir():
                if f.is_file() and f.suffix.lower() in extensions:
                    files.append(f)
        return sorted(files, key=lambda x: (str(x.parent), x.name.lower()))

    def load_current_settings(self):
        music = self.config.get_music_settings()
        self.music_folders = music.get("folders", [])
        if not self.music_folders and music.get("folder"):
            self.music_folders = [music.get("folder")]
        self._update_folder_label()
        self.update_file_list(music.get("selected_tracks", []))

    def _update_folder_label(self):
        if not self.music_folders:
            self.folder_label.setText("Папки: не выбраны")
        elif len(self.music_folders) == 1:
            self.folder_label.setText(f"Папка: {self.music_folders[0]}")
        else:
            self.folder_label.setText(f"Папок выбрано: {len(self.music_folders)}")

    def update_file_list(self, selected_tracks=None):
        self.file_list.clear()
        self.track_items = []
        selected = set(selected_tracks or [])
        files = self._audio_files()

        if not files:
            item = QListWidgetItem("📭 В выбранных папках нет аудиофайлов")
            item.setForeground(Qt.gray)
            self.file_list.addItem(item)
            return

        for track in files:
            rel_name = f"{track.parent.name}/{track.name}"
            item = QListWidgetItem(f"🎵 {rel_name}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setData(Qt.UserRole, str(track))
            item.setCheckState(Qt.Checked if not selected or str(track) in selected else Qt.Unchecked)
            self.file_list.addItem(item)
            self.track_items.append(item)

    def _save_music_state(self):
        selected_tracks = [
            item.data(Qt.UserRole)
            for item in self.track_items
            if item.checkState() == Qt.Checked
        ]
        self.config.set_music_folders(self.music_folders)
        music = self.config.get_music_settings()
        music["selected_tracks"] = selected_tracks
        self.config.preferences["music"] = music

    def select_folders(self):
        folders = QFileDialog.getExistingDirectoryUrl(self, "Выберите папку с музыкой")
        # fallback for platforms without URL-based multi-select
        if folders and folders.isValid():
            first = folders.toLocalFile()
            if first and first not in self.music_folders:
                self.music_folders.append(first)
                self._update_folder_label()
                self.update_file_list()
                self._save_music_state()

    def select_all_tracks(self):
        for item in self.track_items:
            item.setCheckState(Qt.Checked)
        self._save_music_state()

    def clear_folders(self):
        self.music_folders = []
        self.config.set_music_folders([])
        music = self.config.get_music_settings()
        music["selected_tracks"] = []
        self.config.preferences["music"] = music
        self._update_folder_label()
        self.file_list.clear()
        item = QListWidgetItem("✅ Музыка отключена")
        item.setForeground(Qt.green)
        self.file_list.addItem(item)

    def accept(self):
        self._save_music_state()
        super().accept()
