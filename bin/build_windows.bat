@echo off
REM Build standalone Windows binary for Canals Workbench
REM Run this on a Windows machine with Python 3.10+ installed.

cd /d "%~dp0\.."

echo ===========================================================
echo  Building Canals Workbench Windows binary...
echo ===========================================================

REM Step 1: Install build dependencies
echo Installing PyInstaller and build deps...
pip install --upgrade pip
pip install pyinstaller PySide6 numpy scipy matplotlib

REM Step 2: Run the build using the verified .spec file
echo.
echo Running PyInstaller with canals.spec...
pyinstaller --clean --noconfirm canals.spec

echo.
echo ===========================================================
echo  Build complete!
echo  Output: dist\Canals.exe
echo  Size:   ~ 130 MB
echo ===========================================================
echo.
echo To distribute: zip up dist\Canals.exe and share.
echo No Python installation required on the target machine.

pause
