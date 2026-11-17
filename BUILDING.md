# Сборка School Bell для Linux

Версия приложения берётся из `src/config.py` (`VERSION`). Все Linux-пакеты
собираются в `dist/` и не содержат пользовательских настроек, журналов,
музыки и других локальных файлов.

```
dist/
├── SchoolBell_<version>_all.deb
├── SchoolBell_<version>_noarch.rpm
└── SchoolBell_<version>_x86_64.AppImage
```

Общие функции находятся в `build_scripts/build_common.sh`: определение версии,
копирование только ресурсов приложения, создание `.desktop` и установка значка.
Скрипты можно запускать из любого каталога; они сами находят корень проекта.

## Пользовательские данные

Пакеты не содержат `preferences.yml`, `logs/`, `music/` и не изменяют
пользовательские настройки при установке или обновлении. Установленная
программа хранит данные в:

```
$XDG_DATA_HOME/school-bell/   (если XDG_DATA_HOME задан)
~/.local/share/school-bell/  (по умолчанию)
```

Внутри создаются `preferences.yml`, `schedule.yml`, `music/` и `logs/`.
Звуки и расписание по умолчанию остаются в read-only каталоге приложения.

## 1. DEB (Debian/Ubuntu)

### Инструменты сборки

```bash
sudo apt-get update
sudo apt-get install -y dpkg-dev fakeroot desktop-file-utils
```

Для проверки пакета полезны `lintian` и чистая виртуальная машина Debian/Ubuntu.

### Сборка

```bash
cd /path/to/school_bell
bash build_scripts/build_deb.sh
```

Результат: `dist/SchoolBell_<version>_all.deb`.

Пакет устанавливается в `/usr/share/school-bell`, launcher — в
`/usr/bin/school-bell`, desktop-файл и значок — в стандартные каталоги
`/usr/share`.

### Зависимости Debian

`python3`, `python3-pyside6.qtcore`, `python3-pyside6.qtgui`,
`python3-pyside6.qtwidgets`, `python3-pyside6.qtmultimedia`, `python3-yaml`.

### Проверка

```bash
dpkg-deb -I dist/SchoolBell_<version>_all.deb
dpkg-deb -c dist/SchoolBell_<version>_all.deb
sudo dpkg -i dist/SchoolBell_<version>_all.deb
sudo apt-get install -f
school-bell
```

Удаление: `sudo apt remove school-bell`. Пользовательские данные в
`~/.local/share/school-bell` при удалении не стираются.

## 2. RPM (ALT Linux)

### Инструменты сборки

В ALT Linux:

```bash
sudo apt-get install -y rpm-build
```

`rpmbuild` должен быть доступен в `PATH`. Сборка выполняется от обычного
пользователя; root не требуется.

### Сборка

```bash
cd /path/to/school_bell
bash build_scripts/build_rpm.sh
```

Скрипт создаёт чистый tar-архив без `preferences.yml`, `logs/`, `music/`,
`build/` и `.git`, затем запускает `rpmbuild`. Результат:
`dist/SchoolBell_<version>_noarch.rpm`.

### Зависимости ALT Linux

- `python3`
- `python3-module-pyside6` — включает Python-модуль Qt Multimedia и подтягивает
  системные библиотеки Qt 6.
- `python3-module-yaml`

Для сборки на Fedora/RHEL spec автоматически использует другие имена:
`python3-pyside6` и `python3-pyyaml`. Это не гарантирует идентичный набор
Qt-плагинов; для Fedora пакет нужно отдельно проверить.

### Проверка

```bash
rpm -qip dist/SchoolBell_<version>_noarch.rpm
rpm -qlp dist/SchoolBell_<version>_noarch.rpm
sudo rpm -i dist/SchoolBell_<version>_noarch.rpm
school-bell
```

Удаление: `sudo rpm -e school-bell`. Пользовательские настройки не входят
в RPM и при удалении пакета не затрагиваются.

## 3. AppImage

AppImage собирается через PyInstaller в режиме `onedir`. Внутрь попадают
Python runtime, PySide6, Qt-библиотеки, Qt-плагины (включая
`plugins/multimedia` и `plugins/platforms`), звуки, расписание и значок.

### Инструменты сборки

```bash
python3 -m pip install --user pyinstaller
```

Дополнительно нужен `appimagetool` в `PATH` либо путь в переменной
`APPIMAGETOOL`. `desktop-file-validate` и ImageMagick желательны, но не
обязательны.

### Сборка

```bash
cd /path/to/school_bell
bash build_scripts/build_appimage.sh
```

Результат: `dist/SchoolBell_<version>_x86_64.AppImage`.

Если `appimagetool` не найден, скрипт остановится с ошибкой, но оставит
готовый AppDir в `build/appimage/AppDir`. Это позволяет проверить упаковку
до установки дополнительного инструмента.

### Проверка

```bash
chmod +x dist/SchoolBell_<version>_x86_64.AppImage
./dist/SchoolBell_<version>_x86_64.AppImage
```

Запуск должен работать из любого каталога, без установки и без root.
AppImage использует пользовательский каталог данных, а не записывает
настройки внутрь смонтированного образа.

### Ограничения AppImage

- AppImage не является универсально совместимым с любой glibc. Собирайте его
  в среде с достаточно старой glibc (например, в контейнере со старым
  Debian/Ubuntu), иначе на старых дистрибутивах возможна ошибка загрузки.
- FUSE не всегда доступен. Для проверки без FUSE можно распаковать образ
  (`--appimage-extract`) или использовать `APPIMAGE_EXTRACT_AND_RUN=1`.
- Qt Multimedia использует системные FFmpeg/GStreamer-библиотеки, собранные
  PyInstaller в bundle. Проверяйте воспроизведение на целевой системе.
- Wayland/X11-плагины и темы оформления зависят от окружения; базовые
  `platforms/libqxcb.so` и `libqwayland.so` включены.

## Общие проверки

```bash
python3 -m compileall -q school_bell.py src tests
python3 -m unittest discover -s tests -v
desktop-file-validate build/appimage/AppDir/school-bell.desktop
```

Проверяйте, что в пакетах нет пользовательских файлов:

```bash
dpkg-deb -c dist/SchoolBell_<version>_all.deb | grep -E 'preferences|logs|/music/'
rpm -qlp dist/SchoolBell_<version>_noarch.rpm | grep -E 'preferences|logs|/music/'
```

Обе команды не должны находить совпадений.

## Windows

Существующие Windows-скрипты (`build_msi.bat`, `build_exe.bat`,
`build_msi.py`) не входят в задачу Linux-сборки. Для Windows по-прежнему
требуются Windows, PyInstaller/cx_Freeze и WiX/Inno Setup.
