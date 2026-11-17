#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateEdit, QDialog, QGroupBox,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout,
)

from src.config_manager import ConfigManager


class HolidaySettingsDialog(QDialog):
    """Настройка графика каникул и ручного режима."""

    def __init__(self, parent, config_manager: ConfigManager, tr=None):
        super().__init__(parent)
        self.config = config_manager
        self.tr = tr or (lambda key, fallback=None: fallback or key)
        self.periods = list(config_manager.get_holidays()["periods"])

        self.setWindowTitle(self.tr("holidays_dialog_title", "🏖 График каникул"))
        self.resize(520, 460)

        layout = QVBoxLayout(self)

        info = QLabel(self.tr(
            "holidays_info",
            "Периоды каникул включают обе граничные даты. "
            "В автоматическом режиме состояние определяется текущей датой.",
        ))
        info.setWordWrap(True)
        layout.addWidget(info)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(self.tr("holidays_mode_label", "Режим:")))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(self.tr("holidays_mode_auto", "Автоматически"), "auto")
        self.mode_combo.addItem(self.tr("holidays_mode_on", "Включить принудительно"), "on")
        self.mode_combo.addItem(self.tr("holidays_mode_off", "Выключить принудительно"), "off")
        current_mode = config_manager.get_holiday_mode()
        index = self.mode_combo.findData(current_mode)
        self.mode_combo.setCurrentIndex(index if index >= 0 else 0)
        mode_layout.addWidget(self.mode_combo, stretch=1)
        layout.addLayout(mode_layout)

        periods_group = QGroupBox(self.tr("holidays_periods_group", "Периоды каникул"))
        periods_layout = QVBoxLayout(periods_group)
        self.periods_list = QListWidget()
        self.periods_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.periods_list.itemSelectionChanged.connect(self.on_selection_changed)
        periods_layout.addWidget(self.periods_list)

        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel(self.tr("holidays_start", "Начало:")))
        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_edit.setDateRange(QDate(2000, 1, 1), QDate(2100, 12, 31))
        self.start_edit.setDate(QDate.currentDate())
        dates_layout.addWidget(self.start_edit)

        dates_layout.addWidget(QLabel(self.tr("holidays_end", "Окончание:")))
        self.end_edit = QDateEdit()
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_edit.setDateRange(QDate(2000, 1, 1), QDate(2100, 12, 31))
        self.end_edit.setDate(QDate.currentDate())
        dates_layout.addWidget(self.end_edit)
        dates_layout.addStretch()
        periods_layout.addLayout(dates_layout)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton(self.tr("btn_add_holiday", "➕ Добавить"))
        self.add_btn.clicked.connect(self.add_period)
        buttons_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton(self.tr("btn_edit_holiday", "✏️ Изменить"))
        self.edit_btn.clicked.connect(self.update_period)
        buttons_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton(self.tr("btn_delete_holiday", "🗑️ Удалить"))
        self.delete_btn.clicked.connect(self.delete_period)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        periods_layout.addLayout(buttons_layout)

        layout.addWidget(periods_group, stretch=1)

        dialog_buttons = QHBoxLayout()
        dialog_buttons.addStretch()
        cancel_btn = QPushButton(self.tr("btn_cancel", "Отмена"))
        cancel_btn.clicked.connect(self.reject)
        dialog_buttons.addWidget(cancel_btn)
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        dialog_buttons.addWidget(ok_btn)
        layout.addLayout(dialog_buttons)

        self.reload_list()

    def _period_text(self, period):
        return f"{period['start']} — {period['end']}"

    def reload_list(self, select_index=None):
        self.periods_list.blockSignals(True)
        self.periods_list.clear()
        for period in self.periods:
            item = QListWidgetItem(self._period_text(period))
            item.setData(Qt.UserRole, period)
            self.periods_list.addItem(item)
        self.periods_list.blockSignals(False)

        if select_index is not None and 0 <= select_index < self.periods_list.count():
            self.periods_list.setCurrentRow(select_index)

    def on_selection_changed(self):
        item = self.periods_list.currentItem()
        if not item:
            return
        period = item.data(Qt.UserRole)
        start = QDate.fromString(period.get("start", ""), "yyyy-MM-dd")
        end = QDate.fromString(period.get("end", ""), "yyyy-MM-dd")
        if start.isValid():
            self.start_edit.setDate(start)
        if end.isValid():
            self.end_edit.setDate(end)

    def _read_dates(self):
        start = self.start_edit.date().toString("yyyy-MM-dd")
        end = self.end_edit.date().toString("yyyy-MM-dd")
        if start > end:
            QMessageBox.warning(
                self,
                self.tr("error_title", "Ошибка"),
                self.tr(
                    "holidays_error_order",
                    "Дата начала не может быть позже даты окончания.",
                ),
            )
            return None
        return {"start": start, "end": end}

    def add_period(self):
        period = self._read_dates()
        if period is None:
            return
        self.periods.append(period)
        self.periods.sort(key=lambda item: item["start"])
        self.reload_list(select_index=self.periods.index(period))

    def update_period(self):
        row = self.periods_list.currentRow()
        if row < 0:
            return
        period = self._read_dates()
        if period is None:
            return
        self.periods[row] = period
        self.periods.sort(key=lambda item: item["start"])
        self.reload_list(select_index=self.periods.index(period))

    def delete_period(self):
        row = self.periods_list.currentRow()
        if row < 0:
            return
        self.periods.pop(row)
        self.reload_list(select_index=max(0, min(row, len(self.periods) - 1)))

    def accept(self):
        self.config.set_holiday_mode(self.mode_combo.currentData())
        self.config.set_holiday_periods(self.periods)
        self.config.save_preferences(self.config.preferences)
        super().accept()
