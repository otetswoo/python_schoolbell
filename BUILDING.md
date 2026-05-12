# 📦 Building Installers / Сборка установщиков

This guide explains how to build DEB (Linux) and MSI (Windows) installers for School Bell.

Это руководство объясняет, как создать установщики DEB (Linux) и MSI (Windows) для School Bell.

---

## 🐧 Building DEB Package (Linux - Debian/Ubuntu)

### Prerequisites / Требования

```bash
# Install required tools
sudo apt-get update
sudo apt-get install -y dpkg-dev fakeroot
```

### Build Steps / Шаги сборки

1. **Navigate to project root:**
   ```bash
   cd /path/to/school_bell
   ```

2. **Run the build script:**
   ```bash
   bash build_scripts/build_deb.sh [version]
   ```
   
   Example:
   ```bash
   bash build_scripts/build_deb.sh 1.0.0
   ```

3. **Install the package:**
   ```bash
   sudo dpkg -i build/deb/school-bell_1.0.0_all.deb
   sudo apt-get install -f  # Fix dependencies if needed
   ```

### Uninstall / Удаление

```bash
sudo apt remove school-bell
```

### What's Included / Что включено

- Application files in `/opt/school-bell/`
- Desktop entry for applications menu
- Command-line launcher (`school-bell`)
- Automatic dependency resolution for Python 3, PySide6, and PyYAML

---

## 🪟 Building MSI Package (Windows)

### Prerequisites / Требования

1. **Python 3.8+** installed
2. **Install cx_Freeze:**
   ```cmd
   pip install cx-Freeze
   ```

### Build Steps / Шаги сборки

1. **Navigate to project root:**
   ```cmd
   cd C:\path\to\school_bell
   ```

2. **Build the MSI:**
   ```cmd
   python build_scripts\build_msi.py bdist_msi
   ```

3. **Find the installer:**
   The MSI file will be created in the `dist\` directory.

### Alternative: Build EXE only / Альтернатива: только EXE

```cmd
python build_scripts\build_msi.py build_exe
```

### Customization / Настройка

Edit `build_scripts/build_msi.py` to:
- Change application icon (add `.ico` file)
- Modify included files
- Adjust package metadata

---

## 📝 Notes / Примечания

### For DEB Package:
- The package installs to `/opt/school-bell/`
- A symlink is created at `/usr/bin/school-bell`
- Desktop entry appears in the applications menu
- Dependencies are automatically handled by apt

### For MSI Package:
- Requires Windows environment
- cx_Freeze bundles Python interpreter with the app
- Creates desktop shortcut automatically
- All dependencies are included in the installer

---

## 🔧 Troubleshooting / Решение проблем

### DEB Build Fails
```bash
# Ensure you have proper permissions
chmod +x build_scripts/build_deb.sh

# Check if fakeroot is installed
which fakeroot
```

### MSI Build Fails
```cmd
# Reinstall cx_Freeze
pip uninstall cx-Freeze
pip install cx-Freeze

# Clean previous builds
rmdir /s /q build dist
```

### Missing Dependencies
- **Linux:** `sudo apt-get install python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets python3-yaml`
- **Windows:** Already bundled by cx_Freeze

---

## 📄 License / Лицензия

MIT License
