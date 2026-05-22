#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QDateEdit, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import QDate, Qt, QDateTime
from PySide6.QtGui import QColor

import datetime

from src.config_manager import ConfigManager
from src.volume_control import VolumeControl


class AnnouncementSelectDialog(QDialog):
    """Диалог выбора активного объявления для ручного воспроизведения."""
    
    def __init__(self, parent, active_announcements, config: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("📢 Выбор объявления")
        self.resize(500, 350)
        self.config = config
        self.active_announcements = active_announcements
        self.selected_index = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Выберите объявление для воспроизведения:")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Список объявлений
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setAlternatingRowColors(True)
        layout.addWidget(self.list_widget)
        
        # Заполняем список
        now = datetime.datetime.now()
        for idx, ann in active_announcements:
            file_name = ann.get("file", "").split("/")[-1] or "(не выбран)"
            date_str = ann.get("date", "")
            time_str = ann.get("time", "")
            repeat_days = ann.get("repeat_days", [])
            
            # Вычисляем время до события
            if date_str and time_str:
                try:
                    ann_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    delta = ann_datetime - now
                    if delta.total_seconds() > 0:
                        days = delta.days
                        hours, remainder = divmod(int(delta.seconds), 3600)
                        minutes, _ = divmod(remainder, 60)
                        if days > 0:
                            time_until = f"{days} дн. {hours} ч. {minutes} мин."
                        elif hours > 0:
                            time_until = f"{hours} ч. {minutes} мин."
                        else:
                            time_until = f"{minutes} мин."
                    else:
                        time_until = "Сейчас"
                except ValueError:
                    time_until = "?"
            else:
                time_until = "?"
            
            # Формируем описание повторения
            if repeat_days:
                repeat_text = f"Повтор: {', '.join(repeat_days)}"
            else:
                repeat_text = "Повтор: нет"
            
            item_text = f"{file_name}\n  Дата: {date_str or '—'}, Время: {time_str}, {repeat_text}\n  До события: {time_until}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, idx)
            self.list_widget.addItem(item)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        play_btn = QPushButton("▶️ Воспроизвести")
        play_btn.clicked.connect(self.accept)
        btn_layout.addWidget(play_btn)
        
        layout.addLayout(btn_layout)
    
    def get_selected_index(self):
        """Возвращает индекс выбранного объявления в общем списке announcements."""
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None


class AnnouncementSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.setWindowTitle("📢 Объявления")
        self.resize(620, 400)
        self.config = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(
            "Настройка разовых объявлений.\n"
            "Выберите аудиофайл, дату и время автоматического воспроизведения.\n"
            "После запуска объявление будет отмечено как воспроизведенное."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Таблица объявлений
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Файл", "Дата", "Время", "Повтор", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.on_edit_clicked)
        layout.addWidget(self.table)

        # Кнопки под таблицей
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.on_add_clicked)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("✏️ Изменить")
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

        self.load_announcements()

    def load_announcements(self):
        """Загружает список объявлений в таблицу."""
        announcements = self.config.get_announcements()
        
        # Сортируем объявления: сначала ближайшие по времени, затем более дальние
        def sort_key(ann):
            date_str = ann.get("date", "")
            time_str = ann.get("time", "")
            if date_str and time_str:
                try:
                    return datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                except ValueError:
                    pass
            return datetime.datetime.max
        
        sorted_announcements = sorted(enumerate(announcements), key=lambda x: sort_key(x[1]))
        
        self.table.setRowCount(len(sorted_announcements))
        
        today = datetime.date.today()
        now = datetime.datetime.now()
        
        for new_row, (orig_row, ann) in enumerate(sorted_announcements):
            # Сохраняем оригинальный индекс в данных строки
            self.table.setVerticalHeaderItem(new_row, QTableWidgetItem(str(orig_row)))
            
            # Файл
            file_path = ann.get("file", "")
            file_name = file_path.split("/")[-1] if file_path else "(не выбран)"
            item_file = QTableWidgetItem(file_name)
            item_file.setToolTip(file_path)
            self.table.setItem(new_row, 0, item_file)

            # Дата
            date_str = ann.get("date", "")
            item_date = QTableWidgetItem(date_str)
            self.table.setItem(new_row, 1, item_date)

            # Время
            time_str = ann.get("time", "")
            item_time = QTableWidgetItem(time_str)
            self.table.setItem(new_row, 2, item_time)
            
            # Повтор
            repeat_days = ann.get("repeat_days", [])
            if repeat_days:
                repeat_text = ", ".join(repeat_days)
            else:
                repeat_text = "нет"
            item_repeat = QTableWidgetItem(repeat_text)
            self.table.setItem(new_row, 3, item_repeat)

            # Статус и время до события
            played = ann.get("played", False)
            enabled = ann.get("enabled", True)
            
            # Вычисляем время до события
            time_until = ""
            if date_str and time_str:
                try:
                    ann_datetime = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
                    delta = ann_datetime - now
                    if delta.total_seconds() > 0:
                        days = delta.days
                        hours, remainder = divmod(int(delta.seconds), 3600)
                        minutes, _ = divmod(remainder, 60)
                        if days > 0:
                            time_until = f"{days} дн. {hours} ч."
                        elif hours > 0:
                            time_until = f"{hours} ч. {minutes} мин."
                        else:
                            time_until = f"{minutes} мин."
                    else:
                        time_until = "Сейчас"
                except ValueError:
                    time_until = "?"
            
            if not enabled:
                status_text = "⏸ Выкл"
                color = QColor("#888888")
            elif played:
                status_text = "✅ Сыграно"
                color = QColor("#888888")
            else:
                # Проверяем, не прошла ли дата
                try:
                    ann_date = datetime.date.fromisoformat(date_str) if date_str else None
                    if ann_date and ann_date < today:
                        status_text = f"⏳ Ожидает (дата прошла)\n{time_until}"
                        color = QColor("#888888")
                    else:
                        status_text = f"⏳ Ожидает\n{time_until}" if time_until else "⏳ Ожидает"
                        color = QColor("#000000")
                except ValueError:
                    status_text = "⏳ Ожидает"
                    color = QColor("#000000")
            
            item_status = QTableWidgetItem(status_text)
            item_status.setForeground(color)
            self.table.setItem(new_row, 4, item_status)

            # Если played=True или дата в прошлом — делаем строку серой
            if played or not enabled:
                self._set_row_gray(new_row)
            elif date_str:
                try:
                    ann_date = datetime.date.fromisoformat(date_str)
                    if ann_date < today:
                        self._set_row_gray(new_row)
                except ValueError:
                    pass

    def _set_row_gray(self, row):
        """Делает строку таблицы серой."""
        gray = QColor("#888888")
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setForeground(gray)

    def on_add_clicked(self):
        """Открывает диалог добавления нового объявления."""
        dialog = AnnouncementEditDialog(self, entry=None)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data.get("file"):
                index = self.config.add_announcement(
                    data["file"],
                    data["date"],
                    data["time"]
                )
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()
                self.table.selectRow(index)

    def on_edit_clicked(self):
        """Открывает диалог редактирования выбранного объявления."""
        row = self.table.currentRow()
        if row < 0:
            return
        
        # Получаем оригинальный индекс из вертикального заголовка
        header_item = self.table.verticalHeaderItem(row)
        if header_item:
            orig_row = int(header_item.text())
        else:
            orig_row = row
        
        announcements = self.config.get_announcements()
        if 0 <= orig_row < len(announcements):
            entry = announcements[orig_row].copy()
            dialog = AnnouncementEditDialog(self, entry=entry)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                self.config.update_announcement(orig_row, **data)
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()

    def on_delete_clicked(self):
        """Удаляет выбранное объявление."""
        row = self.table.currentRow()
        if row < 0:
            return
        
        # Получаем оригинальный индекс из вертикального заголовка
        header_item = self.table.verticalHeaderItem(row)
        if header_item:
            orig_row = int(header_item.text())
        else:
            orig_row = row
        
        announcements = self.config.get_announcements()
        if 0 <= orig_row < len(announcements):
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Удалить объявление '{announcements[orig_row].get('file', '').split('/')[-1]}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.config.delete_announcement(orig_row)
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()

    def accept(self):
        super().accept()


class AnnouncementEditDialog(QDialog):
    def __init__(self, parent, entry=None):
        super().__init__(parent)
        
        if entry is None:
            self.setWindowTitle("➕ Добавление объявления")
        else:
            self.setWindowTitle("✏️ Редактирование объявления")
        
        self.resize(450, 320)
        self.entry = entry or {}

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Выбор файла
        file_group = QGroupBox("Аудиофайл")
        file_layout = QHBoxLayout()
        file_group.setLayout(file_layout)
        
        self.file_label = QLabel("Файл: не выбран")
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label, 1)
        
        self.select_file_btn = QPushButton("📁 Выбрать файл")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        layout.addWidget(file_group)

        # Дата
        date_group = QGroupBox("Дата")
        date_layout = QHBoxLayout()
        date_group.setLayout(date_layout)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        layout.addWidget(date_group)

        # Время
        time_group = QGroupBox("Время")
        time_layout = QHBoxLayout()
        time_group.setLayout(time_layout)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(8)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(30)
        
        time_layout.addWidget(QLabel("Часы:"))
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minute_spin)
        time_layout.addStretch()
        
        layout.addWidget(time_group)

        # Громкость
        self.volume_control = VolumeControl(
            "Громкость объявления:",
            self.config.get_volume("announcement"),
            self,
        )
        layout.addWidget(self.volume_control)

        # Активно
        self.active_checkbox = QCheckBox("Активно")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)

        layout.addStretch()

        # Кнопки OK / Отмена
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)

        self.load_entry()

    @property
    def config(self):
        return self.parent().config

    def load_entry(self):
        """Загружает данные из entry в элементы управления."""
        if not self.entry:
            return
        
        file_path = self.entry.get("file", "")
        if file_path:
            self.file_label.setText(f"Файл: {file_path}")
        
        date_str = self.entry.get("date", "")
        if date_str:
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if date.isValid():
                self.date_edit.setDate(date)
        
        time_str = self.entry.get("time", "08:30")
        try:
            h, m = map(int, time_str.split(":")[:2])
            self.hour_spin.setValue(h)
            self.minute_spin.setValue(m)
        except ValueError:
            pass
        
        enabled = self.entry.get("enabled", True)
        self.active_checkbox.setChecked(enabled)

    def select_file(self):
        """Открывает диалог выбора файла."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл объявления",
            "",
            "Audio (*.wav *.mp3 *.ogg *.flac *.m4a *.wma)"
        )
        if path:
            self.file_label.setText(f"Файл: {path}")

    def get_data(self) -> dict:
        """Возвращает данные из диалога."""
        file_path = self.file_label.text().replace("Файл: ", "")
        if file_path == "не выбран":
            file_path = ""
        
        return {
            "file": file_path,
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "time": f"{self.hour_spin.value():02d}:{self.minute_spin.value():02d}",
            "enabled": self.active_checkbox.isChecked(),
            "volume": self.volume_control.value(),
        }

