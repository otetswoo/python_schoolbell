#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QPlainTextEdit, QDialogButtonBox
)
from PySide6.QtGui import QFont

from src.event_logger import EventLogger


class LogViewerDialog(QDialog):
    """Диалог просмотра журнала событий"""

    def __init__(self, parent, logger: EventLogger):
        super().__init__(parent)
        self.setWindowTitle(parent.tr("log_dialog_title", "Журнал событий"))
        self.resize(700, 500)
        self.logger = logger

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Текстовое поле для отображения логов
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        # Моноширинный шрифт
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.log_text.setFont(font)
        layout.addWidget(self.log_text)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.today_btn = QPushButton(parent.tr("btn_today_log", "Сегодня"))
        self.today_btn.clicked.connect(self.load_today_events)
        btn_layout.addWidget(self.today_btn)

        self.errors_btn = QPushButton(parent.tr("btn_errors_log", "Ошибки"))
        self.errors_btn.clicked.connect(self.load_error_events)
        btn_layout.addWidget(self.errors_btn)

        btn_layout.addStretch()

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText(parent.tr("btn_close", "Закрыть"))
        bb.rejected.connect(self.reject)
        btn_layout.addWidget(bb)

        layout.addLayout(btn_layout)

        # По умолчанию загружаем события сегодня
        self.load_today_events()

    def load_today_events(self):
        """Загружает события за сегодня"""
        events = self.logger.get_today_events()
        self._display_events(events)

    def load_error_events(self):
        """Загружает только ошибки"""
        events = self.logger.get_recent_errors()
        self._display_events(events)

    def _display_events(self, events):
        """Отображает события в текстовом поле"""
        self.log_text.clear()
        if not events:
            self.log_text.appendPlainText(
                self.tr("no_events", "Нет событий для отображения")
            )
            return

        for event in events:
            if isinstance(event, str):
                self.log_text.appendPlainText(event)  # строка из файла — выводим как есть
            elif isinstance(event, dict):
                timestamp = event.get("timestamp", "")
                level = event.get("level", "info")
                message = event.get("message", "")
                line = f"[{timestamp}] [{level.upper()}] {message}"
                self.log_text.appendPlainText(line)
