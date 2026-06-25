#!/bin/bash
# Build standalone Linux binary for Canals Workbench
# Run on Linux with Python 3.10+ installed.
set -e
cd "$(dirname "$0")/.."

echo "==========================================================="
echo " Building Canals Workbench Linux binary..."
echo "==========================================================="

# Install build dependencies
echo "Installing PyInstaller and build deps..."
pip install --upgrade pip
pip install pyinstaller PySide6 numpy scipy matplotlib

# Build
echo ""
echo "Running PyInstaller with canals.spec..."
pyinstaller --clean --noconfirm canals.spec

echo ""
echo "==========================================================="
echo " Build complete!"
echo " Output: dist/Canals"
echo " Size:   ~ 130 MB"
echo "==========================================================="
echo ""
echo "To run: chmod +x dist/Canals && ./dist/Canals"
echo "To distribute: tar czf Canals-linux-x64.tar.gz dist/Canals"
