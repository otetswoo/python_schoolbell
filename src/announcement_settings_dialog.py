#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QDateEdit, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QWidget, QRadioButton, QButtonGroup
)
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QColor

import datetime

from src.config_manager import ConfigManager
from src.volume_control import VolumeControl
from src.config import WEEK_DAYS, WEEK_DAYS_RU
from src.gui.localization import LOCALIZATION


class AnnouncementSettingsDialog(QDialog):
    def __init__(self, parent, config_manager: ConfigManager):
        super().__init__(parent)
        self.current_locale = config_manager.get_locale() if hasattr(config_manager, 'get_locale') else 'ru'
        self.setWindowTitle(self.l10n("announcements_dialog_title", "📢 Announcements"))
        self.resize(750, 450)
        self.config = config_manager

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(self.l10n("announcements_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        # Таблица объявлений
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "✓",
            self.l10n("ann_col_days", "Days"),
            self.l10n("ann_col_file", "File"),
            self.l10n("ann_col_date", "Date"),
            self.l10n("ann_col_time", "Time"),
            self.l10n("ann_col_status", "Status")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self.on_edit_clicked)
        layout.addWidget(self.table)

        # Кнопки под таблицей
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton(self.l10n("btn_add_announcement", "➕ Add"))
        self.add_btn.clicked.connect(self.on_add_clicked)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(self.l10n("btn_edit_announcement", "✏️ Edit"))
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(self.l10n("btn_delete_announcement", "🗑️ Delete"))
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

        self.load_announcements()

    def l10n(self, key, default=None):
        return LOCALIZATION.get(self.current_locale, {}).get(key, default if default is not None else key)

    def load_announcements(self):
        """Загружает список объявлений в таблицу."""
        announcements = self.config.get_announcements()
        self.table.setRowCount(len(announcements))
        
        today = datetime.date.today()
        today_weekday = WEEK_DAYS[datetime.date.today().weekday()]
        
        for row, ann in enumerate(announcements):
            # Чекбокс включения
            enabled = ann.get("enabled", True)
            checkbox = QCheckBox()
            checkbox.setChecked(enabled)
            checkbox.stateChanged.connect(lambda state, r=row: self.on_enabled_changed(r, state))
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.addWidget(checkbox)
            container_layout.setAlignment(Qt.AlignCenter)
            container_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, container)

            # Повторяющееся
            repeat_days = ann.get("repeat_days", [])
            if repeat_days:
                # Преобразуем дни недели в русские названия
                day_names = []
                for day in repeat_days:
                    if day in WEEK_DAYS:
                        idx = WEEK_DAYS.index(day)
                        day_names.append(WEEK_DAYS_RU[idx][:2])  # Первые две буквы
                repeat_text = ", ".join(day_names)
                repeat_item = QTableWidgetItem(repeat_text)
                tooltip_prefix = "Повторяется" if self.current_locale == "ru" else "Recurring"
                repeat_item.setToolTip(f"{tooltip_prefix}: {', '.join(day_names)}")
            else:
                repeat_item = QTableWidgetItem("")
                repeat_item.setToolTip("Одноразовое" if self.current_locale == "ru" else "One-time")
            self.table.setItem(row, 1, repeat_item)

            # Файл
            file_path = ann.get("file", "")
            file_name = file_path.split("/")[-1] if file_path else ("(не выбран)" if self.current_locale == "ru" else "(not selected)")
            item_file = QTableWidgetItem(file_name)
            item_file.setToolTip(file_path)
            self.table.setItem(row, 2, item_file)

            # Дата с форматом "22 мая 2026"
            date_str = ann.get("date", "")
            display_date = date_str
            if date_str:
                try:
                    # Пробуем распарсить дату в формате yyyy-MM-dd и отобразить в формате "22 мая 2026"
                    parsed_date = datetime.date.fromisoformat(date_str)
                    if self.current_locale == "ru":
                        month_names = {
                            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
                            5: "мая", 6: "июня", 7: "июля", 8: "августа",
                            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
                        }
                        display_date = f"{parsed_date.day} {month_names[parsed_date.month]} {parsed_date.year}"
                    else:
                        display_date = parsed_date.strftime("%d %B %Y")
                except (ValueError, KeyError):
                    pass  # Оставляем как есть если не удалось распарсить
            item_date = QTableWidgetItem(display_date)
            item_date.setToolTip(date_str)  # В подсказке показываем оригинальный формат
            self.table.setItem(row, 3, item_date)

            # Время
            time_str = ann.get("time", "")
            item_time = QTableWidgetItem(time_str)
            self.table.setItem(row, 4, item_time)

            # Статус
            played = ann.get("played", False)
            
            if not enabled:
                status_text = self.l10n("ann_status_disabled", "⏸ Disabled")
                color = QColor("#888888")
            elif played:
                status_text = self.l10n("ann_status_played", "✅ Played")
                color = QColor("#888888")
            else:
                # Проверяем, не прошла ли дата
                try:
                    ann_date = datetime.date.fromisoformat(date_str) if date_str else None
                    if repeat_days:
                        # Для повторяющихся объявлений проверяем день недели
                        if today_weekday not in repeat_days:
                            status_text = "⏳ Ожидает (не сегодня)" if self.current_locale == "ru" else "⏳ Pending (not today)"
                            color = QColor("#888888")
                        else:
                            status_text = "🔄 Повтор" if self.current_locale == "ru" else "🔄 Recurring"
                            color = QColor("#0066cc")
                    elif ann_date and ann_date < today:
                        status_text = "⏳ Ожидает (дата прошла)" if self.current_locale == "ru" else "⏳ Pending (date passed)"
                        color = QColor("#888888")
                    else:
                        status_text = self.l10n("ann_status_pending", "⏳ Pending")
                        color = QColor("#000000")
                except ValueError:
                    status_text = self.l10n("ann_status_pending", "⏳ Pending")
                    color = QColor("#000000")
            
            item_status = QTableWidgetItem(status_text)
            item_status.setForeground(color)
            self.table.setItem(row, 5, item_status)

            # Если played=True или дата в прошлом — делаем строку серой
            if played or not enabled:
                self._set_row_gray(row)
            elif date_str and not repeat_days:
                try:
                    ann_date = datetime.date.fromisoformat(date_str)
                    if ann_date < today:
                        self._set_row_gray(row)
                except ValueError:
                    pass

    def _set_row_gray(self, row):
        """Делает строку таблицы серой."""
        gray = QColor("#888888")
        for col in range(self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setForeground(gray)

    def on_enabled_changed(self, row, state):
        """Обработчик изменения состояния чекбокса включения."""
        announcements = self.config.get_announcements()
        if 0 <= row < len(announcements):
            enabled = (state != 0)
            self.config.update_announcement(row, enabled=enabled)
            self.config.save_preferences(self.config.preferences)
            # Перезагружаем таблицу для обновления статуса
            self.load_announcements()

    def on_add_clicked(self):
        """Открывает диалог добавления нового объявления."""
        dialog = AnnouncementEditDialog(self, entry=None,
                                        config_manager=self.config)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if not data:
                return  # Пользователь отменил или нет файла
            if data.get("file"):
                index = self.config.add_announcement(
                    data["file"],
                    data["date"],
                    data["time"],
                    repeat_days=data.get("repeat_days", []),
                )
                self.config.set_volume("announcement", data["volume"])
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()
                self.table.selectRow(index)

    def on_edit_clicked(self):
        """Открывает диалог редактирования выбранного объявления."""
        row = self.table.currentRow()
        if row < 0:
            return
        
        announcements = self.config.get_announcements()
        if 0 <= row < len(announcements):
            entry = announcements[row].copy()
            dialog = AnnouncementEditDialog(self, entry=entry,
                                            config_manager=self.config)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_data()
                if not data:
                    return  # Пользователь отменил или нет файла
                announcement_volume = data.pop("volume")
                self.config.update_announcement(row, **data)
                self.config.set_volume("announcement", announcement_volume)
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()

    def on_delete_clicked(self):
        """Удаляет выбранное объявление."""
        row = self.table.currentRow()
        if row < 0:
            return
        
        announcements = self.config.get_announcements()
        if 0 <= row < len(announcements):
            reply = QMessageBox.question(
                self,
                self.l10n("confirm_delete_title", "Confirm delete"),
                self.l10n("confirm_delete_text").format(announcements[row].get('file', '').split('/')[-1]),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.config.delete_announcement(row)
                self.config.save_preferences(self.config.preferences)
                self.load_announcements()

    def accept(self):
        """Валидация данных перед сохранением объявления."""
        super().accept()


class AnnouncementEditDialog(QDialog):
    def __init__(self, parent, entry=None, config_manager=None):
        super().__init__(parent)
        
        self._config = config_manager
        self.current_locale = config_manager.get_locale() if hasattr(config_manager, 'get_locale') else 'ru'
        
        if entry is None:
            self.setWindowTitle(self.l10n("ann_add_title", "➕ Add Announcement"))
        else:
            self.setWindowTitle(self.l10n("ann_edit_title", "✏️ Edit Announcement"))
        
        self.resize(500, 420)
        self.entry = entry or {}
        self._file_path = ""

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Выбор файла
        file_group = QGroupBox(self.l10n("ann_file_group", "Audio File"))
        file_layout = QHBoxLayout()
        file_group.setLayout(file_layout)
        
        self.file_label = QLabel(self.l10n("ann_file_not_selected", "File: not selected"))
        self.file_label.setWordWrap(True)
        file_layout.addWidget(self.file_label, 1)
        
        self.select_file_btn = QPushButton(self.l10n("btn_select_file", "📁 Select File"))
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.select_file_btn)
        
        layout.addWidget(file_group)
        self.file_group = file_group  # Сохраняем ссылку для стилизации

        # Тип объявления (одноразовое/повторяющееся) - взаимоисключающие радиокнопки
        type_group = QGroupBox(self.l10n("ann_mode_group", "Repeat Mode"))
        type_layout = QVBoxLayout()
        type_group.setLayout(type_layout)
        
        self.type_button_group = QButtonGroup(self)
        self.one_time_radio = QRadioButton(self.l10n("ann_one_time", "One-time (by date)"))
        self.repeat_radio = QRadioButton(self.l10n("ann_repeat", "Recurring (by weekdays)"))
        
        self.type_button_group.addButton(self.one_time_radio)
        self.type_button_group.addButton(self.repeat_radio)
        
        self.one_time_radio.setChecked(True)
        self.one_time_radio.toggled.connect(self.on_type_changed)
        self.repeat_radio.toggled.connect(self.on_type_changed)
        
        type_layout.addWidget(self.one_time_radio)
        type_layout.addWidget(self.repeat_radio)
        layout.addWidget(type_group)

        # Дни недели для повторения
        self.days_group = QGroupBox(self.l10n("ann_days_label", "Days:"))
        days_layout = QVBoxLayout()
        self.days_group.setLayout(days_layout)
        self.days_group.setEnabled(False)
        
        self.day_checkboxes = {}
        for i, day_ru in enumerate(WEEK_DAYS_RU):
            day_key = WEEK_DAYS[i]
            cb = QCheckBox(day_ru)
            cb.setProperty("day_key", day_key)
            days_layout.addWidget(cb)
            self.day_checkboxes[day_key] = cb
        
        layout.addWidget(self.days_group)

        # Дата с форматом "22 мая 2026"
        self.date_group = QGroupBox(self.l10n("ann_date_label", "Date:"))
        date_layout = QHBoxLayout()
        self.date_group.setLayout(date_layout)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("d MMMM yyyy")  # Формат: "22 мая 2026"
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumDate(QDate.currentDate())
        date_layout.addWidget(self.date_edit)
        date_layout.addStretch()
        
        layout.addWidget(self.date_group)

        # Время - подставляем текущее + 5 минут
        time_group = QGroupBox(self.l10n("ann_time_group", "Time"))
        time_layout = QHBoxLayout()
        time_group.setLayout(time_layout)
        
        now = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(now.hour)
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(now.minute)
        
        time_layout.addWidget(QLabel("Часы:"))
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(QLabel(":"))
        time_layout.addWidget(self.minute_spin)
        time_layout.addStretch()
        
        layout.addWidget(time_group)
        
        # Лейбл предупреждения о прошедшем времени
        self._time_warning_label = QLabel("⚠️ Это время уже прошло")
        self._time_warning_label.setStyleSheet("color: #e53935; font-size: 11px;")
        self._time_warning_label.setVisible(False)
        layout.addWidget(self._time_warning_label)

        # Громкость
        self.volume_control = VolumeControl(
            self.l10n("ann_volume", "Announcement volume:"),
            self.config.get_volume("announcement"),
            self,
        )
        layout.addWidget(self.volume_control)

        # Активно
        self.active_checkbox = QCheckBox(self.l10n("ann_active", "Active"))
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)

        layout.addStretch()

        # Кнопки OK / Отмена
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton(self.l10n("btn_cancel", "Cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)
        
        layout.addLayout(btn_layout)

        self.load_entry()
        
        # Подключаем сигналы для живой валидации времени
        self.date_edit.dateChanged.connect(self._validate_datetime_live)
        self.hour_spin.valueChanged.connect(self._validate_datetime_live)
        self.minute_spin.valueChanged.connect(self._validate_datetime_live)
        self.one_time_radio.toggled.connect(self._validate_datetime_live)
        
        # Первичная валидация
        self._validate_datetime_live()

    def l10n(self, key, default=None):
        return LOCALIZATION.get(self.current_locale, {}).get(key, default if default is not None else key)

    @property
    def config(self):
        if self._config:
            return self._config
        return self.parent().config
    
    def _validate_datetime_live(self):
        """Живая подсветка прошедшего времени."""
        RED = "QSpinBox { border: 2px solid #e53935; background: #fff3f3; }"
        OK = ""
        if self.one_time_radio.isChecked():
            selected = datetime.datetime(
                self.date_edit.date().year(), self.date_edit.date().month(),
                self.date_edit.date().day(), self.hour_spin.value(), self.minute_spin.value()
            )
            is_past = selected < datetime.datetime.now()
        else:
            # Для повторяющихся — только время
            is_past = datetime.time(self.hour_spin.value(), self.minute_spin.value()) \
                      < datetime.datetime.now().time()

        style = RED if is_past else OK
        self.hour_spin.setStyleSheet(style)
        self.minute_spin.setStyleSheet(style)
        self._time_warning_label.setVisible(is_past)

    def on_type_changed(self):
        """Обработчик изменения типа объявления."""
        is_repeat = self.repeat_radio.isChecked()
        self.days_group.setEnabled(is_repeat)
        self.date_group.setEnabled(not is_repeat)
    
    def load_entry(self):
        """Загружает данные из entry в элементы управления."""
        if not self.entry:
            return
        
        file_path = self.entry.get("file", "")
        self._file_path = file_path
        if file_path:
            self.file_label.setText(f"Файл: {file_path}")
        
        # Тип объявления
        repeat_days = self.entry.get("repeat_days", [])
        if repeat_days:
            self.repeat_radio.setChecked(True)
            self.one_time_radio.setChecked(False)
            self.on_type_changed()
            # Отмечаем дни недели
            for day_key, cb in self.day_checkboxes.items():
                cb.setChecked(day_key in repeat_days)
        else:
            self.one_time_radio.setChecked(True)
            self.repeat_radio.setChecked(False)
            self.on_type_changed()
        
        date_str = self.entry.get("date", "")
        if date_str:
            # Пробуем разные форматы даты для совместимости
            date = QDate.fromString(date_str, "yyyy-MM-dd")
            if not date.isValid():
                date = QDate.fromString(date_str, "d MMMM yyyy")
            if date.isValid():
                self.date_edit.setDate(date)
        
        time_str = self.entry.get("time", "08:30")
        try:
            h, m = map(int, time_str.split(":")[:2])
            self.hour_spin.setValue(h)
            self.minute_spin.setValue(m)
        except ValueError:
            pass
        
        self.volume_control.set_value(self.config.get_volume("announcement"))

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
            self._file_path = path
            self.file_label.setText(f"Файл: {path}")

    def get_data(self) -> dict:
        """Возвращает данные из диалога. Возвращает None если файл не выбран."""
        if not self._file_path:
            QMessageBox.warning(
                self,
                self.l10n("warning_title", "Предупреждение"),
                self.l10n("ann_file_required",
                          "Необходимо выбрать аудиофайл для объявления.")
            )
            return None

        repeat_days = []
        if self.repeat_radio.isChecked():
            for day_key, cb in self.day_checkboxes.items():
                if cb.isChecked():
                    repeat_days.append(day_key)

        date_str = ""
        if self.one_time_radio.isChecked():
            date_str = self.date_edit.date().toString("yyyy-MM-dd")

        return {
            "file": self._file_path,
            "date": date_str,
            "time": f"{self.hour_spin.value():02d}:{self.minute_spin.value():02d}",
            "enabled": self.active_checkbox.isChecked(),
            "volume": self.volume_control.value(),
            "repeat_days": repeat_days,
        }
