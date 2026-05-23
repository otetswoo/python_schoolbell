#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import datetime
from pathlib import Path
import platform

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QLabel, QMenu, QFileDialog, QMessageBox,
    QHeaderView, QMenuBar, QDialog, QListWidget, QListWidgetItem, QCheckBox,
    QFormLayout, QSpinBox, QComboBox, QDialogButtonBox, QGroupBox, QSystemTrayIcon,
    QFrame,
)
from PySide6.QtGui import QColor, QFont, QPalette, QKeySequence, QIcon, QAction
from PySide6.QtCore import Qt, QTimer, QEvent

from src.config import (
    WEEK_DAYS, WEEK_DAYS_RU, WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN, VERSION,
    DEFAULT_SCHEDULE, SCHEDULE_PATH, PREFERENCES_FILE, ensure_dirs
)
from src.config_manager import ConfigManager
from src.sound_player import SoundPlayer
from src.music_player import MusicPlayer
from src.lesson_dialog import LessonDialog
from src.music_settings_dialog import MusicSettingsDialog
from src.bell_settings_dialog import BellSettingsDialog
from src.schedule_editor_dialog import ScheduleEditorDialog
from src.gui.localization import LOCALIZATION
from src.event_logger import EventLogger
from src.volume_control import VolumeControl

# Version of the application
APP_VERSION = VERSION

COLOR_CURRENT_LIGHT = QColor("#c8e6c9")
COLOR_SOON_LIGHT = QColor("#fff9c4")
COLOR_NORMAL_LIGHT = QColor("#ffffff")
PLAYBACK_TRIGGER_WINDOW_SECONDS = 60


class AnnouncementSelectDialog(QDialog):
    """Диалог выбора объявления для экстренного запуска."""
    
    def __init__(self, parent, active_announcements):
        """
        Args:
            parent: родительское окно
            active_announcements: список кортежей (index, announcement_dict)
        """
        super().__init__(parent)
        self.setWindowTitle("📢 Выберите объявление")
        self.resize(500, 350)
        self.selected_index = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        info = QLabel("Выберите объявление для воспроизведения:")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Список объявлений
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        
        for idx, ann in active_announcements:
            file_path = ann.get("file", "")
            file_name = file_path.split("/")[-1] if file_path else "(не выбран)"
            
            # Формируем описание
            repeat_days = ann.get("repeat_days", [])
            date_str = ann.get("date", "")
            time_str = ann.get("time", "")
            
            if repeat_days:
                # Преобразуем дни недели в русские названия
                day_names = []
                for day in repeat_days:
                    if day in WEEK_DAYS:
                        day_idx = WEEK_DAYS.index(day)
                        day_names.append(WEEK_DAYS_RU[day_idx])
                type_text = f"🔄 Повторяется: {', '.join(day_names)}"
            elif date_str:
                type_text = f"📅 Одноразовое ({date_str})"
            else:
                type_text = "❓ Неизвестный тип"
            
            item_text = f"{file_name}\n   {type_text}, время: {time_str}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, idx)  # Сохраняем индекс объявления
            self.list_widget.addItem(item)
        
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        
        layout.addLayout(btn_layout)
        
        # Выделяем первый элемент
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
    
    def on_item_double_clicked(self, item):
        """Обработчик двойного клика по элементу списка."""
        self.selected_index = item.data(Qt.UserRole)
        self.accept()
    
    def get_selected_index(self):
        """Возвращает индекс выбранного объявления."""
        if self.selected_index is not None:
            return self.selected_index
        
        # Если не было двойного клика, берем выделенный элемент
        current_item = self.list_widget.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        
        return None


class SchoolBell(QMainWindow):
    def __init__(self):
        super().__init__()

        ensure_dirs()

        self.config = ConfigManager()
        self.config.load_schedule()
        self.config.load_preferences()

        self.current_locale = self.config.get_locale()

        # Инициализация логгера
        self.logger = EventLogger()
        self.logger.log_event("info", "Application started")

        self.sound_player = SoundPlayer(logger=self.logger)
        self.music_player = MusicPlayer(sound_player=self.sound_player, logger=self.logger)
        # Устанавливаем callback для уведомления об окончании музыки
        self.music_player.is_music_playing_callback = self._on_music_finished

        self.schedule_variants = {}
        self.day_variants = {d: "usual" for d in WEEK_DAYS_RU}
        self.current_day = None
        self.current_variant = "usual"
        self.last_day = None  # Для отслеживания смены дня

        self.played_events = {}
        # Загружаем состояние звонков из настроек, по умолчанию True
        bells_prefs = self.config.preferences.get("bells", {})
        self.bells_enabled = bells_prefs.get("enabled", True)
        self.current_playing_track = None
        self.main_window_message = None
        
        # Блокировка для предотвращения гонок условий при воспроизведении
        self._playback_lock = False

        music_settings = self.config.get_music_settings()
        self.music_enabled = music_settings.get("enabled", False)

        anthem_settings = self.config.get_anthem_settings()
        self.anthem_enabled = anthem_settings.get("enabled", False)

        active = self.config.get_active_announcements()
        self.announcement_enabled = len(active) > 0

        # Настройки системного трея
        self.tray_icon = None
        self.force_quit = False
        self.setup_tray_icon()

        self.init_ui()
        self.load_data()
        self.set_today_schedule()

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start(1000)

        self.bell_timer = QTimer()
        self.bell_timer.timeout.connect(self.check_bells)
        self.bell_timer.start(500)
        
        # Таймер для проверки окончания музыки
        self.music_check_timer = QTimer()
        self.music_check_timer.timeout.connect(self._check_music_status)
        self.music_check_timer.start(1000)

    def _check_music_status(self):
        """Проверяет, закончилась ли музыка на перемене."""
        self.music_player.check_music_finished()

    def _texts(self, locale=None):
        """Возвращает локализацию с fallback на русский для новых/отсутствующих ключей."""
        texts = LOCALIZATION.get("ru", {}).copy()
        texts.update(LOCALIZATION.get(locale or self.current_locale, {}))
        return texts

    def tr(self, key, fallback=None):
        """Безопасно возвращает строку интерфейса без KeyError при старых настройках локализации."""
        return self._texts().get(key, fallback if fallback is not None else key)

    def init_ui(self):
        # Создаем интерфейс программно
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(8, 8, 8, 8)
        
        # Устанавливаем заголовок окна
        self.setWindowTitle(self.tr("app_title"))
        
        # Создаем основной горизонтальный layout (controls слева, table справа)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(6)
        
        # === ЛЕВАЯ ПАНЕЛЬ: Кнопки управления и чекбоксы ===
        controls_frame = QFrame()
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setSpacing(6)
        controls_frame.setMinimumWidth(160)
        controls_frame.setMaximumWidth(160)
        
        # Кнопки Edit и Today
        self.edit_btn = QPushButton(self.tr("btn_edit", "Edit"))
        self.edit_btn.setMinimumHeight(30)
        controls_layout.addWidget(self.edit_btn)
        
        self.today_btn = QPushButton(self.tr('btn_today'))
        self.today_btn.setMinimumHeight(30)
        self.today_btn.setToolTip(self.tr("navigate_to_current_day", "Navigate to current day"))
        controls_layout.addWidget(self.today_btn)
        
        controls_layout.addSpacing(8)
        
        # Чекбоксы
        self.bells_checkbox = QCheckBox(self.tr("chk_bells", "Bells"))
        controls_layout.addWidget(self.bells_checkbox)
        
        self.music_checkbox = QCheckBox(self.tr("chk_music", "Music"))
        controls_layout.addWidget(self.music_checkbox)
        
        self.anthem_checkbox = QCheckBox(self.tr("chk_anthem", "Anthem"))
        controls_layout.addWidget(self.anthem_checkbox)
        
        self.announcement_checkbox = QCheckBox(self.tr("chk_announcement", "Announcement"))
        controls_layout.addWidget(self.announcement_checkbox)
        
        controls_layout.addStretch()
        
        # Добавляем левую панель в основной layout
        content_layout.addWidget(controls_frame)
        
        # === ПРАВАЯ ПАНЕЛЬ: Таблица расписания ===
        self.scheduleTable = QTableWidget()
        self.scheduleTable.setMinimumWidth(300)
        self.scheduleTable.setColumnCount(3)
        self.scheduleTable.setHorizontalHeaderLabels([
            self.tr("col_start", "Start"),
            self.tr("col_end", "End"),
            self.tr("col_break", "Break")
        ])
        self.scheduleTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.scheduleTable.setEditTriggers(QTableWidget.NoEditTriggers)
        self.scheduleTable.setSelectionMode(QTableWidget.NoSelection)
        self.scheduleTable.verticalHeader().setDefaultSectionSize(24)
        self.scheduleTable.setAlternatingRowColors(True)
        
        content_layout.addWidget(self.scheduleTable, stretch=1)
        
        main_layout.addLayout(content_layout, stretch=1)
        
        # === НИЖНЯЯ ЧАСТЬ: Громкость, кнопки, статус ===
        
        # Группа громкости
        self.volumeGroup = QGroupBox(self.tr("volume_group", "Volume"))
        self.volumeLayout = QHBoxLayout(self.volumeGroup)
        main_layout.addWidget(self.volumeGroup)
        
        # Панель кнопок управления
        buttons_frame = QFrame()
        bottom_layout = QHBoxLayout(buttons_frame)
        bottom_layout.setSpacing(8)
        
        self.bell_btn = QPushButton()
        self.bell_btn.setMinimumHeight(34)
        bottom_layout.addWidget(self.bell_btn)
        
        self.music_btn = QPushButton()
        self.music_btn.setMinimumHeight(34)
        bottom_layout.addWidget(self.music_btn)
        
        self.anthem_btn = QPushButton()
        self.anthem_btn.setMinimumHeight(34)
        bottom_layout.addWidget(self.anthem_btn)
        
        self.announcement_btn = QPushButton()
        self.announcement_btn.setMinimumHeight(34)
        bottom_layout.addWidget(self.announcement_btn)
        
        self.stop_btn = QPushButton(self.tr("btn_stop", "Stop"))
        self.stop_btn.setMinimumHeight(34)
        self.stop_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
        bottom_layout.addWidget(self.stop_btn)
        
        main_layout.addWidget(buttons_frame)
        
        # Строка статуса
        self.statusLabel = QLabel(self.tr("status_ready", "Ready"))
        self.statusLabel.setMinimumHeight(35)
        self.statusLabel.setStyleSheet("background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        self.statusLabel.setWordWrap(True)
        main_layout.addWidget(self.statusLabel)
        
        # Создаем контейнер для кнопок дней недели
        days_container = QWidget()
        self.days_layout = QHBoxLayout(days_container)
        self.days_layout.setSpacing(5)
        days_container.setMaximumHeight(42)
        
        # Вставляем кнопки дней недели над основным контентом
        main_layout.insertWidget(0, days_container)
        
        # Инициализируем кнопки дней недели
        self.day_buttons = {}
        for i, (short_ru, short_en) in enumerate(zip(WEEK_DAYS_SHORT, WEEK_DAYS_SHORT_EN)):
            short = short_ru if self.current_locale == "ru" else short_en
            full = WEEK_DAYS_RU[i]

            btn = QPushButton(short)
            btn.setMinimumHeight(30)
            btn.setToolTip(full + "\nЛКМ - выбрать день\nПКМ - переключить вариант расписания")
            btn.clicked.connect(lambda checked=False, d=full: self.select_day(d))
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(lambda pos, d=full: self.on_day_clicked(d))
            btn.setCheckable(True)
            self.days_layout.addWidget(btn)
            self.day_buttons[full] = btn
        
        # Создаем меню вручную
        self._create_menu()

        # Подключаем чекбоксы
        self.bells_checkbox.setChecked(self.bells_enabled)
        self.bells_checkbox.stateChanged.connect(self.on_bells_toggled)
        
        music_settings = self.config.get_music_settings()
        self.music_checkbox.setChecked(music_settings.get("enabled", False))
        self.music_checkbox.stateChanged.connect(self.on_music_toggled)
        
        anthem_settings = self.config.get_anthem_settings()
        self.anthem_checkbox.setChecked(anthem_settings.get("enabled", False))
        self.anthem_checkbox.stateChanged.connect(self.on_anthem_toggled)
        
        active = self.config.get_active_announcements()
        self.announcement_checkbox.setChecked(len(active) > 0)
        self.announcement_checkbox.stateChanged.connect(self.on_announcement_toggled)

        # Создаем контролы громкости
        self.volume_controls = {}
        self._create_volume_control(self.volumeLayout, "bell", self.config.get_volume("start"))
        self._create_volume_control(self.volumeLayout, "music", self.config.get_volume("music"))

        # Подключаем кнопки
        self.edit_btn.clicked.connect(self.edit_schedule)
        self.today_btn.clicked.connect(self.set_today_schedule)
        self.bell_btn.clicked.connect(self.manual_bell)
        self.music_btn.clicked.connect(self.manual_music)
        self.anthem_btn.clicked.connect(self.manual_anthem)
        self.announcement_btn.clicked.connect(self.manual_announcement)
        self.stop_btn.clicked.connect(self.manual_stop)
        
        # Обновляем текст кнопок
        self.bell_btn.setText("▶️ " + self.tr("btn_bell").replace("🔔", "").strip())
        self.music_btn.setText("▶️ " + self.tr("btn_music").replace("🎵", "").strip())
        self.anthem_btn.setText(self._get_anthem_button_text())
        self.announcement_btn.setText(self._get_announcement_button_text())
        
        # Обновляем статус
        self.statusLabel.setText(self.tr("status_ready"))
        self.statusLabel.setStyleSheet("background-color: #f5f5f5; padding: 8px; border-radius: 4px;")
        
        # Настраиваем меню
        self.setup_menu()
        self._apply_compact_style()

    def _create_volume_control(self, parent_layout, volume_type, value):
        """Создает подписанный ползунок громкости для главного окна."""
        control = VolumeControl(self.tr(f"volume_{volume_type}"), value, self)
        control.value_changed.connect(
            lambda new_value, vt=volume_type: self.on_volume_changed(vt, new_value)
        )
        parent_layout.addWidget(control)
        self.volume_controls[volume_type] = control


    def _apply_compact_style(self):
        """Применяет компактный современный стиль интерфейса."""
        self.setStyleSheet("""
            QWidget { font-size: 12px; }
            QPushButton {
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 4px 8px;
                background: #f7f7f7;
            }
            QPushButton:hover { background: #ededed; }
            QPushButton:checked { background: #dceeff; border-color: #8ab4f8; }
            QTableWidget {
                border: 1px solid #dadada;
                border-radius: 8px;
                gridline-color: #e8e8e8;
            }
            QHeaderView::section {
                background: #f2f2f2;
                border: none;
                border-bottom: 1px solid #dddddd;
                padding: 4px;
            }
            QGroupBox { border: 1px solid #dadada; border-radius: 8px; margin-top: 8px; padding-top: 8px; }
        """)

    def export_all_settings(self):
        """Экспортирует все настройки приложения в один YAML-файл."""
        fname, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("export_settings_title", "Export all settings"),
            str(SCHEDULE_PATH.parent / "school_bell_export.yml"),
            "YAML (*.yml *.yaml)",
        )
        if not fname:
            return

        try:
            import yaml

            export_data = {
                "meta": {
                    "app": "school_bell",
                    "version": "1",
                    "exported_at": datetime.datetime.now().isoformat(),
                },
                "schedule": self.config.schedule_data or {},
                "preferences": self.config.preferences or {},
                "runtime": {
                    "day_variants": self.day_variants,
                    "current_locale": self.current_locale,
                },
            }

            with open(fname, "w", encoding="utf-8") as f:
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

            QMessageBox.information(self, "OK", self.tr("export_settings_done", "Settings exported successfully"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("error_title", "Error"), str(e))

    def import_all_settings(self):
        """Импортирует все настройки приложения из YAML-файла экспорта."""
        fname, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("action_import_settings", "Import all settings..."),
            str(SCHEDULE_PATH.parent),
            "YAML (*.yml *.yaml)",
        )
        if not fname:
            return
        try:
            import yaml
            with open(fname, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            self.config.schedule_data = data.get("schedule", {}) or {}
            self.config.preferences = data.get("preferences", {}) or {}
            self.current_locale = data.get("runtime", {}).get("current_locale", self.config.get_locale())
            self.config.save_schedule(self.config.schedule_data)
            self.config.save_preferences(self.config.preferences)
            self.load_data()
            self._retranslate_ui()
            QMessageBox.information(self, "OK", self.tr("import_settings_done", "Settings imported successfully"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("error_title", "Error"), str(e))

    def on_volume_changed(self, volume_type, value):
        """Сохраняет изменения громкости из ползунков главного окна."""
        if volume_type == "bell":
            self.config.set_volume("start", value)
            self.config.set_volume("end", value)
            self.sound_player.set_volume(value)
        else:
            self.config.set_volume(volume_type, value)
            if volume_type == "music" and self.sound_player.is_playing("music"):
                self.sound_player.set_volume(value)
        self.config.save_preferences(self.config.preferences)

    def _create_menu(self):
        """Создает меню программно"""
        menubar = self.menuBar()
        
        # Меню File
        self.menuFile = QMenu(self.tr("menu_file", "File"), menubar)
        self.actionLoad = QAction(self.tr("action_load", "Load..."), self)
        self.actionLoad.setShortcut(QKeySequence("Ctrl+O"))
        self.actionSave = QAction(self.tr("action_save", "Save"), self)
        self.actionSave.setShortcut(QKeySequence("Ctrl+S"))
        self.actionExportSettings = QAction(self.tr("action_export_settings", "Export all settings..."), self)
        self.actionExportSettings.setShortcut(QKeySequence("Ctrl+E"))
        self.actionImportSettings = QAction(self.tr("action_import_settings", "Import all settings..."), self)
        self.actionImportSettings.setShortcut(QKeySequence("Ctrl+I"))
        self.actionExit = QAction(self.tr("action_exit", "Exit"), self)
        self.actionExit.setShortcut(QKeySequence("Ctrl+Q"))
        
        self.menuFile.addAction(self.actionLoad)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionImportSettings)
        self.menuFile.addAction(self.actionExportSettings)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        menubar.addMenu(self.menuFile)
        
        # Меню Settings
        self.menuSettings = QMenu(self.tr("menu_settings", "Settings"), menubar)
        
        self.actionSounds = QAction(self.tr("action_sounds", "Bell melodies..."), self.menuSettings)
        
        self.actionMusic = QAction(self.tr("action_music", "Music Break..."), self)
        self.actionAnthem = QAction(self.tr("action_anthem", "Anthem..."), self)
        self.actionAnnouncement = QAction(self.tr("action_announcement", "Announcement..."), self)
        self.actionTemplates = QAction(self.tr("action_templates", "Edit Templates"), self)
        
        # Подменю Language
        self.menuLanguage = QMenu(self.tr("menu_language", "Language"), self.menuSettings)
        self.actionLocaleRu = QAction(self.tr("action_locale_ru", "Russian"), self.menuLanguage)
        self.actionLocaleEn = QAction(self.tr("action_locale_en", "English"), self.menuLanguage)
        self.menuLanguage.addAction(self.actionLocaleRu)
        self.menuLanguage.addAction(self.actionLocaleEn)
        
        self.menuSettings.addAction(self.actionSounds)
        self.menuSettings.addAction(self.actionMusic)
        self.menuSettings.addAction(self.actionAnthem)
        self.menuSettings.addAction(self.actionAnnouncement)
        self.menuSettings.addAction(self.actionTemplates)
        self.menuSettings.addSeparator()
        self.actionProfiles = QAction(
            self.tr("action_profiles", "Профили расписания..."), self)
        self.actionLog = QAction(
            self.tr("action_log", "Журнал событий..."), self)
        self.menuSettings.addAction(self.actionProfiles)
        self.menuSettings.addAction(self.actionLog)
        self.menuSettings.addMenu(self.menuLanguage)
        menubar.addMenu(self.menuSettings)
        
        # Меню Help
        self.menuHelp = QMenu(self.tr("menu_help", "Help"), menubar)
        self.actionAbout = QAction(self.tr("action_about", "About"), self)
        self.menuHelp.addAction(self.actionAbout)
        menubar.addMenu(self.menuHelp)
        
        # Действие Today (доступно через Ctrl+T)
        self.actionToday = QAction(self.tr("action_today", "Today"), self)
        self.actionToday.setShortcut(QKeySequence("Ctrl+T"))
        self.addAction(self.actionToday)
    
    def setup_menu(self):
        # Подключаем действия меню
        self.actionLoad.triggered.connect(self.load_schedule)
        self.actionSave.triggered.connect(self.save_schedule)
        self.actionExportSettings.triggered.connect(self.export_all_settings)
        self.actionImportSettings.triggered.connect(self.import_all_settings)
        self.actionExit.triggered.connect(self.close)
        self.actionSounds.triggered.connect(self.show_bell_settings)
        self.actionMusic.triggered.connect(self.show_music_settings)
        self.actionAnthem.triggered.connect(self.show_anthem_settings)
        self.actionAnnouncement.triggered.connect(self.show_announcement_settings)
        self.actionTemplates.triggered.connect(self.show_templates_editor)
        self.actionLog.triggered.connect(self.show_log_viewer)
        self.actionProfiles.triggered.connect(self.show_profiles_dialog)
        self.actionLocaleRu.triggered.connect(lambda: self.set_locale("ru"))
        self.actionLocaleEn.triggered.connect(lambda: self.set_locale("en"))
        self.actionAbout.triggered.connect(self.show_about)
        self.actionToday.triggered.connect(self.set_today_schedule)

    def show_about(self):
        """Показать диалог 'О программе'"""
        about_text = self.tr("about_text").format(version=APP_VERSION)
        QMessageBox.about(self, self.tr("about_title"), about_text)

    def show_templates_editor(self):
        """Открыть диалог редактирования шаблонов расписания"""
        from src.templates_dialog import TemplatesEditorDialog
        dlg = TemplatesEditorDialog(self, self.schedule_variants, self.config)
        if dlg.exec() == QDialog.Accepted:
            new_templates = dlg.get_templates()
            # Обновляем шаблоны для всех дней
            for key in WEEK_DAYS:
                for variant in ["usual", "short"]:
                    if variant in new_templates:
                        self.schedule_variants[key][variant] = list(new_templates[variant])
            QMessageBox.information(self, "OK", "Шаблоны обновлены")

    def load_data(self):
        prefs = self.config.preferences

        variants = prefs.get("variants", {})
        schedule_days = self.config.schedule_data.get("days", {}) if self.config.schedule_data else {}
        for i, day_ru in enumerate(WEEK_DAYS_RU):
            day_key = WEEK_DAYS[i]
            self.day_variants[day_ru] = (
                variants.get(day_ru)
                or variants.get(day_key)
                or schedule_days.get(day_key)
                or self.day_variants.get(day_ru, "usual")
            )

        sounds = DEFAULT_SCHEDULE["sounds"].copy()
        sounds.update(prefs.get("sounds", {}))
        self.sounds = sounds

        music = self.config.get_music_settings()
        folders = music.get("folders", [])
        if music.get("enabled") and folders:
            self.music_player.set_music_folders(folders)

        # Загружаем шаблоны из текущего профиля
        current_profile = self.config.get_current_profile()
        templates = self.config.get_profile_schedules(current_profile)
        if not templates:
            templates = self.config.schedule_data.get("schedules", DEFAULT_SCHEDULE["schedules"])

        for key in WEEK_DAYS:
            self.schedule_variants[key] = {
                "usual": list(templates.get("usual", [])),
                "short": list(templates.get("short", [])),
                "none": []
            }

    def select_day(self, day_ru):
        self.current_day = day_ru
        variant = self.day_variants.get(day_ru, "usual")
        self.current_variant = variant

        idx = WEEK_DAYS_RU.index(day_ru)
        key = WEEK_DAYS[idx]

        lessons = self.schedule_variants.get(key, {}).get(variant, [])

        self.scheduleTable.setRowCount(0)
        for l in lessons:
            row = self.scheduleTable.rowCount()
            self.scheduleTable.insertRow(row)
            self.scheduleTable.setItem(row, 0, QTableWidgetItem(l.get("start", "")))
            self.scheduleTable.setItem(row, 1, QTableWidgetItem(l.get("end", "")))
            # Третий столбец - длительность перемены (время от конца текущего до начала следующего)
            break_duration = self._calculate_break_duration(l, lessons)
            self.scheduleTable.setItem(row, 2, QTableWidgetItem(break_duration))

        self._update_day_buttons_style()

    def _calculate_break_duration(self, lesson, all_lessons):
        """Вычисляет длительность перемены после данного урока.
        
        Args:
            lesson: текущий урок со временем end
            all_lessons: список всех уроков
            
        Returns:
            строка с длительностью перемены в формате "X мин" или пустая строка
        """
        try:
            current_end = lesson.get("end", "")
            if not current_end:
                return ""
            
            # Находим следующий урок
            current_idx = all_lessons.index(lesson)
            if current_idx >= len(all_lessons) - 1:
                # Это последний урок, перемены нет
                return ""
            
            next_lesson = all_lessons[current_idx + 1]
            next_start = next_lesson.get("start", "")
            if not next_start:
                return ""
            
            # Парсим время
            end_time = self._parse_time(current_end)
            start_time = self._parse_time(next_start)
            
            # Вычисляем разницу в минутах
            today = datetime.datetime.now().date()
            end_dt = datetime.datetime.combine(today, end_time)
            start_dt = datetime.datetime.combine(today, start_time)
            
            diff_seconds = (start_dt - end_dt).total_seconds()
            if diff_seconds < 0:
                return ""
            
            diff_minutes = int(diff_seconds / 60)
            return f"{diff_minutes} {self.tr('min', 'мин')}"
        except Exception:
            return ""

    def _update_day_buttons_style(self):
        """Обновляет стиль кнопок дней недели: выделяет текущий день и показывает варианты"""
        for day_ru, btn in self.day_buttons.items():
            variant = self.day_variants.get(day_ru, "usual")

            if day_ru == self.current_day:
                btn.setChecked(True)
            else:
                btn.setChecked(False)

            # Меняем текст кнопки в зависимости от варианта
            idx = WEEK_DAYS_RU.index(day_ru)
            short = WEEK_DAYS_SHORT[idx] if self.current_locale == "ru" else WEEK_DAYS_SHORT_EN[idx]

            if variant == "short":
                suffix = "(К)" if self.current_locale == "ru" else "(S)"
                btn.setText(short + f" {suffix}")
            elif variant == "none":
                suffix = self.tr("no_schedule", "Нет") if self.current_locale == "ru" else self.tr("no_schedule", "No")
                btn.setText(short + f" ({suffix})")
            else:
                btn.setText(short)

    def on_day_clicked(self, day_ru):
        """Обработчик клика на день недели - переключает вариант расписания"""
        current_variant = self.day_variants.get(day_ru, "usual")
        # Циклическое переключение: usual -> short -> none -> usual
        next_variant = {"usual": "short", "short": "none", "none": "usual"}[current_variant]
        self.day_variants[day_ru] = next_variant
        self.config.set_day_variant(day_ru, next_variant)
        self.config.save_preferences(self.config.preferences)

        self._update_day_buttons_style()

        # Если клик был на текущем дне, обновляем таблицу
        if day_ru == self.current_day:
            self.select_day(day_ru)

    def set_today_schedule(self):
        today = datetime.datetime.today()
        idx = today.weekday()
        day_ru = WEEK_DAYS_RU[idx]
        # Обновляем текст кнопки Сегодня (только надпись, без даты)
        self.today_btn.setText(self.tr('btn_today'))

        # Сбрасываем кэш при смене дня
        self._reset_daily_state(WEEK_DAYS[idx])

        self.select_day(day_ru)

    def edit_schedule(self):
        if not self.current_day:
            QMessageBox.warning(self, "Ошибка", "Выберите день")
            return

        idx = WEEK_DAYS_RU.index(self.current_day)
        key = WEEK_DAYS[idx]
        lessons = self.schedule_variants.get(key, {}).get(self.current_variant, [])

        dlg = ScheduleEditorDialog(self, self.current_day, self.current_variant, lessons, self.schedule_variants)
        if dlg.exec() == QDialog.Accepted:
            new_lessons = dlg.get_lessons()
            self.schedule_variants[key][self.current_variant] = new_lessons
            self.select_day(self.current_day)
            QMessageBox.information(self, "OK", "Расписание обновлено")

    def update_ui(self):
        now = datetime.datetime.now()

        day_names_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        day_names_en = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        day_name = day_names_ru[now.weekday()] if self.current_locale == "ru" else day_names_en[now.weekday()]

        month_names_ru = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
        month_names_en = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_name = month_names_ru[now.month - 1] if self.current_locale == "ru" else month_names_en[now.month - 1]

        time_str = now.strftime("%H:%M")
        # Форматируем дату с жирным выделением для лучшей читаемости
        if self.current_locale == "ru":
            date_html = f"<b>{day_name}, {now.day} {month_name}</b> {time_str}"
        else:
            date_html = f"<b>{day_name}, {month_name} {now.day}</b> {time_str}"
        status = f"{self.tr('btn_today').replace('📅', '').strip()} {date_html}"

        cur, seconds_left, next_seconds, is_break = self.get_current_lesson(now)

        if cur:
            mins = seconds_left // 60
            lesson_text = f"Урок {cur.get('num')}" if self.current_locale == "ru" else f"Lesson {cur.get('num')}"
            status += f"   |   {lesson_text}, {mins} мин" if self.current_locale == "ru" else f"   |   {lesson_text}, {mins} min"
            
            # Добавляем время до перемены (звонка)
            bell_mins = mins
            bell_secs = seconds_left % 60
            if self.current_locale == "ru":
                status += f" ({bell_mins}:{bell_secs:02d} до звонка)"
            else:
                status += f" ({bell_mins}:{bell_secs:02d} to bell)"
                
        elif is_break:
            # Сейчас перемена - показываем время до следующего урока
            next_mins = next_seconds // 60
            next_secs = next_seconds % 60
            if self.current_locale == "ru":
                status += f"   |   Перемена, следующий урок через {next_mins} мин {next_secs} сек"
            else:
                status += f"   |   Break, next lesson in {next_mins} min {next_secs} sec"
        elif next_seconds is not None and next_seconds > 0:
            # Показываем время до следующего звонка
            next_mins = next_seconds // 60
            next_secs = next_seconds % 60
            if self.current_locale == "ru":
                status += f"   |   Следующий звонок через {next_mins} мин {next_secs} сек"
            else:
                status += f"   |   Next bell in {next_mins} min {next_secs} sec"
        else:
            status += f"   |   {self.tr('status_lessons_finished', 'Lessons are finished')}"

        # Добавляем индикатор текущего воспроизведения
        if hasattr(self, 'current_playing_track') and self.current_playing_track:
            track_name = Path(self.current_playing_track).name if self.current_playing_track else ""
            playing_text = f"   |   ▶️ {track_name}" if self.current_locale == "ru" else f"   |   ▶️ {track_name}"
            status += playing_text

        if self.main_window_message:
            status += f"   |   ⚠️ {self.main_window_message}"

        self.statusLabel.setTextFormat(Qt.RichText)
        self.statusLabel.setText(status)
        self.highlight_table(now, is_break=is_break)

    def get_current_lesson(self, now):
        """Возвращает текущий урок и информацию о следующем звонке

        Returns:
            tuple: (текущий_урок, секунд_осталось, секунд_до_следующего, является_ли_переменой)
        """
        if not self.current_day:
            return None, None, None, False

        idx = WEEK_DAYS_RU.index(self.current_day)
        key = WEEK_DAYS[idx]
        lessons = self.schedule_variants.get(key, {}).get(self.current_variant, [])

        today = now.date()
        parsed = []
        for l in lessons:
            try:
                s = self._lesson_datetime(l, "start", today)
                e = self._lesson_datetime(l, "end", today)
                parsed.append((s, e, l))
            except:
                continue

        # Проверяем, на уроке ли мы сейчас
        for s, e, l in parsed:
            if s <= now <= e:
                return l, int((e - now).total_seconds()), None, False

        # Проверяем, на перемене ли мы сейчас (между уроками)
        for i in range(len(parsed) - 1):
            s_curr, e_curr, l_curr = parsed[i]
            s_next, e_next, l_next = parsed[i + 1]
            
            if e_curr < now < s_next:
                # Сейчас перемена между уроками
                return None, None, int((s_next - now).total_seconds()), True
        
        # Ищем следующий звонок (первый урок дня)
        for s, e, l in parsed:
            if now < s:
                return None, None, int((s - now).total_seconds()), False

        return None, None, None, False

    def highlight_table(self, now, is_break=False):
        """Подсвечивает текущий урок или перемену в таблице.
        
        Args:
            now: текущее время
            is_break: True если сейчас перемена (для явного выделения)
        """
        rows = self.scheduleTable.rowCount()
        today = now.date()

        # Используем только светлую тему
        color_current = COLOR_CURRENT_LIGHT
        color_soon = COLOR_SOON_LIGHT
        color_normal = COLOR_NORMAL_LIGHT
        
        # Найти индекс последнего завершившегося урока
        last_ended_row = None
        for r in range(rows):
            try:
                end_str = self.scheduleTable.item(r, 1).text()
                end = datetime.datetime.combine(today, self._parse_time(end_str))
                if end < now:
                    last_ended_row = r
            except:
                continue

        for r in range(rows):
            try:
                start_str = self.scheduleTable.item(r, 0).text()
                end_str = self.scheduleTable.item(r, 1).text()
                start = datetime.datetime.combine(today, self._parse_time(start_str))
                end = datetime.datetime.combine(today, self._parse_time(end_str))

                if start <= now <= end:
                    bg = color_current
                elif is_break and r == last_ended_row:
                    bg = color_soon  # только последний завершившийся
                elif 0 <= (start - now).total_seconds() <= 120:
                    bg = color_soon
                else:
                    bg = color_normal

                # Применяем цвет ко всем ячейкам строки (включая столбец с переменой)
                for c in range(3):
                    item = self.scheduleTable.item(r, c)
                    if item:
                        item.setBackground(bg)

            except Exception as e:
                # Игнорируем ошибки парсинга времени для пустых или некорректных строк
                continue

    def _parse_time(self, time_str):
        """Преобразует строку HH:MM или HH:MM:SS в объект time."""
        if not time_str:
            raise ValueError("empty time")

        parts = str(time_str).strip().split(":")
        if len(parts) == 2:
            hour, minute = map(int, parts)
            return datetime.time(hour=hour, minute=minute)
        if len(parts) == 3:
            hour, minute, second = map(int, parts)
            return datetime.time(hour=hour, minute=minute, second=second)
        return datetime.time.fromisoformat(str(time_str).strip())

    def _lesson_datetime(self, lesson, field, date_obj):
        return datetime.datetime.combine(date_obj, self._parse_time(lesson[field]))

    def _event_cache_key(self, event_type, event_time):
        return f"{event_type}_{event_time.strftime('%Y%m%d_%H%M')}"

    def _is_time_to_play(self, now, scheduled_time):
        diff = (now - scheduled_time).total_seconds()
        return 0 <= diff < PLAYBACK_TRIGGER_WINDOW_SECONDS

    def _set_main_window_message(self, message_key, fallback):
        message = self.tr(message_key, fallback)
        message_changed = self.main_window_message != message
        self.main_window_message = message
        if hasattr(self, "statusLabel"):
            self.statusLabel.setText(f"⚠️ {message}")
        if message_changed:
            self.logger.log_event("warning", message)

    def _clear_main_window_message(self):
        self.main_window_message = None

    def _get_variant_for_day_key(self, day_key):
        """Возвращает вариант расписания для дня, поддерживая старые и новые настройки."""
        day_ru = WEEK_DAYS_RU[WEEK_DAYS.index(day_key)]
        variants = self.config.preferences.get("variants", {})

        variant = variants.get(day_ru) or variants.get(day_key)
        if not variant and self.config.schedule_data:
            variant = self.config.schedule_data.get("days", {}).get(day_key)
        return variant or self.day_variants.get(day_ru, "usual")

    def _get_lessons_for_day_key(self, day_key):
        variant = self._get_variant_for_day_key(day_key)
        return self.schedule_variants.get(day_key, {}).get(variant, [])

    def _resolve_existing_file(self, path):
        """Возвращает абсолютный Path для существующего файла или None."""
        if not path:
            return None

        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = SCHEDULE_PATH.parent / resolved_path
        return resolved_path if resolved_path.exists() else None

    def _get_sound_path(self, sound_type):
        """Возвращает существующий путь к звуку с fallback на настройки по умолчанию."""
        candidates = [self.sounds.get(sound_type), DEFAULT_SCHEDULE["sounds"].get(sound_type)]
        for candidate in candidates:
            path = self._resolve_existing_file(candidate)
            if path:
                return str(path)
        return ""

    def _reset_daily_state(self, day_key):
        """Сбрасывает кэш событий и состояние музыки при смене календарного дня."""
        if self.last_day == day_key:
            return

        self.logger.log_event("info", f"New day: {WEEK_DAYS_RU[WEEK_DAYS.index(day_key)]}")
        self.played_events.clear()
        self.music_player.reset_daily()
        self.current_playing_track = None
        self.last_day = day_key
        
        # Сбрасываем played для повторяющихся объявлений
        changed = False
        for ann in self.config.get_announcements():
            if ann.get("repeat_days") and ann.get("played", False):
                ann["played"] = False
                ann["enabled"] = True
                changed = True
        if changed:
            self.config.save_preferences(self.config.preferences)

    def _play_cached_audio(self, event_type, event_time, path, volume, status_text=None, log_message=None):
        """Проигрывает событие один раз в минутном окне и помечает его в кэше.
        
        Использует блокировку для предотвращения гонок условий при одновременных вызовах.
        Приоритет событий: anthem > announcement > start/end > music
        """
        cache_key = self._event_cache_key(event_type, event_time)
        if cache_key in self.played_events:
            return False
        
        # Проверка блокировки для предотвращения гонок
        if self._playback_lock:
            # Если уже идет воспроизведение, проверяем приоритет
            current_type = self.sound_player.current_type
            # Более важные события могут прервать менее важные
            priority_order = {"anthem": 0, "announcement": 1, "start": 2, "end": 2, "music": 3}
            new_priority = priority_order.get(event_type, 99)
            current_priority = priority_order.get(current_type, 99)
            
            if new_priority >= current_priority:
                # Менее важное или равное событие не прерывает текущее
                self.played_events[cache_key] = True  # Помечаем как сыгранное
                return False
        
        # Устанавливаем блокировку
        self._playback_lock = True
        try:
            self.sound_player.stop_all()
            if self.sound_player.play(str(path), event_type, volume=volume):
                self._clear_main_window_message()
                self.played_events[cache_key] = True
                if status_text:
                    self.statusLabel.setText(status_text)
                if log_message:
                    category = "bell" if event_type in {"start", "end"} else event_type
                    self.logger.log_event(category, log_message)
                return True
            return False
        finally:
            # Снимаем блокировку после небольшой задержки
            # Это позволяет избежать мгновенного повторного захвата
            self._playback_lock = False

    def play_bell(self, bell_type, event_time):
        if not self.bells_enabled:
            return

        path = self._get_sound_path(bell_type)
        if not path:
            self._set_main_window_message(
                "missing_bell_sound",
                "Мелодия звонка не выбрана. Выберите звук в настройках.",
            )
            return

        self._play_cached_audio(
            bell_type,
            event_time,
            path,
            self.config.get_volume(bell_type),
        )

    def play_break_music(self, event_time=None):
        """Воспроизведение музыки на перемене."""
        if event_time:
            cache_key = self._event_cache_key("music", event_time)
            if cache_key in self.played_events:
                return

        music_settings = self.config.get_music_settings()
        folders = music_settings.get("folders", [])
        if folders and not self.music_player.music_folders:
            self.music_player.set_music_folders(folders)

        if not self.music_player.music_folders:
            self._set_main_window_message(
                "missing_music_folder",
                "Папка с музыкой не выбрана. Выберите папку в настройках.",
            )
            return

        if self.sound_player.is_playing("announcement"):
            if event_time:
                self.played_events[cache_key] = True
            return

        volumes = self.config.get_volumes()
        music_volume = volumes.get("music", 50)

        if not self.music_player.can_play():
            self.current_playing_track = None
            return

        selected_tracks = set(music_settings.get("selected_tracks", []))
        track = self.music_player.get_next_track()
        if selected_tracks:
            attempts = 0
            while track and str(track) not in selected_tracks and attempts < 200:
                track = self.music_player.get_next_track()
                attempts += 1
        if track:
            self.sound_player.play_music(str(track), volume=music_volume)
            self._clear_main_window_message()
            self.music_player.mark_played()
            self.current_playing_track = str(track)
            if event_time:
                self.played_events[cache_key] = True
            self.logger.log_event("music", f"Break music: {Path(track).name}")
        else:
            self.current_playing_track = None
            self._set_main_window_message(
                "missing_music_tracks",
                "В выбранной папке нет аудиофайлов.",
            )

    def check_bells(self):
        now = datetime.datetime.now()
        today_key = WEEK_DAYS[now.weekday()]
        self._reset_daily_state(today_key)
        self.check_anthem(now)
        self.check_announcement(now)
        self.check_schedule_bells(now)

    def check_schedule_bells(self, now):
        """Проверка звонков и музыки по расписанию реального текущего дня."""
        today_key = WEEK_DAYS[now.weekday()]
        lessons = self._get_lessons_for_day_key(today_key)
        if not lessons:
            return

        music_settings = self.config.get_music_settings()
        music_delay = music_settings.get("delay_minutes", 2)
        try:
            music_delay = int(music_delay)
        except (TypeError, ValueError):
            music_delay = 2

        for lesson in lessons:
            try:
                start = self._lesson_datetime(lesson, "start", today_date)
                end = self._lesson_datetime(lesson, "end", today_date)

                if self.bells_enabled:
                    bell_events = (
                        ("start", start, f"Start bell: lesson {lesson.get('num')}"),
                        ("end", end, f"End bell: lesson {lesson.get('num')}"),
                    )
                    for bell_type, bell_time, log_message in bell_events:
                        if not self._is_time_to_play(now, bell_time):
                            continue

                        path = self._get_sound_path(bell_type)
                        if path:
                            self._play_cached_audio(
                                bell_type,
                                bell_time,
                                path,
                                self.config.get_volume(bell_type),
                                log_message=log_message,
                            )
                        else:
                            self._set_main_window_message(
                                "missing_bell_sound",
                                "Мелодия звонка не выбрана. Выберите звук в настройках.",
                            )

                if self.music_enabled:
                    music_time = end + datetime.timedelta(minutes=music_delay)
                    if self._is_time_to_play(now, music_time):
                        self.play_break_music(event_time=music_time)
            except Exception as e:
                self.logger.log_event("error", f"Error checking schedule events: {e}")
                continue

    def load_schedule(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Загрузить расписание", "", "YAML (*.yml *.yaml)")
        if fname:
            try:
                import yaml
                with open(fname, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                self.config.schedule_data = data
                self.load_data()
                self.set_today_schedule()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def save_schedule(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Сохранить расписание", str(SCHEDULE_PATH), "YAML (*.yml *.yaml)")
        if fname:
            try:
                import yaml
                days_out = {}
                for i, key in enumerate(WEEK_DAYS):
                    days_out[key] = self.day_variants.get(WEEK_DAYS_RU[i], "usual")

                # Сохраняем шаблоны (берём из первого дня как базовые)
                templates = {}
                first_key = WEEK_DAYS[0]
                for var in ["usual", "short"]:
                    templates[var] = list(self.schedule_variants.get(first_key, {}).get(var, []))

                data = {"days": days_out, "schedules": templates, "sounds": self.sounds}
                with open(fname, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def show_bell_settings(self):
        dlg = BellSettingsDialog(self, self.sounds, self.current_locale)
        if dlg.exec() == QDialog.Accepted:
            for bell_type in ("start", "end"):
                self.config.set_sound(bell_type, self.sounds.get(bell_type, ""))
            self.config.save_preferences(self.config.preferences)
            self.statusLabel.setText(self.tr("bell_settings_saved", "Bell melodies updated"))

    def show_music_settings(self):
        dlg = MusicSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            music = self.config.get_music_settings()
            folders = music.get("folders", [])
            if folders:
                self.music_player.set_music_folders(folders)
            self.config.save_preferences(self.config.preferences)

    def show_anthem_settings(self):
        """Открыть диалог настройки гимна"""
        from src.anthem_settings_dialog import AnthemSettingsDialog
        dlg = AnthemSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            self.config.save_preferences(self.config.preferences)

    def show_announcement_settings(self):
        """Открыть диалог настройки объявлений"""
        from src.announcement_settings_dialog import AnnouncementSettingsDialog
        dlg = AnnouncementSettingsDialog(self, self.config)
        if dlg.exec() == QDialog.Accepted:
            self.config.save_preferences(self.config.preferences)
            self._update_announcement_ui_state()

    def set_locale(self, locale):
        self.current_locale = locale
        self.config.set_locale(locale)
        self.config.save_preferences(self.config.preferences)

        self._retranslate_ui()

    def _retranslate_ui(self):
        texts = self._texts(self.current_locale)
        self.setWindowTitle(texts["app_title"])

        self._update_day_buttons_style()

        self.edit_btn.setText(texts["btn_edit"])
        self.statusLabel.setText(texts["status_ready"])
        self.bells_checkbox.setText(texts["chk_bells"])
        self.music_checkbox.setText(texts["chk_music"])
        self.anthem_checkbox.setText(texts["chk_anthem"])
        self.announcement_checkbox.setText(texts["chk_announcement"])
        self.volumeGroup.setTitle(texts["volume_group"])
        for volume_type, control in self.volume_controls.items():
            control.set_title(texts[f"volume_{volume_type}"])

        self.today_btn.setText(texts["btn_today"])
        self.bell_btn.setText("▶️ " + texts["btn_bell"].replace("🔔", "").strip())
        self.music_btn.setText("▶️ " + texts["btn_music"].replace("🎵", "").strip())
        self.anthem_btn.setText(self._get_anthem_button_text())
        self.announcement_btn.setText(self._get_announcement_button_text())
        self.stop_btn.setText(texts["btn_stop"])

        headers = [self.tr("col_start", "Start"), self.tr("col_end", "End"), self.tr("col_break", "Break")]
        self.scheduleTable.setHorizontalHeaderLabels(headers)

        self.menuFile.setTitle(texts["menu_file"])
        self.actionLoad.setText(texts["action_load"])
        self.actionSave.setText(texts["action_save"])
        self.actionExportSettings.setText(texts["action_export_settings"])
        self.actionImportSettings.setText(texts["action_import_settings"])
        self.actionExit.setText(texts["action_exit"])

        self.menuSettings.setTitle(texts["menu_settings"])
        self.actionSounds.setText(texts["action_sounds"])
        self.actionMusic.setText(texts["action_music"])
        self.actionAnthem.setText(texts["action_anthem"])
        self.actionAnnouncement.setText(texts["action_announcement"])
        self.actionTemplates.setText(texts["action_templates"])
        self.actionLog.setText(texts["action_log"])
        self.actionProfiles.setText(texts["action_profiles"])
        self.menuLanguage.setTitle(texts["menu_language"])
        self.actionLocaleRu.setText(texts["action_locale_ru"])
        self.actionLocaleEn.setText(texts["action_locale_en"])

        self.menuHelp.setTitle(texts["menu_help"])
        self.actionAbout.setText(texts["action_about"])
        self.actionToday.setText(texts["action_today"])

    def on_bells_toggled(self, state):
        self.bells_enabled = (state != 0)
        # Сохраняем состояние в настройки
        if "bells" not in self.config.preferences:
            self.config.preferences["bells"] = {}
        self.config.preferences["bells"]["enabled"] = self.bells_enabled
        self.config.save_preferences(self.config.preferences)
        if self.bells_enabled and (not self._get_sound_path("start") or not self._get_sound_path("end")):
            self._set_main_window_message(
                "missing_bell_sound",
                "Мелодия звонка не выбрана. Выберите звук в настройках.",
            )

    def on_music_toggled(self, state):
        self.music_enabled = (state != 0)
        music_settings = self.config.get_music_settings()
        music_settings["enabled"] = self.music_enabled
        self.config.preferences["music"] = music_settings
        self.config.save_preferences(self.config.preferences)
        if self.music_enabled:
            folders = music_settings.get("folders", [])
            if not folders or not self.music_player.set_music_folders(folders):
                self._set_main_window_message(
                    "missing_music_folder",
                    "Папка с музыкой не выбрана или не найдена.",
                )
            elif not self.music_player.get_audio_files():
                self._set_main_window_message(
                    "missing_music_tracks",
                    "В выбранной папке нет аудиофайлов.",
                )

    def on_anthem_toggled(self, state):
        self.anthem_enabled = (state != 0)
        anthem_settings = self.config.get_anthem_settings()
        anthem_settings["enabled"] = self.anthem_enabled
        self.config.preferences["anthem"] = anthem_settings
        self.config.save_preferences(self.config.preferences)
        if self.anthem_enabled:
            anthem_path = self._resolve_existing_file(anthem_settings.get("file", ""))
            if not anthem_path:
                self._set_main_window_message(
                    "missing_anthem_file",
                    "Файл гимна не выбран или не найден. Выберите файл в настройках.",
                )
        self.anthem_btn.setText(self._get_anthem_button_text())

    def on_announcement_toggled(self, state):
        self.announcement_enabled = (state != 0)
        
        # При включении сбрасываем played=False только для объявлений с датой >= сегодня
        # или для повторяющихся объявлений
        if self.announcement_enabled:
            today = datetime.date.today().isoformat()
            for index, ann in enumerate(self.config.get_announcements()):
                ann_date = ann.get("date", "")
                repeat_days = ann.get("repeat_days", [])
                
                # Для повторяющихся объявлений или объявлений с датой >= сегодня
                if repeat_days or (ann_date and ann_date >= today):
                    self.config.update_announcement(index, played=False, enabled=True)
        
        self.config.save_preferences(self.config.preferences)
        
        # Обновляем UI состояние
        self._update_announcement_ui_state()

    def _update_announcement_ui_state(self):
        """Обновляет состояние чекбокса и кнопки объявления."""
        # Проверяем наличие активных объявлений
        active_announcements = self.config.get_active_announcements()
        has_active = len(active_announcements) > 0
        
        # Устанавливаем флаг announcement_enabled если есть активные объявления
        self.announcement_enabled = has_active
        self.announcement_checkbox.setChecked(has_active)
        self.announcement_btn.setText(self._get_announcement_button_text())

    def manual_bell(self):
        path = self._get_sound_path("start")
        if path:
            # Останавливаем предыдущее воспроизведение перед запуском нового
            self.sound_player.stop_all()
            volumes = self.config.get_volumes()
            start_volume = volumes.get("start", 100)
            if self.sound_player.play(path, "start", volume=start_volume):
                self._clear_main_window_message()
                self.statusLabel.setText(f"🔔 {self.tr('btn_bell').replace('🔔', '').strip()}!")
                self.logger.log_event("bell", f"Manual start bell: {Path(path).name}")
        else:
            self._set_main_window_message(
                "missing_bell_sound",
                "Мелодия звонка не выбрана. Выберите звук в настройках.",
            )

    def manual_music(self):
        if self.sound_player.is_playing("announcement"):
            self._set_main_window_message(
                "announcement_playing",
                "Сейчас воспроизводится объявление. Музыка не будет запущена.",
            )
            return

        music_settings = self.config.get_music_settings()
        folders = music_settings.get("folders", [])
        if folders:
            if not self.music_player.set_music_folders(folders):
                self._set_main_window_message(
                    "missing_music_folder",
                    "Папка с музыкой не выбрана или не найдена.",
                )
                return
            # Останавливаем предыдущее воспроизведение перед запуском нового
            self.sound_player.stop_all()
            volumes = self.config.get_volumes()
            music_volume = volumes.get("music", 50)
            track = self.music_player.get_next_track()
            if track:
                # Помечаем трек как сыгранный для кэша, чтобы избежать повторного запуска в окне PLAYBACK_TRIGGER_WINDOW_SECONDS
                now = datetime.datetime.now()
                cache_key = self._event_cache_key("music", now)
                self.played_events[cache_key] = True
                
                self.sound_player.play_music(str(track), volume=music_volume)
                self._clear_main_window_message()
                self.music_player.mark_played()
                self.current_playing_track = str(track)
                self.statusLabel.setText(f"🎵 {self.tr('btn_music').replace('🎵', '').strip()}!")
                self.logger.log_event("music", "Manual music playback")
            else:
                self._set_main_window_message(
                    "missing_music_tracks",
                    "В выбранной папке нет аудиофайлов.",
                )
        else:
            self._set_main_window_message(
                "missing_music_folder",
                "Папка с музыкой не выбрана. Выберите папку в настройках.",
            )

    def manual_anthem(self):
        anthem_settings = self.config.get_anthem_settings()
        anthem_path = self._resolve_existing_file(anthem_settings.get("file", ""))
        if not anthem_path:
            self._set_main_window_message(
                "missing_anthem_file",
                "Файл гимна не выбран или не найден. Выберите файл в настройках.",
            )
            return

        self.sound_player.stop_all()
        anthem_volume = self.config.get_volume("anthem")
        if self.sound_player.play(str(anthem_path), "anthem", volume=anthem_volume):
            self._clear_main_window_message()
            self.statusLabel.setText(f"🎼 {self.tr('btn_anthem').replace('🎼', '').strip()}!")
            self.logger.log_event("anthem", f"Manual anthem: {anthem_path.name}")

    def check_anthem(self, now):
        """Проверяет, нужно ли автоматически запустить гимн."""
        if not self.anthem_enabled:
            return

        anthem_settings = self.config.get_anthem_settings()
        anthem_path = self._resolve_existing_file(anthem_settings.get("file", ""))
        day = anthem_settings.get("day", "")
        time_str = anthem_settings.get("time", "")

        if not anthem_path:
            self._set_main_window_message(
                "missing_anthem_file",
                "Файл гимна не выбран или не найден. Выберите файл в настройках.",
            )
            return
        if not day or not time_str:
            self._set_main_window_message(
                "missing_anthem_schedule",
                "День или время гимна не заданы. Проверьте настройки гимна.",
            )
            return

        today_key = WEEK_DAYS[now.weekday()]
        if today_key != day:
            return

        try:
            anthem_clock = self._parse_time(time_str)
            anthem_time = now.replace(
                hour=anthem_clock.hour,
                minute=anthem_clock.minute,
                second=anthem_clock.second,
                microsecond=0,
            )

            # Проверяем запуск в течение минуты, чтобы таймер GUI не пропускал событие.
            if self._is_time_to_play(now, anthem_time):
                self._play_cached_audio(
                    "anthem",
                    anthem_time,
                    anthem_path,
                    self.config.get_volume("anthem"),
                    status_text="🎼 Гимн!",
                    log_message=f"Anthem played: {anthem_path.name}",
                )
        except Exception as e:
            self.logger.log_event("error", f"Error checking anthem: {e}")

    def manual_announcement(self):
        """Открывает диалог выбора объявления для экстренного запуска."""
        announcements = self.config.get_announcements()
        
        # Фильтруем только активные объявления (enabled=True, played=False)
        active_announcements = []
        for idx, ann in enumerate(announcements):
            if ann.get("enabled", True) and not ann.get("played", False):
                active_announcements.append((idx, ann))
        
        if not active_announcements:
            self._set_main_window_message(
                "no_active_announcements",
                "Нет активных объявлений для запуска. Добавьте объявление в настройках.",
            )
            return
        
        # Если только одно активное объявление - запускаем его сразу
        if len(active_announcements) == 1:
            idx, ann = active_announcements[0]
            self._play_single_announcement(idx, ann)
            return
        
        # Если несколько объявлений - показываем диалог выбора
        dialog = AnnouncementSelectDialog(self, active_announcements)
        if dialog.exec() == QDialog.Accepted:
            selected_idx = dialog.get_selected_index()
            if selected_idx is not None:
                # Находим объявление по индексу
                for idx, ann in active_announcements:
                    if idx == selected_idx:
                        self._play_single_announcement(idx, ann)
                        break
    
    def _play_single_announcement(self, index, ann):
        """Запускает воспроизведение одного объявления."""
        announcement_path = self._resolve_existing_file(ann.get("file", ""))
        if not announcement_path:
            self._set_main_window_message(
                "missing_announcement_file",
                "Файл объявления не выбран или не найден. Выберите файл в настройках.",
            )
            return
        
        self.sound_player.stop_all()
        announcement_volume = self.config.get_volume("announcement")
        if self.sound_player.play(str(announcement_path), "announcement", volume=announcement_volume):
            self._clear_main_window_message()
            self.statusLabel.setText(
                f"📢 {self.tr('btn_announcement').replace('📢', '').strip()}!"
            )
            self.logger.log_event("announcement", f"Manual announcement: {announcement_path.name}")

    def check_announcement(self, now):
        """Проверяет, нужно ли автоматически запустить объявления (одноразовые и повторяющиеся)."""
        if not self.announcement_enabled:
            return

        for index, ann in enumerate(self.config.get_announcements()):
            if not ann.get("enabled", True):
                continue
            if ann.get("played", False):
                continue

            announcement_path = self._resolve_existing_file(ann.get("file", ""))
            date_str = ann.get("date", "")
            time_str = ann.get("time", "")
            repeat_days = ann.get("repeat_days", [])

            if not announcement_path:
                self._set_main_window_message(
                    "missing_announcement_file",
                    "Файл объявления не выбран или не найден. Выберите файл в настройках.",
                )
                continue
            if not time_str:
                self._set_main_window_message(
                    "missing_announcement_schedule",
                    "Время объявления не задано. Проверьте настройки объявления.",
                )
                continue

            # Проверяем день недели для повторяющихся объявлений
            today_key = WEEK_DAYS[now.weekday()]
            
            if repeat_days:
                # Повторяющееся объявление - проверяем день недели
                if today_key not in repeat_days:
                    continue
            elif date_str:
                # Одноразовое объявление - проверяем дату
                try:
                    announcement_date = datetime.date.fromisoformat(date_str)
                    if now.date() != announcement_date:
                        continue
                except ValueError:
                    continue
            else:
                # Нет ни repeat_days, ни даты - пропускаем
                continue

            try:
                announcement_clock = self._parse_time(time_str)
                announcement_time = now.replace(
                    hour=announcement_clock.hour,
                    minute=announcement_clock.minute,
                    second=announcement_clock.second,
                    microsecond=0,
                )

                if self._is_time_to_play(now, announcement_time) and self._play_cached_audio(
                    "announcement",
                    announcement_time,
                    announcement_path,
                    self.config.get_volume("announcement"),
                    status_text="📢 Объявление!",
                    log_message=f"Announcement played: {announcement_path.name}",
                ):
                    # Для одноразовых объявлений помечаем как сыгранное
                    if not repeat_days:
                        self.config.set_announcement_played_by_index(index, True)
                        self.config.save_preferences(self.config.preferences)
                    # Обновляем состояние чекбокса и кнопки
                    self._update_announcement_ui_state()
            except Exception as e:
                self.logger.log_event("error", f"Error checking announcement: {e}")

    def _get_announcement_button_text(self):
        """Возвращает текст кнопки объявления в зависимости от состояния."""
        btn_text = self.tr("btn_announcement").replace("📢", "").strip()
        if self.announcement_enabled:
            return "▶️ " + btn_text
        else:
            return "⏸️ " + btn_text

    def _get_anthem_button_text(self):
        """Возвращает текст кнопки гимна в зависимости от состояния"""
        btn_text = self.tr("btn_anthem").replace("🎼", "").strip()
        if self.anthem_enabled:
            return "▶️ " + btn_text
        else:
            return "⏸️ " + btn_text

    def _on_music_finished(self):
        """Вызывается когда музыка закончилась - очищает статус трека."""
        self.current_playing_track = None

    def manual_stop(self):
        """Остановка воспроизведения звонка, музыки, гимна и объявления"""
        self.sound_player.stop_all()
        self.current_playing_track = None
        self.statusLabel.setText(f"🛑 {self.tr('btn_stop').replace('🛑', '').strip()}!")
        self.logger.log_event("stop", "Playback stopped by user")

    def setup_tray_icon(self):
        """Настройка иконки в системном трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # Создаем иконку (используем стандартную)
        self.tray_icon = QSystemTrayIcon(self)

        # Используем эмодзи колокольчика как единую иконку трея.
        from PySide6.QtGui import QPixmap, QPainter
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setFont(QFont("Segoe UI Emoji" if platform.system() == "Windows" else "Noto Color Emoji", 42))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "🔔")
        painter.end()
        tray_icon = QIcon(pixmap)

        self.tray_icon.setIcon(tray_icon)
        self.tray_icon.setToolTip(self.tr("app_title"))

        # Создаем меню трея
        tray_menu = QMenu()

        show_act = QAction(self.tr("tray_show", "Показать"), self)
        show_act.triggered.connect(self.show_window)
        tray_menu.addAction(show_act)

        today_act = QAction(self.tr("tray_today", "Сегодня"), self)
        today_act.triggered.connect(self.set_today_schedule)
        tray_menu.addAction(today_act)

        tray_menu.addSeparator()

        exit_act = QAction(self.tr("tray_exit", "Выход"), self)
        exit_act.triggered.connect(self.quit_application)
        tray_menu.addAction(exit_act)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        """Обработчик активации иконки в трее"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        """Показать окно программы"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_application(self):
        """Корректный выход из приложения"""
        self.force_quit = True
        self.logger.log_event("info", "Application closed by user")
        self.config.save_preferences(self.config.preferences)
        QApplication.quit()

    def closeEvent(self, event):
        """При закрытии спрашиваем: оставить программу в трее или выйти."""
        if self.force_quit:
            self._cleanup_resources()
            event.accept()
            return

        if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
            title = self.tr("close_to_tray_title", "Закрыть программу?")
            text = self.tr("close_to_tray_text", "Оставить программу в трее, чтобы расписание продолжало работать?")
            stay_button_text = self.tr("close_to_tray_stay", "Остаться в трее")
            exit_button_text = self.tr("close_to_tray_exit", "Выйти")

            dialog = QMessageBox(self)
            dialog.setWindowTitle(title)
            dialog.setText(text)
            dialog.setIcon(QMessageBox.Question)
            stay_button = dialog.addButton(stay_button_text, QMessageBox.YesRole)
            exit_button = dialog.addButton(exit_button_text, QMessageBox.NoRole)
            cancel_button = dialog.addButton(self.tr("btn_cancel", "Отмена"), QMessageBox.RejectRole)
            dialog.setDefaultButton(stay_button)
            dialog.exec()

            clicked_button = dialog.clickedButton()
            if clicked_button == stay_button:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    self.tr("app_title"),
                    self.tr("minimized_to_tray", "Приложение свернуто в трей"),
                    QSystemTrayIcon.Information,
                    2000
                )
                self.logger.log_event("info", "Window minimized to tray")
            elif clicked_button == exit_button:
                self.force_quit = True
                self._cleanup_resources()
                self.logger.log_event("info", "Application closed from close dialog")
                event.accept()
            elif clicked_button == cancel_button:
                event.ignore()
            else:
                event.ignore()
            return

        title = self.tr("confirm_exit_title", "Подтверждение выхода")
        text = self.tr("confirm_exit_text", "Вы уверены, что хотите выйти из программы?")
        if QMessageBox.question(self, title, text, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            self.force_quit = True
            self._cleanup_resources()
            event.accept()
        else:
            event.ignore()

    def _cleanup_resources(self):
        """Корректно освобождает ресурсы Qt-объектов при закрытии приложения."""
        # Останавливаем все таймеры
        if hasattr(self, 'ui_timer'):
            self.ui_timer.stop()
        if hasattr(self, 'bell_timer'):
            self.bell_timer.stop()
        
        # Останавливаем воспроизведение и освобождаем ресурсы через cleanup()
        self.sound_player.cleanup()
        
        # Сохраняем настройки
        self.config.save_preferences(self.config.preferences)
        
        # Очищаем кэш событий
        self.played_events.clear()
        
        self.logger.log_event("info", "Resources cleaned up")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = SchoolBell()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

