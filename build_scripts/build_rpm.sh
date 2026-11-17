#!/usr/bin/env bash
# Build an RPM package from a clean source tree.
# Primary target: ALT Linux. The spec selects Fedora dependency names outside ALT.

source "$(dirname "$0")/build_common.sh"

VERSION="$(read_version)"
print_build_header "RPM"

require_command rpmbuild
require_command tar

BUILD_DIR="$BUILD_ROOT/rpm"
RPMBUILD_DIR="$BUILD_DIR/rpmbuild"
SOURCE_ROOT="$BUILD_DIR/source"
PKG_SRC="$SOURCE_ROOT/$APP_ID-$VERSION"
SPEC_FILE="$SCRIPT_DIR/school-bell.spec"
SOURCE_TAR="$RPMBUILD_DIR/SOURCES/$APP_ID-$VERSION.tar.gz"

rm -rf "$BUILD_DIR"
mkdir -p "$PKG_SRC" "$RPMBUILD_DIR"/{BUILD,BUILDROOT,RPMS,SOURCES,SPECS,SRPMS}

echo "[1/3] Preparing clean source tree..."
copy_app_files "$PKG_SRC"
write_desktop_entry "$PKG_SRC/$APP_ID.desktop"
install_square_icon "$PKG_SRC/$APP_ID.png"

# The source archive intentionally contains no preferences.yml, logs, music,
# tests or build artifacts.
tar -C "$SOURCE_ROOT" -czf "$SOURCE_TAR" "$APP_ID-$VERSION"

echo "[2/3] Running rpmbuild..."
rpmbuild -bb \
    --define "_topdir $RPMBUILD_DIR" \
    --define "app_version $VERSION" \
    "$SPEC_FILE"

RPM_FILE="$(find "$RPMBUILD_DIR/RPMS" -type f -name '*.rpm' -print -quit)"
[ -n "$RPM_FILE" ] || die "RPM не создан."

OUTPUT="$DIST_DIR/SchoolBell_${VERSION}_noarch.rpm"
cp -f "$RPM_FILE" "$OUTPUT"

echo "[3/3] Checking package contents..."
if command -v rpm >/dev/null 2>&1; then
    rpm -qlp "$OUTPUT" | grep -E '(^|/)(preferences\.yml|logs|music/|\.pyc$)' \
        && die "В RPM попали пользовательские или временные файлы."
fi

echo "Готово: $OUTPUT"
