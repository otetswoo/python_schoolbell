#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QListWidget, QListWidgetItem, QCheckBox
)

from src.config_manager import ConfigManager


class MusicSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("🎵 Музыка на переменах")
        self.resize(560, 440)
        self.config = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Выберите папку с музыкой для воспроизведения на переменах.\n"
            "Через 2 минуты после звонка на перемену будет играть случайный трек.\n"
            "Отметьте галочками композиции, которые можно воспроизводить."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.folder_label = QLabel("Папка: не выбрана")
        self.folder_label.setStyleSheet("font-weight: bold; padding: 6px;")
        layout.addWidget(self.folder_label)

        list_toolbar = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("✅ Выбрать все")
        self.select_all_checkbox.stateChanged.connect(self.toggle_select_all)
        list_toolbar.addWidget(self.select_all_checkbox)
        list_toolbar.addStretch()
        layout.addLayout(list_toolbar)

        self.file_list = QListWidget()
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

    def _audio_files(self, folder):
        p = Path(folder)
        if not p.exists():
            return []
        extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".wma"}
        return sorted([f.name for f in p.iterdir() if f.is_file() and f.suffix.lower() in extensions])

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
        files = self._audio_files(folder)
        selected = set(self.config.get_music_settings().get("selected_tracks", []))

        if not files:
            item = QListWidgetItem("📭 В папке нет аудиофайлов")
            item.setForeground(Qt.gray)
            self.file_list.addItem(item)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.setEnabled(False)
            return

        self.select_all_checkbox.setEnabled(True)
        for filename in files:
            item = QListWidgetItem(f"🎵 {filename}")
            item.setData(Qt.UserRole, filename)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            checked = True if not selected else filename in selected
            item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
            self.file_list.addItem(item)
        self._update_select_all_state()

    def toggle_select_all(self, state):
        if self.file_list.count() == 0:
            return
        checked = state == Qt.Checked
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)

    def _update_select_all_state(self):
        checkable = []
        checked = 0
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable:
                checkable.append(item)
                if item.checkState() == Qt.Checked:
                    checked += 1
        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setChecked(bool(checkable) and checked == len(checkable))
        self.select_all_checkbox.blockSignals(False)

    def _collect_selected_tracks(self):
        selected = []
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            if item.flags() & Qt.ItemIsUserCheckable and item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку с музыкой")
        if folder:
            self.config.set_music_folder(folder)
            self.folder_label.setText(f"Папка: {folder}")
            self.update_file_list(folder)

    def clear_folder(self):
        self.config.set_music_folder("")
        self.config.preferences.setdefault("music", {})["selected_tracks"] = []
        self.folder_label.setText("Папка: не выбрана")
        self.file_list.clear()
        self.select_all_checkbox.setChecked(False)
        self.select_all_checkbox.setEnabled(False)
        item = QListWidgetItem("✅ Музыка отключена")
        item.setForeground(Qt.green)
        self.file_list.addItem(item)

    def accept(self):
        self.config.preferences.setdefault("music", {})["selected_tracks"] = self._collect_selected_tracks()
        super().accept()
