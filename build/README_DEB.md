# School Bell - DEB Package

Пакет `.deb` успешно собран и готов к установке.

## Расположение пакета

```
/workspace/build/school-bell_1.0.0_all.deb
```

## Информация о пакете

- **Название**: school-bell
- **Версия**: 1.0.0
- **Архитектура**: all (универсальный)
- **Размер**: ~162 KB
- **Установленный размер**: ~540 KB
- **Зависимости**: 
  - python3
  - python3-pyside6.qtcore
  - python3-pyside6.qtgui
  - python3-pyside6.qtwidgets
  - python3-yaml

## Структура пакета

```
/opt/school-bell/           # Основная директория приложения
├── school_bell.py          # Главный скрипт
├── src/                    # Исходный код
├── sounds/                 # Звуковые файлы
├── logs/                   # Директория для логов
├── schedule.yml            # Файл расписания
├── preferences.yml         # Файл настроек
└── launch.sh               # Скрипт запуска

/usr/share/applications/    # Desktop-файл для меню приложений
└── school-bell.desktop

/usr/share/icons/           # Иконка приложения
└── hicolor/256x256/apps/school-bell.png

/usr/bin/school-bell        # Символическая ссылка (создается при установке)
```

## Установка

```bash
sudo dpkg -i /workspace/build/school-bell_1.0.0_all.deb
sudo apt-get install -f  # Если нужно установить зависимости
```

## Запуск

После установки приложение можно запустить:

1. Через меню приложений (категория "Utility" или "Education")
2. Из терминала: `school-bell`
3. Прямой запуск: `/opt/school-bell/school_bell.py`

## Удаление

```bash
sudo apt remove school-bell
```

## Сборка новой версии

Для сборки пакета с другой версией:

```bash
cd /workspace
bash build_scripts/build_deb.sh <версия>
# Пример:
bash build_scripts/build_deb.sh 1.0.1
```

## Примечания

- Пакет создает директорию `/opt/school-bell/logs/` для файлов логов
- Desktop-файл поддерживает русский и английский языки
- Иконка устанавливается в стандартную директорию Hicolor
