#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QDialogButtonBox
)
from PySide6.QtCore import Qt

from src.config_manager import ConfigManager


class ProfilesDialog(QDialog):
    """Диалог управления профилями расписания"""

    def __init__(self, parent, config: ConfigManager, main_window_ref):
        super().__init__(parent)
        self.setWindowTitle(parent.tr("profiles_dialog_title", "Профили расписания"))
        self.resize(400, 300)
        self.config = config
        self.main_window_ref = main_window_ref

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel(parent.tr(
            "profiles_info",
            "Управляйте профилями расписания. Активируйте нужный профиль для применения его настроек."
        ))
        info.setWordWrap(True)
        layout.addWidget(info)

        # Список профилей
        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        self.add_btn = QPushButton(parent.tr("btn_add", "Добавить"))
        self.add_btn.clicked.connect(self.add_profile)
        btn_layout.addWidget(self.add_btn)

        self.rename_btn = QPushButton(parent.tr("btn_rename", "Переименовать"))
        self.rename_btn.clicked.connect(self.rename_profile)
        btn_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton(parent.tr("btn_delete", "Удалить"))
        self.delete_btn.clicked.connect(self.delete_profile)
        btn_layout.addWidget(self.delete_btn)

        self.activate_btn = QPushButton(parent.tr("btn_activate", "Активировать"))
        self.activate_btn.clicked.connect(self.activate_profile)
        btn_layout.addWidget(self.activate_btn)

        btn_layout.addStretch()

        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.button(QDialogButtonBox.Close).setText(parent.tr("btn_close", "Закрыть"))
        bb.rejected.connect(self.reject)
        btn_layout.addWidget(bb)

        layout.addLayout(btn_layout)

        self.refresh_list()

    def refresh_list(self):
        """Обновляет список профилей в QListWidget"""
        self.profile_list.clear()
        profiles = self.config.get_profiles()
        current_profile = self.config.get_current_profile()

        for profile_name, profile_data in profiles.items():
            display_name = profile_data.get("name", profile_name)
            item = QListWidgetItem(f"{display_name} ({profile_name})")
            if profile_name == current_profile:
                item.setForeground(Qt.blue)
                item.setText(item.text() + " *")
            self.profile_list.addItem(item)

    def add_profile(self):
        """Добавление нового профиля"""
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            self.tr("add_profile_title", "Добавить профиль"),
            self.tr("add_profile_label", "Введите имя профиля:")
        )
        if ok and name.strip():
            profile_key = name.strip().lower().replace(" ", "_")
            if profile_key in self.config.get_profiles():
                QMessageBox.warning(
                    self,
                    self.tr("error_title", "Ошибка"),
                    self.tr("profile_exists", "Профиль с таким именем уже существует")
                )
                return
            self.config.add_profile(profile_key, name.strip(), {})
            self.refresh_list()

    def rename_profile(self):
        """Переименование профиля"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            return

        profile_name = current_item.text()
        # Извлекаем ключ профиля (до скобки)
        if "(" in profile_name:
            profile_key = profile_name.split("(")[1].split(")")[0].strip()
        else:
            profile_key = profile_name.strip()

        if profile_key == "default":
            QMessageBox.warning(
                self,
                self.tr("error_title", "Ошибка"),
                self.tr("cannot_rename_default", "Нельзя переименовать профиль 'default'")
            )
            return

        from PySide6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self,
            self.tr("rename_profile_title", "Переименовать профиль"),
            self.tr("rename_profile_label", "Введите новое имя:"),
            text=profile_name.split("(")[0].strip() if "(" in profile_name else profile_name
        )
        if ok and new_name.strip():
            profiles = self.config.get_profiles()
            if profile_key in profiles:
                profiles[profile_key]["name"] = new_name.strip()
                # Пересохраняем профиль
                self.config.schedule_data["profiles"] = profiles
                self.refresh_list()

    def delete_profile(self):
        """Удаление профиля"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            return

        profile_name = current_item.text()
        # Извлекаем ключ профиля
        if "(" in profile_name:
            profile_key = profile_name.split("(")[1].split(")")[0].strip()
        else:
            profile_key = profile_name.strip()

        if profile_key == "default":
            QMessageBox.warning(
                self,
                self.tr("error_title", "Ошибка"),
                self.tr("cannot_delete_default", "Нельзя удалить профиль 'default'")
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("confirm_delete_title", "Подтверждение удаления"),
            self.tr("confirm_delete_text", f"Вы уверены, что хотите удалить профиль '{profile_key}'?"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.config.delete_profile(profile_key):
                self.refresh_list()
            else:
                QMessageBox.warning(
                    self,
                    self.tr("error_title", "Ошибка"),
                    self.tr("delete_failed", "Не удалось удалить профиль")
                )

    def activate_profile(self):
        """Активация выбранного профиля"""
        current_item = self.profile_list.currentItem()
        if not current_item:
            return

        profile_name = current_item.text()
        # Извлекаем ключ профиля
        if "(" in profile_name:
            profile_key = profile_name.split("(")[1].split(")")[0].strip()
        else:
            profile_key = profile_name.strip()

        self.config.set_current_profile(profile_key)
        self.config.save_schedule(self.config.schedule_data)

        # Обновляем главное окно
        if self.main_window_ref:
            self.main_window_ref.load_data()
            self.main_window_ref.select_day(self.main_window_ref.current_day)

        self.refresh_list()
        QMessageBox.information(
            self,
            self.tr("success_title", "Успешно"),
            self.tr("profile_activated", f"Профиль '{profile_key}' активирован")
        )
