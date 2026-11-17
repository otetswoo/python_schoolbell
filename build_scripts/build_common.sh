#!/usr/bin/env bash
# Shared helpers for Linux package builds (DEB, RPM source, AppImage).
# This file is sourced by build scripts; it is not invoked directly.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_ROOT="$PROJECT_ROOT/build"
DIST_DIR="$PROJECT_ROOT/dist"

APP_ID="school-bell"
APP_NAME="School Bell"
APP_NAME_RU="Школьные звонки"
APP_MAINTAINER="otetswoo"
APP_SUMMARY="School bell automation with schedule, break music, anthem and announcements"
APP_SUMMARY_RU="Автоматизация школьных звонков: расписание, музыка на переменах, гимн и объявления"
APP_URL="https://github.com/otetswoo/python_schoolbell"

mkdir -p "$BUILD_ROOT" "$DIST_DIR"

die() {
    echo "ERROR: $*" >&2
    exit 1
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "Не найден инструмент '$1'. Установите его и повторите сборку."
}

read_version() {
    local version
    version="$(sed -n 's/^VERSION[[:space:]]*=[[:space:]]*"\([^"]*\)".*/\1/p' \
        "$PROJECT_ROOT/src/config.py" | head -n 1)"
    [ -n "$version" ] || die "Не удалось прочитать VERSION из src/config.py"
    printf '%s\n' "$version"
}

# Copies only read-only application resources. Never copies preferences,
# logs, music, tests, build artifacts or the local git metadata.
copy_app_files() {
    local dest="$1"
    mkdir -p "$dest"
    tar -C "$PROJECT_ROOT" \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.pyo' \
        -cf - \
        school_bell.py src sounds schedule.yml README.md \
        | tar -C "$dest" -xf -
}

install_square_icon() {
    local dest="$1"
    local source="$PROJECT_ROOT/src/school_bell.png"
    mkdir -p "$(dirname "$dest")"
    [ -f "$source" ] || die "Не найден исходный значок: $source"

    # Необязательное приведение к квадрату 256x256, если доступен ImageMagick.
    if command -v magick >/dev/null 2>&1; then
        magick "$source" -resize 256x256 -background none -gravity center \
            -extent 256x256 "$dest"
    elif command -v convert >/dev/null 2>&1; then
        convert "$source" -resize 256x256 -background none -gravity center \
            -extent 256x256 "$dest" 2>/dev/null
    else
        cp "$source" "$dest"
    fi
}

write_desktop_entry() {
    local dest="$1"
    mkdir -p "$(dirname "$dest")"
    cat > "$dest" <<EOF
[Desktop Entry]
Type=Application
Name=$APP_NAME
Name[ru]=$APP_NAME_RU
Comment=$APP_SUMMARY
Comment[ru]=$APP_SUMMARY_RU
Exec=$APP_ID
Icon=$APP_ID
Terminal=false
Categories=Education;
Keywords=school;bell;schedule;automation;
Keywords[ru]=школа;звонок;расписание;автоматизация;
StartupWMClass=$APP_ID
EOF
}

write_launcher() {
    local dest="$1"
    local app_dir="$2"
    mkdir -p "$(dirname "$dest")"
    cat > "$dest" <<EOF
#!/bin/sh
exec python3 "$app_dir/school_bell.py" "\$@"
EOF
    chmod 755 "$dest"
}

print_build_header() {
    local format="$1"
    echo "=========================================="
    echo " School Bell — $format build"
    echo " Version: $VERSION"
    echo " Project: $PROJECT_ROOT"
    echo "=========================================="
}
