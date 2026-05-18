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
