#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog


class BellSettingsDialog(QDialog):
    def __init__(self, parent, sounds: dict, locale: str = "ru"):
        super().__init__(parent)
        self.sounds = sounds
        self.locale = locale

        self.setWindowTitle("🔔 Настройки звонков" if locale == "ru" else "🔔 Bell settings")
        self.resize(620, 220)

        layout = QVBoxLayout(self)
        info = QLabel(
            "Выберите файлы для звонка на урок и звонка с урока."
            if locale == "ru"
            else "Choose files for start-lesson and end-lesson bells."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.start_label = QLabel()
        self.end_label = QLabel()

        self._build_row(layout, "start")
        self._build_row(layout, "end")

        btns = QHBoxLayout()
        btns.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btns.addWidget(ok_btn)
        layout.addLayout(btns)

        self._refresh_labels()

    def _build_row(self, layout, bell_type: str):
        row = QHBoxLayout()
        label = self.start_label if bell_type == "start" else self.end_label
        row.addWidget(label, 1)

        choose_text = "📁 Выбрать" if self.locale == "ru" else "📁 Choose"
        clear_text = "❌ Очистить" if self.locale == "ru" else "❌ Clear"

        choose_btn = QPushButton(choose_text)
        choose_btn.clicked.connect(lambda: self.select_sound(bell_type))
        row.addWidget(choose_btn)

        clear_btn = QPushButton(clear_text)
        clear_btn.clicked.connect(lambda: self.clear_sound(bell_type))
        row.addWidget(clear_btn)

        layout.addLayout(row)

    def _refresh_labels(self):
        start = self.sounds.get("start", "")
        end = self.sounds.get("end", "")
        if self.locale == "ru":
            self.start_label.setText(f"На урок: {start or 'не выбрано'}")
            self.end_label.setText(f"С урока: {end or 'не выбрано'}")
        else:
            self.start_label.setText(f"Start lesson: {start or 'not selected'}")
            self.end_label.setText(f"End lesson: {end or 'not selected'}")

    def select_sound(self, bell_type):
        title = "Звонок на урок" if bell_type == "start" else "Звонок с урока"
        if self.locale == "en":
            title = "Start lesson bell" if bell_type == "start" else "End lesson bell"

        path, _ = QFileDialog.getOpenFileName(self, title, "", "Audio (*.wav *.mp3 *.ogg *.flac *.m4a)")
        if path:
            self.sounds[bell_type] = path
            self._refresh_labels()

    def clear_sound(self, bell_type):
        self.sounds[bell_type] = ""
        self._refresh_labels()
