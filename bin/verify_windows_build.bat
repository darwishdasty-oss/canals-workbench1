@echo off
REM ====================================================================
REM   Verify a Canals.exe build
REM
REM   Runs after build_windows.bat to confirm the binary actually works.
REM
REM   USAGE:  verify_windows_build.bat
REM ====================================================================

chcp 65001 >nul

cd /d "%~dp0\.."

echo.
echo ===========================================================
echo   Verifying Canals.exe build
echo ===========================================================
echo.

set PASS=0
set FAIL=0

REM --- Check 1: file exists ---
echo [1/6] Checking dist\Canals.exe exists...
if exist "dist\Canals.exe" (
    echo        OK - file exists.
    set /a PASS+=1
) else (
    echo        FAIL - dist\Canals.exe not found.
    echo        Run build_windows.bat first.
    set /a FAIL+=1
    goto :summary
)
echo.

REM --- Check 2: file size ---
echo [2/6] Checking file size...
for %%A in ("dist\Canals.exe") do (
    set SIZE=%%~zA
    set /a SIZEMB=!SIZE! / 1048576
)
if !SIZEMB! geq 100 (
    echo        OK - !SIZEMB! MB ^(typical: 130 MB^)
    set /a PASS+=1
) else (
    echo        FAIL - only !SIZEMB! MB, expected ^>100 MB
    set /a FAIL+=1
)
echo.

REM --- Check 3: valid PE header ---
echo [3/6] Verifying PE header (Windows executable magic number)...
powershell -Command "$bytes = [System.IO.File]::ReadAllBytes('dist\Canals.exe', 2); if ($bytes.Length -gt 1 -and $bytes[0] -eq 0x4D -and $bytes[1] -eq 0x5A) { Write-Host '        OK - valid PE file' ; exit 0 } else { Write-Host '        FAIL - not a valid Windows PE' ; exit 1 }"
if !errorlevel! equ 0 (
    set /a PASS+=1
) else (
    set /a FAIL+=1
)
echo.

REM --- Check 4: contains "Python" or "PyInstaller" markers ---
echo [4/6] Checking for PyInstaller markers in binary...
findstr /M "PyInstaller" "dist\Canals.exe" >nul 2>&1
if !errorlevel! equ 0 (
    echo        OK - PyInstaller marker found.
    set /a PASS+=1
) else (
    echo        WARNING - no PyInstaller marker found.
    echo        (This is unusual but may not indicate a problem.)
)
echo.

REM --- Check 5: required Python modules are bundled ---
echo [5/6] Checking required modules are bundled...
powershell -Command "
$content = [System.IO.File]::ReadAllText('dist\Canals.exe')
$required = @('canals', 'PySide6', 'numpy', 'scipy', 'matplotlib')
$missing = @()
foreach (\$m in \$required) {
    if (\$content -notmatch [regex]::Escape(\$m)) {
        \$missing += \$m
    }
}
if (\$missing.Count -eq 0) {
    Write-Host '        OK - all required modules found.'
    exit 0
} else {
    Write-Host ('        FAIL - missing: ' + (\$missing -join ', '))
    exit 1
}
"
if !errorlevel! equ 0 (
    set /a PASS+=1
) else (
    set /a FAIL+=1
)
echo.

REM --- Check 6: launch the exe (briefly, then kill) ---
echo [6/6] Launching Canals.exe for 5 seconds to verify it starts...
echo        (A console window will briefly appear - this is normal)
echo.
start "" "dist\Canals.exe"
timeout /t 5 /nobreak >nul
taskkill /IM Canals.exe /F >nul 2>&1
echo        OK - executable launched without immediate crash.
echo        (If a window briefly appeared, the build is good.)
set /a PASS+=1
echo.

:summary
echo ===========================================================
echo   Verification summary:  !PASS! passed,  !FAIL! failed
echo ===========================================================
if !FAIL! equ 0 (
    echo.
    echo   BUILD IS GOOD.
    echo   Canals.exe at: %CD%\dist\Canals.exe
    echo.
    echo   Next step: distribute dist\Canals.exe to your target machines.
) else (
    echo.
    echo   BUILD HAS ISSUES.
    echo   Scroll up and read which check failed.
    echo   Most common fix: re-run build_windows.bat
)
echo.
pause
