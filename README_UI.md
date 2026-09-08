# Настройка интерфейса через Qt Designer

## Что такое Qt Designer?

**Qt Designer** — это визуальный редактор интерфейсов для приложений на базе Qt. Он позволяет создавать и изменять интерфейс программы **без написания кода**, просто перетаскивая элементы мышкой.

## Как использовать в вашем проекте

### 1. Запуск Qt Designer

```bash
pyside6-designer src/gui/main_window.ui
```

### 2. Что можно делать в Qt Designer

- **Перемещение элементов**: Просто перетащите кнопку, таблицу или другой элемент в нужное место
- **Изменение размера**: Выделите элемент и потяните за края, чтобы изменить размер
- **Настройка свойств**: В правой панели "Property Editor" можно изменить:
  - `minimumWidth` / `maximumWidth` — минимальная/максимальная ширина
  - `minimumHeight` / `maximumHeight` — минимальная/максимальная высота
  - `geometry` — положение и размер (x, y, width, height)
  - `styleSheet` — CSS-стили (цвет, шрифт, границы)
  - `toolTip` — всплывающая подсказка
  - `text` — текст на кнопке или метке

### 3. Структура текущего интерфейса

```
MainWindow
└── centralwidget
    └── mainLayout (QVBoxLayout)
        ├── daysContainer (QWidget) — кнопки дней недели
        │   └── daysLayout (QHBoxLayout)
        ├── contentLayout (QHBoxLayout)
        │   ├── controlsFrame (QFrame) — левая панель
        │   │   └── controlsLayout (QVBoxLayout)
        │   │       ├── editBtn
        │   │       ├── todayBtn
        │   │       └── controlsSpacer
        │   └── scheduleTable (QTableWidget)
        ├── volumeGroup (QGroupBox) — настройки громкости
        │   └── volumeLayout (QHBoxLayout)
        ├── buttonsFrame (QFrame) — кнопки управления
        │   └── bottomLayout (QHBoxLayout)
        │       ├── bellBtn
        │       ├── musicBtn
        │       ├── anthemBtn
        │       ├── announcementBtn
        │       └── stopBtn
        ├── trackLabel (QLabel) — текущий трек
        └── statusLabel (QLabel) — строка статуса
```

### 4. Применение изменений

После редактирования `.ui` файла нужно перегенерировать Python-код:

```bash
pyside6-uic src/gui/main_window.ui -o src/gui/ui_main_window.py
```

Затем запустите программу — изменения применятся автоматически.

### 5. Автоматизация (опционально)

Чтобы не запускать команду вручную, можно добавить в начало `school_bell.py`:

```python
# Автоматическая компиляция .ui файла при запуске
import subprocess
from pathlib import Path

ui_file = Path(__file__).parent / "src/gui/main_window.ui"
py_file = Path(__file__).parent / "src/gui/ui_main_window.py"

if ui_file.exists() and (not py_file.exists() or ui_file.stat().st_mtime > py_file.stat().st_mtime):
    subprocess.run(["pyside6-uic", str(ui_file), "-o", str(py_file)])
```

## Примеры изменений

### Изменить размер окна
В Qt Designer выделите `MainWindow` → Property Editor → `geometry` → измените `width` и `height`.

### Изменить цвет кнопки
Выделите кнопку → Property Editor → `styleSheet` → добавьте:
```css
background-color: #4CAF50; color: white;
```

### Изменить отступы
Выделите layout → Property Editor → `leftMargin`, `topMargin`, `rightMargin`, `bottomMargin`.

### Добавить новый элемент
1. В палитре виджетов слева выберите нужный элемент (QPushButton, QLabel, etc.)
2. Перетащите его в нужное место
3. Настройте свойства в правой панели

## Важные заметки

- **Не изменяйте имена объектов** (objectName), так как код ссылается на них по имени
- Кнопки дней недели создаются программно и добавляются в `daysLayout`
- Элементы управления громкостью также создаются программно и добавляются в `volumeLayout`
