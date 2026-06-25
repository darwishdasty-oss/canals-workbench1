@echo off
REM ====================================================================
REM   Build Canals Workbench for Windows
REM
REM   This script builds dist\Canals.exe from source.
REM
REM   REQUIREMENTS:
REM     - Windows 10 or 11
REM     - Python 3.10 or newer (https://www.python.org/downloads/)
REM       *** Tick "Add Python to PATH" during installation ***
REM
REM   USAGE:
REM     1. Open this folder in File Explorer
REM     2. Double-click build_windows.bat
REM     3. Wait ~ 5 minutes
REM     4. Look for the green "BUILD SUCCEEDED" message at the end
REM     5. dist\Canals.exe is ready
REM
REM   If you see a red "BUILD FAILED" message, scroll UP and read the
REM   error message that PyInstaller printed.
REM ====================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul

cd /d "%~dp0\.."

echo.
echo ===========================================================
echo   Canals Workbench v1.4.0  -  Windows Build Script
echo ===========================================================
echo.

REM Step 0: verify Python is on PATH
echo [1/4] Checking Python installation...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo   X  ERROR: Python is not on PATH.
    echo.
    echo   SOLUTION: Reinstall Python from https://www.python.org/downloads/
    echo   and tick the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo        OK - found Python !PYVER!
echo.

REM Step 1: upgrade pip and install build deps
echo [2/4] Installing build dependencies (PySide6, numpy, scipy, matplotlib, pyinstaller)...
echo        This takes 1-3 minutes depending on your internet speed.
echo.
python -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo   X  ERROR: pip upgrade failed. Check your internet connection.
    echo.
    pause
    exit /b 1
)

python -m pip install pyinstaller PySide6 numpy scipy matplotlib
if errorlevel 1 (
    echo.
    echo   X  ERROR: pip install failed. Check your internet connection
    echo      and that Python is correctly installed.
    echo.
    pause
    exit /b 1
)
echo.
echo        OK - all dependencies installed.
echo.

REM Step 2: clean any old build
echo [3/4] Cleaning any previous build artifacts...
if exist build (
    rmdir /s /q build
    echo        Removed old build\ directory
)
if exist dist (
    rmdir /s /q dist
    echo        Removed old dist\ directory
)
echo        OK - clean workspace ready.
echo.

REM Step 3: run PyInstaller
echo [4/4] Running PyInstaller... this takes 2-5 minutes.
echo        PyInstaller output follows:
echo.
echo ---------------------------------------------------------------
pyinstaller --clean --noconfirm canals.spec
set BUILD_EXIT=!errorlevel!
echo ---------------------------------------------------------------
echo.

REM Step 4: verify the output
if !BUILD_EXIT! neq 0 (
    echo.
    echo ===========================================================
    echo   X  X  X  BUILD FAILED  X  X  X
    echo ===========================================================
    echo.
    echo   PyInstaller exited with error code !BUILD_EXIT!.
    echo.
    echo   Scroll UP to see the actual error message from PyInstaller.
    echo   Common causes:
    echo     - Antivirus blocking PyInstaller
    echo     - Missing Visual C++ Redistributable (install from microsoft.com)
    echo     - Out of disk space (need ~ 1 GB free)
    echo     - Corrupted PyInstaller install - try:  pip install --upgrade --force-reinstall pyinstaller
    echo.
    pause
    exit /b !BUILD_EXIT!
)

if not exist "dist\Canals.exe" (
    echo.
    echo ===========================================================
    echo   X  X  X  BUILD FAILED  X  X  X
    echo ===========================================================
    echo.
    echo   PyInstaller reported success but dist\Canals.exe was not produced.
    echo   This usually means a missing module - check the PyInstaller
    echo   warnings above for "ModuleNotFoundError".
    echo.
    pause
    exit /b 1
)

REM Success!
echo ===========================================================
echo   BUILD SUCCEEDED
echo ===========================================================
echo.
echo   Canals.exe has been built at:
echo.
echo      %CD%\dist\Canals.exe
echo.

REM Show the file size
for %%A in ("dist\Canals.exe") do (
    set SIZE=%%~zA
    set /a SIZEMB=!SIZE! / 1048576
    echo   File size: !SIZEMB! MB
)
echo.

REM Run a smoke test - just verify the EXE header
echo   Verifying Canals.exe header...
powershell -Command "$bytes = [System.IO.File]::ReadAllBytes('dist\Canals.exe'); if ($bytes[0] -eq 0x4D -and $bytes[1] -eq 0x5A) { Write-Host '   OK - valid Windows PE file' } else { Write-Host '   WARNING - not a valid PE file' }"
echo.

REM Optional: copy to a more accessible location
echo   Copying to %USERPROFILE%\Desktop\Canals.exe for easy access...
copy /Y "dist\Canals.exe" "%USERPROFILE%\Desktop\Canals.exe" >nul 2>&1
if not errorlevel 1 (
    echo   OK - Canals.exe is now on your Desktop!
) else (
    echo   (Could not copy to Desktop - the file is still in dist\)
)
echo.

echo   To run Canals Workbench:
echo      - Double-click Canals.exe on your Desktop, OR
echo      - Navigate to %CD%\dist and double-click Canals.exe
echo.

echo   To distribute:
echo      - Right-click dist\Canals.exe
echo      - Send to - Compressed (zipped) folder
echo      - Email / upload the .zip to colleagues
echo.

echo   No Python installation is required on the target machine.
echo.

pause
endlocal
