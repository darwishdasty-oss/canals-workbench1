# Building Canals Workbench for Windows

## What you need

1. **Windows 10 or 11** (64-bit)
2. **Python 3.10 or newer** from https://www.python.org/downloads/windows/
   - ⚠️ **CRITICAL**: Tick **"Add Python to PATH"** during installation
3. **~ 1 GB free disk space** for the build
4. **Internet connection** (to download PySide6, numpy, scipy, matplotlib)

## Build in 3 minutes

### Step 1 — install Python

1. Download Python 3.11 from https://www.python.org/downloads/
2. Run the installer
3. **⚠️ Tick "Add Python to PATH"** on the first screen — this is the most common cause of "Python is not recognized" errors
4. Click "Install Now"

### Step 2 — get the code

Either:
- **From zip**: extract `canals_workbench.zip` anywhere (Desktop, Documents, etc.)
- **From git**: open PowerShell and run `git clone <repo-url> canals_workbench`

### Step 3 — double-click `bin\build_windows.bat`

That's it. The script will:
1. Verify Python is installed (and exit with clear error if not)
2. Install PySide6 + numpy + scipy + matplotlib + pyinstaller
3. Run PyInstaller using the verified `canals.spec`
4. Show a green "BUILD SUCCEEDED" message
5. Copy `Canals.exe` to your Desktop

**Expected timeline:**
- 1-3 min: pip install dependencies (depends on internet speed)
- 2-5 min: PyInstaller builds the binary
- ~ 5 min total

### Step 4 — verify the build

Run `bin\verify_windows_build.bat`. It runs 6 checks:
- File exists
- File size > 100 MB (typical: 130 MB)
- Valid Windows PE header
- PyInstaller marker present
- All 5 required modules bundled (canals, PySide6, numpy, scipy, matplotlib)
- Binary launches without immediate crash

Output:
```
===========================================================
   Verification summary:  6 passed,  0 failed
===========================================================
   BUILD IS GOOD.
```

### Step 5 — run Canals Workbench

`Canals.exe` has been copied to your Desktop. Double-click it. The Canals Workbench MDI shell opens with all 6 forms available from the menus.

### Step 6 — distribute

Right-click `dist\Canals.exe` → "Send to" → "Compressed (zipped) folder" → email / upload the resulting `.zip`. No Python installation required on the target machine.

---

## How to read the output

The build script's terminal output can look alarming if you've never used a Windows batch file before. Here's what the messages mean:

| Message | Meaning |
|---|---|
| `Press any key to continue . . .` | ✅ **SUCCESS** — the script finished. Press any key to close the window. |
| `[1/4] Checking Python installation... OK - found Python 3.11.9!` | ✅ Python is correctly installed. |
| `[2/4] Installing build dependencies... OK - all dependencies installed.` | ✅ Pip install worked. |
| `[3/4] Cleaning any previous build artifacts... OK - clean workspace ready.` | ✅ Old build/ and dist/ deleted. |
| `[4/4] Running PyInstaller...` | ⏳ Build is running. Wait 2-5 minutes. |
| `BUILD SUCCEEDED` | ✅ The .exe was created. |
| `BUILD FAILED - PyInstaller exited with error code N` | ❌ Scroll UP and look at the actual PyInstaller error. |

---

## Troubleshooting

### "Python is not recognized as an internal or external command"

Python is not on your PATH. Two options:

**Option A** — reinstall Python and tick "Add Python to PATH":
1. https://www.python.org/downloads/
2. Run installer
3. Tick "Add Python to PATH" on the first screen
4. Install
5. Re-run `build_windows.bat`

**Option B** — call Python with full path:
```cmd
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe bin\build_windows.bat
```

### "pip install fails" or "Could not fetch URL"

- Check your internet connection
- If behind a corporate proxy: set `HTTP_PROXY` and `HTTPS_PROXY` environment variables
- Try: `python -m pip install --upgrade pip` first, then re-run

### "Antivirus blocked PyInstaller" or "Windows Defender removed Canals.exe"

Some antivirus products (especially Windows Defender) flag PyInstaller executables as suspicious. This is a **false positive**.

Solutions:
1. Add an exception in Windows Defender for the `dist/` folder
2. Run `verify_windows_build.bat` which has a brief launch test
3. For real distribution: code-sign the .exe (requires a $200-400/year code-signing certificate from Sectigo or DigiCert)

### "Build failed" — but no clear error

Scroll UP from the "BUILD FAILED" message. The PyInstaller output above will contain the actual error. Common causes:
- Missing `PySide6` → run `pip install PySide6` manually
- Missing `numpy` / `scipy` / `matplotlib` → run `pip install numpy scipy matplotlib`
- Antivirus deleted `Canals.exe` mid-build → disable real-time scanning for the build folder

### "Canals.exe is only 5 MB" — way too small

A correctly-built Canals.exe should be **120-140 MB**. If you see < 50 MB, PyInstaller didn't bundle all dependencies. Check:
- `pip list` shows PySide6, numpy, scipy, matplotlib all installed
- No errors during the `pip install` step
- `canals.spec` is the correct spec file (don't replace it with a minimal one)

### "Canals.exe crashes on launch"

1. Run `bin\verify_windows_build.bat` — it'll launch Canals.exe for 5 seconds
2. If a window briefly appears, the build is good
3. If a console window appears with an error, capture the error message
4. Run from a terminal: `dist\Canals.exe` — errors will be visible in the terminal

### "Windows Defender flagged Canals.exe as Trojan"

This is a false positive. PyInstaller executables are notoriously flagged. Options:
1. **Submit to Microsoft** at https://www.microsoft.com/en-us/wdsi/filesubmission — they review and whitelist
2. **Code-sign** the .exe — signed binaries are flagged much less often
3. **Use `--onedir`** mode — produces a folder of files instead of one .exe; less likely to be flagged

---

## Building from CI / GitHub Actions

Instead of building on your local Windows machine, use the GitHub Actions workflow included in `.github/workflows/build.yml`. Push to GitHub and the pipeline builds `Canals.exe` on a real Microsoft-hosted Windows runner in ~ 5 minutes. See `.github/README.md` for details.

## Building on macOS or Linux

See `bin/build_linux.sh` and `bin/build_macos.sh`. Or use the GitHub Actions workflow which builds all 3 platforms in parallel.

---

## License

MIT — see LICENSE.
