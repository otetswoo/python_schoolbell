#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QSpinBox
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
        self.folder_items = []

        layout = QVBoxLayout(self)

        info = QLabel(
            "Выберите одну или несколько папок с музыкой для воспроизведения на переменах.\n"
            "Через 2 минуты после звонка на перемену будет играть случайный трек.\n"
            "Можно исключить композиции из воспроизведения, сняв галочку."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Поле задержки музыки
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Задержка музыки после звонка:")
        delay_layout.addWidget(delay_label)
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setRange(0, 10)
        self.delay_spinbox.setSuffix(" мин")
        self.delay_spinbox.setValue(2)
        delay_layout.addWidget(self.delay_spinbox)
        delay_layout.addStretch()
        layout.addLayout(delay_layout)

        self.folder_label = QLabel("Папки: не выбраны")
        self.folder_label.setStyleSheet("font-weight: bold; padding: 6px;")
        layout.addWidget(self.folder_label)

        self.file_list = QTreeWidget()
        self.file_list.setHeaderHidden(True)
        self.file_list.itemChanged.connect(self.on_item_changed)
        layout.addWidget(self.file_list)

        controls = QHBoxLayout()
        self.select_btn = QPushButton("📁 Выбрать папки")
        self.select_btn.clicked.connect(self.select_folders)
        controls.addWidget(self.select_btn)

        self.select_all_btn = QPushButton("✅ Выбрать все")
        self.select_all_btn.clicked.connect(self.select_all_tracks)
        controls.addWidget(self.select_all_btn)

        self.unselect_all_btn = QPushButton("⬜ Снять все")
        self.unselect_all_btn.clicked.connect(self.unselect_all_tracks)
        controls.addWidget(self.unselect_all_btn)

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
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in extensions:
                    files.append(f)
        return sorted(files, key=lambda x: (str(x.parent), x.name.lower()))

    def load_current_settings(self):
        music = self.config.get_music_settings()
        self.music_folders = music.get("folders", [])
        if not self.music_folders and music.get("folder"):
            self.music_folders = [music.get("folder")]
        # Загружаем значение задержки
        delay = music.get("delay_minutes", 2)
        try:
            delay = int(delay)
        except (TypeError, ValueError):
            delay = 2
        self.delay_spinbox.setValue(delay)
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
        self.folder_items = []
        selected = set(selected_tracks or [])
        files = self._audio_files()

        if not files:
            item = QTreeWidgetItem(["📭 В выбранных папках нет аудиофайлов"])
            item.setForeground(0, Qt.gray)
            self.file_list.addTopLevelItem(item)
            return

        folders = {}
        for track in files:
            folder = str(track.parent)
            folders.setdefault(folder, []).append(track)

        for folder_path in sorted(folders.keys()):
            folder_name = Path(folder_path).name or folder_path
            folder_item = QTreeWidgetItem([f"📁 {folder_name}"])
            folder_item.setData(0, Qt.UserRole, folder_path)
            tristate_flag = getattr(Qt, "ItemIsAutoTristate", None)
            if tristate_flag is None and hasattr(Qt, "ItemFlag"):
                tristate_flag = getattr(Qt.ItemFlag, "ItemIsAutoTristate", None)
            if tristate_flag is None:
                tristate_flag = 0
            folder_item.setFlags(folder_item.flags() | Qt.ItemIsUserCheckable | tristate_flag)
            self.file_list.addTopLevelItem(folder_item)
            self.folder_items.append(folder_item)

            checked_count = 0
            tracks = sorted(folders[folder_path], key=lambda x: x.name.lower())
            for track in tracks:
                child = QTreeWidgetItem([f"   🎵 {track.name}"])
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                child.setData(0, Qt.UserRole, str(track))
                is_checked = (not selected) or (str(track) in selected)
                child.setCheckState(0, Qt.Checked if is_checked else Qt.Unchecked)
                if is_checked:
                    checked_count += 1
                folder_item.addChild(child)
                self.track_items.append(child)

            if checked_count == 0:
                folder_item.setCheckState(0, Qt.Unchecked)
            elif checked_count == len(tracks):
                folder_item.setCheckState(0, Qt.Checked)
            else:
                folder_item.setCheckState(0, Qt.PartiallyChecked)

        self.file_list.expandAll()

    def _save_music_state(self):
        selected_tracks = [
            item.data(0, Qt.UserRole)
            for item in self.track_items
            if item.checkState(0) == Qt.Checked
        ]
        self.config.set_music_folders(self.music_folders)
        music = self.config.get_music_settings()
        music["selected_tracks"] = selected_tracks
        # Сохраняем задержку музыки
        music["delay_minutes"] = self.delay_spinbox.value()
        self.config.preferences["music"] = music

    def select_folders(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой")
        while folder:
            if folder not in self.music_folders:
                self.music_folders.append(folder)
            folder = QFileDialog.getExistingDirectory(
                self,
                "Выберите следующую папку с музыкой (Отмена — завершить выбор)",
            )
        self._update_folder_label()
        self.update_file_list()
        self._save_music_state()

    def select_all_tracks(self):
        for item in self.track_items:
            item.setCheckState(0, Qt.Checked)
        for item in self.folder_items:
            item.setCheckState(0, Qt.Checked)
        self._save_music_state()

    def unselect_all_tracks(self):
        for item in self.track_items:
            item.setCheckState(0, Qt.Unchecked)
        for item in self.folder_items:
            item.setCheckState(0, Qt.Unchecked)
        self._save_music_state()

    def clear_folders(self):
        self.music_folders = []
        self.config.set_music_folders([])
        music = self.config.get_music_settings()
        music["selected_tracks"] = []
        self.config.preferences["music"] = music
        self._update_folder_label()
        self.file_list.clear()
        item = QTreeWidgetItem(["✅ Музыка отключена"])
        item.setForeground(0, Qt.green)
        self.file_list.addTopLevelItem(item)


    def on_item_changed(self, item, _column):
        if item.childCount() > 0:
            return
        self._save_music_state()

    def accept(self):
        self._save_music_state()
        super().accept()
