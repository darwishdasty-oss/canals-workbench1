#!/bin/bash
# ====================================================================
#  Build Canals Workbench for macOS (universal: x86_64 + arm64)
#  Produces: dist/Canals (~ 70 MB)
# ====================================================================

set -e
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo
echo "==========================================================="
echo "  Canals Workbench v1.4.0  -  macOS Build Script"
echo "==========================================================="
echo

# Step 1: check Python
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found. Install via 'brew install python@3.11' or python.org${NC}"
    exit 1
fi
PYVER=$(python3 --version)
echo "     OK - found $PYVER"
echo

# Step 2: install deps
echo "[2/4] Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller PySide6 numpy scipy matplotlib || {
    echo -e "${RED}ERROR: pip install failed.${NC}"
    exit 1
}
echo "     OK"
echo

# Step 3: clean
echo "[3/4] Cleaning previous build artifacts..."
rm -rf build dist
echo "     OK"
echo

# Step 4: build
echo "[4/4] Running PyInstaller..."
echo "---------------------------------------------------------------"
pyinstaller --clean --noconfirm canals.spec
echo "---------------------------------------------------------------"
echo

if [ ! -f "dist/Canals" ]; then
    echo -e "${RED}BUILD FAILED - dist/Canals not produced.${NC}"
    exit 1
fi

SIZE_MB=$(du -m dist/Canals | cut -f1)

echo -e "${GREEN}===========================================================${NC}"
echo -e "${GREEN}  BUILD SUCCEEDED${NC}"
echo -e "${GREEN}===========================================================${NC}"
echo
echo "  Canals binary built at: $(pwd)/dist/Canals"
echo "  File size: ${SIZE_MB} MB"
echo
echo "  To run:    ./dist/Canals"
echo "  To share:  tar czf Canals-macos-universal.tar.gz dist/Canals"
echo
