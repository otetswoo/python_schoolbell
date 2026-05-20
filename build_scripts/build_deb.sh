#!/bin/bash
# Build script for creating DEB package on Linux (Debian/Ubuntu)
# This script creates a proper Debian package structure and builds the .deb file
# Uses system Python packages - no PyInstaller needed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}📦 School Bell - DEB Package Builder${NC}"
echo "=========================================="

# Get project root directory (parent of build_scripts)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check for required tools
check_requirements() {
    local missing=0
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ python3 is not installed${NC}"
        missing=1
    fi
    
    if ! command -v dpkg-deb &> /dev/null; then
        echo -e "${RED}❌ dpkg-deb is not installed${NC}"
        missing=1
    fi
    
    if ! command -v fakeroot &> /dev/null; then
        echo -e "${RED}❌ fakeroot is not installed. Install with: sudo apt install fakeroot${NC}"
        missing=1
    fi
    
    if [ $missing -eq 1 ]; then
        echo -e "${RED}❌ Missing required tools. Please install them and try again.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All requirements met${NC}"
}

check_requirements

# Get version from src/config.py
VERSION=$(grep -E '^VERSION\s*=' "$PROJECT_ROOT/src/config.py" | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
if [ -z "$VERSION" ]; then
    VERSION="1.0.0"
fi
echo -e "${YELLOW}📋 Version: ${VERSION}${NC}"

# Configuration
APP_NAME="school-bell"
MAINTAINER="otetswoo"
DESCRIPTION="School Bell Automation System / Автоматизация школьных звонков"
ARCH="all"

# Directories
BUILD_DIR="$PROJECT_ROOT/build/deb"
DEBIAN_DIR="$BUILD_DIR/DEBIAN"
USR_DIR="$BUILD_DIR/usr"
LIB_DIR="$BUILD_DIR/usr/lib/school-bell"

# Clean previous build
echo -e "${YELLOW}🧹 Cleaning previous build...${NC}"
rm -rf "$BUILD_DIR"

# Create directories
mkdir -p "$DEBIAN_DIR"
mkdir -p "$LIB_DIR"
mkdir -p "$USR_DIR/share/applications"
mkdir -p "$USR_DIR/share/icons/hicolor/256x256/apps"
mkdir -p "$USR_DIR/bin"

# Copy source files to lib directory
echo -e "${YELLOW}📁 Copying application files...${NC}"
cp "$PROJECT_ROOT/school_bell.py" "$LIB_DIR/"
cp -r "$PROJECT_ROOT/src" "$LIB_DIR/"
cp -r "$PROJECT_ROOT/sounds" "$LIB_DIR/"
cp "$PROJECT_ROOT/schedule.yml" "$LIB_DIR/"
cp "$PROJECT_ROOT/preferences.yml" "$LIB_DIR/"

# Create launcher script in /usr/bin
echo -e "${YELLOW}🚀 Creating launcher script...${NC}"
cat > "$USR_DIR/bin/school-bell" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/school-bell/school_bell.py "$@"
EOF
chmod 755 "$USR_DIR/bin/school-bell"

# Copy icon
echo -e "${YELLOW}🎨 Copying application icon...${NC}"
if [ -f "$PROJECT_ROOT/src/school_bell.png" ]; then
    cp "$PROJECT_ROOT/src/school_bell.png" "$USR_DIR/share/icons/hicolor/256x256/apps/$APP_NAME.png"
fi

# Create control file
echo -e "${YELLOW}📝 Creating control file...${NC}"
cat > "$DEBIAN_DIR/control" << EOF
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Depends: python3,
         python3-pyside6.qtcore,
         python3-pyside6.qtgui,
         python3-pyside6.qtwidgets,
         python3-pyside6.qtmultimedia,
         python3-yaml
Maintainer: $MAINTAINER
Description: $DESCRIPTION
 School Bell is an automation system for school bells with flexible scheduling and music during breaks.
 Features:
  - Automatic bells for lesson start/end
  - Music playback during breaks
  - Flexible schedule editor
  - Russian and English localization
EOF

# Create postinst script
echo -e "${YELLOW}🔧 Creating post-installation script...${NC}"
cat > "$DEBIAN_DIR/postinst" << EOF
#!/bin/bash
set -e

echo "Setting up School Bell..."

# Create data directory for user data
mkdir -p /var/lib/school-bell
chmod 755 /var/lib/school-bell

# Update desktop database
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications 2>/dev/null || true
fi

# Update icon cache
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
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
    
    # Update desktop database
    if [ -x /usr/bin/update-desktop-database ]; then
        update-desktop-database /usr/share/applications 2>/dev/null || true
    fi
    
    # Update icon cache
    if [ -x /usr/bin/gtk-update-icon-cache ]; then
        gtk-update-icon-cache -f /usr/share/icons/hicolor 2>/dev/null || true
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
Exec=/usr/bin/school-bell
Icon=school-bell
Terminal=false
Type=Application
Categories=Education;Utility;
Keywords=school;bell;schedule;automation;
Keywords[ru]=школа;звонок;расписание;автоматизация;
EOF

# Calculate installed size
INSTALLED_SIZE=$(du -sk "$LIB_DIR" | cut -f1)
echo -e "${YELLOW}📊 Installed size: ${INSTALLED_SIZE} KB${NC}"

# Update control file with installed size
sed -i "s/^Architecture: all/Architecture: all\nInstalled-Size: ${INSTALLED_SIZE}/" "$DEBIAN_DIR/control"

# Set proper ownership and permissions
echo -e "${YELLOW}⚙️  Setting permissions...${NC}"
find "$BUILD_DIR" -type f -exec chmod 644 {} \;
find "$BUILD_DIR" -type d -exec chmod 755 {} \;
find "$LIB_DIR" -type f -name "*.so*" -exec chmod 755 {} \;
find "$LIB_DIR" -type f -executable -exec chmod 755 {} \;
chmod 755 "$DEBIAN_DIR"/*
chmod 755 "$USR_DIR/bin/school-bell"

# Build the package
echo -e "${YELLOW}📦 Building DEB package...${NC}"
cd "$BUILD_DIR"

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

exit 0
