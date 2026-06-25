#!/bin/bash
# ====================================================================
#  Build Canals Workbench for Linux
#  Produces: dist/Canals (~ 125 MB)
# ====================================================================

set -e
cd "$(dirname "$0")/.."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo
echo "==========================================================="
echo "  Canals Workbench v1.4.0  -  Linux Build Script"
echo "==========================================================="
echo

# Step 1: check Python
echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}ERROR: python3 not found. Install Python 3.10+ from https://python.org${NC}"
    exit 1
fi
PYVER=$(python3 --version)
echo "     OK - found $PYVER"
echo

# Step 2: install deps
echo "[2/4] Installing build dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller PySide6 numpy scipy matplotlib || {
    echo -e "${RED}ERROR: pip install failed. Check your internet connection.${NC}"
    exit 1
}
echo "     OK - all dependencies installed."
echo

# Step 3: clean
echo "[3/4] Cleaning previous build artifacts..."
rm -rf build dist
echo "     OK"
echo

# Step 4: build
echo "[4/4] Running PyInstaller (this takes 2-5 minutes)..."
echo "---------------------------------------------------------------"
pyinstaller --clean --noconfirm canals.spec
echo "---------------------------------------------------------------"
echo

# Verify
if [ ! -f "dist/Canals" ]; then
    echo -e "${RED}BUILD FAILED - dist/Canals not produced. Scroll up for the error.${NC}"
    exit 1
fi

SIZE_MB=$(du -m dist/Canals | cut -f1)

# Copy to a convenient location
cp dist/Canals /tmp/Canals 2>/dev/null || true

echo -e "${GREEN}===========================================================${NC}"
echo -e "${GREEN}  BUILD SUCCEEDED${NC}"
echo -e "${GREEN}===========================================================${NC}"
echo
echo "  Canals binary built at:"
echo "      $(pwd)/dist/Canals"
echo
echo "  File size: ${SIZE_MB} MB"
echo

# Smoke test
echo "  Verifying binary..."
chmod +x dist/Canals
timeout 3 ./dist/Canals 2>&1 | head -3 || true
echo

echo "  To run:    ./dist/Canals"
echo "  To share:  tar czf Canals-linux-x64.tar.gz dist/Canals"
echo
