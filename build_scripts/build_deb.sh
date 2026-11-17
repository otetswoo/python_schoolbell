#!/usr/bin/env bash
# Build a Debian package with system Python/PySide6 dependencies.
# The package contains no user settings, logs or music library.

source "$(dirname "$0")/build_common.sh"

VERSION="$(read_version)"
print_build_header "DEB"

require_command dpkg-deb
require_command fakeroot

BUILD_DIR="$BUILD_ROOT/deb"
PKG_ROOT="$BUILD_DIR/pkg"
DEBIAN_DIR="$PKG_ROOT/DEBIAN"
APP_DIR="$PKG_ROOT/usr/share/$APP_ID"
OUTPUT="$DIST_DIR/SchoolBell_${VERSION}_all.deb"

rm -rf "$BUILD_DIR"
mkdir -p "$APP_DIR" "$DEBIAN_DIR" \
    "$PKG_ROOT/usr/bin" \
    "$PKG_ROOT/usr/share/applications" \
    "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps" \
    "$PKG_ROOT/usr/share/doc/$APP_ID"

echo "[1/4] Copying application resources..."
copy_app_files "$APP_DIR"
write_launcher "$PKG_ROOT/usr/bin/$APP_ID" "/usr/share/$APP_ID"
write_desktop_entry "$PKG_ROOT/usr/share/applications/$APP_ID.desktop"
install_square_icon "$PKG_ROOT/usr/share/icons/hicolor/256x256/apps/$APP_ID.png"
cp "$PROJECT_ROOT/README.md" "$PKG_ROOT/usr/share/doc/$APP_ID/README.md"

echo "[2/4] Creating maintainer scripts..."
cat > "$DEBIAN_DIR/postinst" <<'EOF'
#!/bin/sh
set -e

if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

exit 0
EOF

cat > "$DEBIAN_DIR/postrm" <<'EOF'
#!/bin/sh
set -e

if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if [ -x /usr/bin/update-desktop-database ]; then
        update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
    fi
    if [ -x /usr/bin/gtk-update-icon-cache ]; then
        gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
    fi
fi

exit 0
EOF
chmod 755 "$DEBIAN_DIR/postinst" "$DEBIAN_DIR/postrm"

echo "[3/4] Creating DEBIAN/control..."
INSTALLED_SIZE="$(du -sk "$PKG_ROOT/usr" | cut -f1)"
cat > "$DEBIAN_DIR/control" <<EOF
Package: $APP_ID
Version: $VERSION
Section: education
Priority: optional
Architecture: all
Installed-Size: $INSTALLED_SIZE
Depends: python3, python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-pyside6.qtmultimedia, python3-yaml
Maintainer: $APP_MAINTAINER
Homepage: $APP_URL
Description: $APP_SUMMARY
 $APP_SUMMARY_RU
 .
 Features: automatic bells, break music, anthem, announcements,
 editable schedule, holiday mode and Russian/English localization.
EOF

# Normal permissions: data files are read-only, directories are traversable.
find "$PKG_ROOT/usr" -type d -exec chmod 755 {} \;
find "$PKG_ROOT/usr" -type f -exec chmod 644 {} \;
chmod 755 "$PKG_ROOT/usr/bin/$APP_ID"

echo "[4/4] Building package..."
rm -f "$OUTPUT"
fakeroot dpkg-deb --build "$PKG_ROOT" "$OUTPUT"

[ -f "$OUTPUT" ] || die "DEB не создан: $OUTPUT"
echo "Готово: $OUTPUT"
