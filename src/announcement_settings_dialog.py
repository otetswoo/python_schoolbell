#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QDateEdit, QTimeEdit, QCheckBox
)
from PySide6.QtCore import QDate, QTime

from src.config_manager import ConfigManager


class AnnouncementSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("📢 Объявления")
        self.resize(520, 360)
        self.config = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Настройка разового объявления.\n"
            "Выберите аудиофайл, дату и время автоматического воспроизведения.\n"
            "После запуска объявление будет отмечено как воспроизведенное."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.enabled_checkbox = QCheckBox("Включить разовый запуск объявления")
        layout.addWidget(self.enabled_checkbox)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setStyleSheet("font-weight: bold; padding: 10px;")
        file_layout.addWidget(self.file_label)

        self.select_file_btn = QPushButton("📁 Выбрать файл")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        layout.addLayout(file_layout)

        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Дата:"))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        layout.addLayout(date_layout)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Время:"))
        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime(8, 30))
        time_layout.addWidget(self.time_edit)
        time_layout.addStretch()
        layout.addLayout(time_layout)

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
        announcement = self.config.get_announcement_settings()
        self.enabled_checkbox.setChecked(announcement.get("enabled", False))

        file_path = announcement.get("file", "")
        if file_path:
            self.file_label.setText(f"Файл: {file_path}")

        date_str = announcement.get("date", "")
        if date_str:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_edit.setDate(date)

        time_str = announcement.get("time", "08:30")
        try:
            h, m = map(int, time_str.split(":")[:2])
            self.time_edit.setTime(QTime(h, m))
        except ValueError:
            pass

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл объявления",
            "",
            "Audio (*.wav *.mp3 *.ogg *.flac *.m4a *.wma)"
        )
        if path:
            self.config.set_announcement_file(path)
            self.file_label.setText(f"Файл: {path}")
            self.enabled_checkbox.setChecked(True)

    def clear_settings(self):
        if "announcement" not in self.config.preferences:
            self.config.preferences["announcement"] = {}
        self.config.preferences["announcement"].update({
            "enabled": False,
            "file": "",
            "played": False,
        })
        self.enabled_checkbox.setChecked(False)
        self.file_label.setText("Файл: не выбран")

    def accept(self):
        if "announcement" not in self.config.preferences:
            self.config.preferences["announcement"] = {}
        self.config.preferences["announcement"]["enabled"] = self.enabled_checkbox.isChecked()
        self.config.set_announcement_date(self.date_edit.date().toString("yyyy-MM-dd"))
        self.config.set_announcement_time(self.time_edit.time().toString("HH:mm"))
        super().accept()
