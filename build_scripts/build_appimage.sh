#!/usr/bin/env bash
# Build a self-contained AppImage using PyInstaller onedir + appimagetool.
# No system Python/PySide6 is required on the target machine.

source "$(dirname "$0")/build_common.sh"

VERSION="$(read_version)"
print_build_header "AppImage"

require_command pyinstaller

BUILD_DIR="$BUILD_ROOT/appimage"
PYI_DIST="$BUILD_DIR/pyinstaller-dist"
PYI_WORK="$BUILD_DIR/pyinstaller-work"
APPDIR="$BUILD_DIR/AppDir"
OUTPUT="$DIST_DIR/SchoolBell_${VERSION}_x86_64.AppImage"

rm -rf "$BUILD_DIR"
mkdir -p "$PYI_DIST" "$PYI_WORK" "$APPDIR"

echo "[1/4] Building PyInstaller onedir bundle..."
pyinstaller --clean --noconfirm \
    --distpath "$PYI_DIST" \
    --workpath "$PYI_WORK" \
    "$PROJECT_ROOT/school_bell.spec"

PYI_APP="$PYI_DIST/school-bell"
[ -x "$PYI_APP/school-bell" ] || die "PyInstaller не создал исполняемый файл."

echo "[2/4] Creating AppDir..."
mkdir -p "$APPDIR/usr/bin"
cp -a "$PYI_APP/." "$APPDIR/usr/bin/"
mkdir -p \
    "$APPDIR/usr/share/applications" \
    "$APPDIR/usr/share/icons/hicolor/256x256/apps"

write_desktop_entry "$APPDIR/usr/share/applications/$APP_ID.desktop"
install_square_icon "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"

# appimagetool expects the desktop file and icon at the AppDir root as well.
cp "$APPDIR/usr/share/applications/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
cp "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_ID.png" "$APPDIR/$APP_ID.png"
ln -sf "$APP_ID.png" "$APPDIR/.DirIcon"

cat > "$APPDIR/AppRun" <<'EOF'
#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
unset PYTHONHOME PYTHONPATH

QT_PLUGINS="$HERE/usr/bin/_internal/PySide6/Qt/plugins"
if [ -d "$QT_PLUGINS" ]; then
    export QT_PLUGIN_PATH="$QT_PLUGINS${QT_PLUGIN_PATH:+:$QT_PLUGIN_PATH}"
fi

export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/school-bell" "$@"
EOF
chmod 755 "$APPDIR/AppRun"

echo "[3/4] Validating desktop entry..."
if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$APPDIR/$APP_ID.desktop"
else
    echo "WARNING: desktop-file-validate не найден, проверка пропущена."
fi

echo "[4/4] Building AppImage..."
APPIMAGETOOL="${APPIMAGETOOL:-}"
if [ -z "$APPIMAGETOOL" ]; then
    if command -v appimagetool >/dev/null 2>&1; then
        APPIMAGETOOL="appimagetool"
    elif [ -x "$PROJECT_ROOT/tools/appimagetool" ]; then
        APPIMAGETOOL="$PROJECT_ROOT/tools/appimagetool"
    else
        die "appimagetool не найден. AppDir подготовлен: $APPDIR. Установите appimagetool или укажите APPIMAGETOOL=/path/to/appimagetool."
    fi
fi

ARCH=x86_64 "$APPIMAGETOOL" --no-appstream "$APPDIR" "$OUTPUT"

[ -f "$OUTPUT" ] || die "AppImage не создан: $OUTPUT"
chmod 755 "$OUTPUT"
echo "Готово: $OUTPUT"
