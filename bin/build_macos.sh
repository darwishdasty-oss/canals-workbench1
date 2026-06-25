#!/bin/bash
# Build standalone macOS binary for Canals Workbench
set -e
cd "$(dirname "$0")/.."

echo "Building Canals Workbench macOS binary..."
pyinstaller --name="Canals" \
    --windowed \
    --onefile \
    --add-data="canals:canals" \
    --add-data="canals_mdi.py:." \
    --hidden-import="canals" \
    --hidden-import="canals.ui" \
    --hidden-import="canals.ui.forms" \
    --collect-all="PySide6" \
    --collect-all="matplotlib" \
    --icon="figures/icon.icns" \
    canals_mdi.py

echo "Done. Binary: dist/Canals (~ 70 MB)"
