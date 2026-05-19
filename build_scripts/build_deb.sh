#!/bin/bash
# Build script for creating DEB package on Linux (Debian/Ubuntu)
# This script creates a proper Debian package structure and builds the .deb file

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 School Bell - DEB Package Builder${NC}"
echo "=========================================="

# Configuration
APP_NAME="school-bell"
VERSION=${1:-"1.0.0"}
MAINTAINER="otetswoo"
DESCRIPTION="School Bell Automation System / Автоматизация школьных звонков"
ARCH="all"

# Directories
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$ROOT_DIR")"
BUILD_DIR="$PROJECT_ROOT/build/deb"
DEBIAN_DIR="$BUILD_DIR/DEBIAN"
OPT_DIR="$BUILD_DIR/opt/$APP_NAME"
USR_DIR="$BUILD_DIR/usr"

# Clean previous build
echo -e "${YELLOW}🧹 Cleaning previous build...${NC}"
rm -rf "$BUILD_DIR"
mkdir -p "$DEBIAN_DIR"
mkdir -p "$OPT_DIR"
mkdir -p "$USR_DIR/share/applications"
mkdir -p "$USR_DIR/share/icons/hicolor/256x256/apps"

# Copy application files
echo -e "${YELLOW}📁 Copying application files...${NC}"
cp -r "$PROJECT_ROOT/school_bell.py" "$OPT_DIR/"
cp -r "$PROJECT_ROOT/src" "$OPT_DIR/"
cp -r "$PROJECT_ROOT/sounds" "$OPT_DIR/"
mkdir -p "$OPT_DIR/logs"
cp "$PROJECT_ROOT/schedule.yml" "$OPT_DIR/"
cp "$PROJECT_ROOT/preferences.yml" "$OPT_DIR/"
cp "$PROJECT_ROOT/README.md" "$OPT_DIR/"

# Copy icon
echo -e "${YELLOW}🎨 Copying application icon...${NC}"
cp "$PROJECT_ROOT/src/school_bell.png" "$USR_DIR/share/icons/hicolor/256x256/apps/$APP_NAME.png"

# Create control file
echo -e "${YELLOW}📝 Creating control file...${NC}"
cat > "$DEBIAN_DIR/control" << EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3, python3-pyside6.qtcore, python3-pyside6.qtgui, python3-pyside6.qtwidgets, python3-pyside6.qtmultimedia, python3-yaml
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 School Bell is an automation system for school bells with flexible scheduling and music during breaks.
 Features:
  - Automatic bells for lesson start/end
  - Music playback during breaks
  - Flexible schedule editor
  - Russian and English localization
EOF

# Create preinst script
cat > "$DEBIAN_DIR/preinst" << 'EOF'
#!/bin/bash
set -e
echo "Preparing installation..."
exit 0
EOF
chmod 755 "$DEBIAN_DIR/preinst"

# Create postinst script
echo -e "${YELLOW}🔧 Creating post-installation script...${NC}"
cat > "$DEBIAN_DIR/postinst" << EOF
#!/bin/bash
set -e

echo "Setting up School Bell..."

# Create symlink in /usr/bin
ln -sf /opt/$APP_NAME/school_bell.py /usr/bin/$APP_NAME
chmod +x /usr/bin/$APP_NAME

# Create logs directory with proper permissions
mkdir -p /opt/$APP_NAME/logs
chmod 755 /opt/$APP_NAME/logs

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

echo "Installation complete!"
echo "You can now run '$APP_NAME' from the applications menu or terminal."
exit 0
EOF
chmod 755 "$DEBIAN_DIR/postinst"

# Create postrm script
cat > "$DEBIAN_DIR/postrm" << EOF
#!/bin/bash
set -e

if [ "\$1" = "remove" ] || [ "\$1" = "purge" ]; then
    echo "Removing School Bell..."
    
    # Remove symlink
    rm -f /usr/bin/$APP_NAME
    
    # Update desktop database
    if [ -x /usr/bin/update-desktop-database ]; then
        update-desktop-database /usr/share/applications 2>/dev/null || true
    fi
    
    echo "Uninstallation complete!"
fi
exit 0
EOF
chmod 755 "$DEBIAN_DIR/postrm"

# Create desktop file
echo -e "${YELLOW}🖥️  Creating desktop entry...${NC}"
cat > "$USR_DIR/share/applications/$APP_NAME.desktop" << EOF
[Desktop Entry]
Name=School Bell
Name[ru]=Школьные звонки
Comment=School Bell Automation System
Comment[ru]=Автоматизация школьных звонков
Exec=/opt/$APP_NAME/launch.sh
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;Education;
Keywords=school;bell;schedule;automation;
Keywords[ru]=школа;звонок;расписание;автоматизация;
EOF

# Create launcher script
echo -e "${YELLOW}🚀 Creating launcher script...${NC}"
cat > "$OPT_DIR/launch.sh" << 'EOF'
#!/bin/bash
# School Bell Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python dependencies
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "❌ PySide6 not found. Installing dependencies..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user PySide6 pyyaml
    else
        echo "Please install PySide6 and pyyaml:"
        echo "  pip3 install PySide6 pyyaml"
        exit 1
    fi
fi

exec python3 "$SCRIPT_DIR/school_bell.py" "$@"
EOF
chmod +x "$OPT_DIR/launch.sh"

# Calculate installed size
INSTALLED_SIZE=$(du -sk "$OPT_DIR" | cut -f1)
echo -e "${YELLOW}📊 Installed size: ${INSTALLED_SIZE} KB${NC}"

# Update control file with installed size
sed -i "s/^Architecture: all/Architecture: all\nInstalled-Size: ${INSTALLED_SIZE}/" "$DEBIAN_DIR/control"

# Set proper ownership (important for deb packages)
echo -e "${YELLOW}⚙️  Setting permissions...${NC}"
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
chmod 755 "$DEBIAN_DIR"/*
chmod +x "$OPT_DIR/school_bell.py"
chmod 755 "$OPT_DIR/logs"

# Build the package
echo -e "${YELLOW}📦 Building DEB package...${NC}"
cd "$BUILD_DIR"

# Update desktop database for icon cache
if [ -f "$USR_DIR/share/icons/hicolor/256x256/apps/$APP_NAME.png" ]; then
    echo -e "${GREEN}✓ Icon installed successfully${NC}"
fi

fakeroot dpkg-deb --build . "../${APP_NAME}_${VERSION}_${ARCH}.deb"

echo -e "${GREEN}✅ Build complete!${NC}"
echo "Package: $BUILD_DIR/../${APP_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo -e "${YELLOW}To install:${NC}"
echo "  sudo dpkg -i ${APP_NAME}_${VERSION}_${ARCH}.deb"
echo "  sudo apt-get install -f  # Fix dependencies if needed"
echo ""
echo -e "${YELLOW}To uninstall:${NC}"
echo "  sudo apt remove $APP_NAME"
