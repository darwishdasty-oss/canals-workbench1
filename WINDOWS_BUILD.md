# Building Canals Workbench for Windows

## What's in this kit

This directory contains everything needed to build `Canals.exe` (the Windows
executable) on a Windows machine:

```
canals_workbench/
├── canals_mdi.py            ← Python entry point
├── canals/                  ← The package (algorithm + forms)
├── canals.spec              ← PyInstaller spec (verified working)
├── pyproject.toml           ← pip metadata
├── README.md
├── LICENSE
├── tests/                   ← 17 unit tests
├── docs/USER_GUIDE.md
├── bin/
│   ├── build_windows.bat    ← Double-click this on Windows
│   ├── build_linux.sh
│   └── build_macos.sh
└── WINDOWS_BUILD.md         ← This file
```

## Quickest way to build (3 minutes)

### Step 1 — install prerequisites on your Windows machine

1. **Python 3.10 or newer** — https://www.python.org/downloads/windows/
   - Tick **"Add Python to PATH"** during installation
2. **Git for Windows** (optional, for cloning) — https://git-scm.com/

### Step 2 — get the source

Either:

- **Option A (zip):** transfer the `canals_workbench/` directory to your Windows
  machine via USB, OneDrive, email attachment, etc.
- **Option B (git):** open PowerShell and run:
  ```cmd
  git clone https://github.com/abbas-hebah/canals-workbench.git
  cd canals-workbench
  ```

### Step 3 — double-click `bin\build_windows.bat`

This script will:
1. Install `pyinstaller`, `PySide6`, `numpy`, `scipy`, `matplotlib`
2. Run PyInstaller using `canals.spec`
3. Produce `dist\Canals.exe` (~ 130 MB)

It typically takes 2-3 minutes. When it finishes, you'll see
"Build complete! Output: dist\Canals.exe".

### Step 4 — test it

Double-click `dist\Canals.exe`. The Canals Workbench MDI shell should open
with all 6 forms available from the menus.

### Step 5 — distribute

The single `Canals.exe` file is fully self-contained — no Python installation
required on the target machine. Compress it (right-click → Send to →
Compressed (zipped) folder) and email / upload / copy as needed.

## Manual build (if the .bat fails)

Open `cmd.exe` (or PowerShell) in the `canals_workbench` directory and run:

```cmd
pip install pyinstaller PySide6 numpy scipy matplotlib
pyinstaller --clean --noconfirm canals.spec
dir dist
```

Expected output:

```
   ...
   Build complete! The results are available in: ...\dist
```

Then check `dist\Canals.exe` exists and is roughly 130 MB.

## Troubleshooting

### "Python is not recognized"

Python is not in your PATH. Reinstall Python and tick "Add Python to PATH",
or run the .bat from the directory containing `python.exe`:

```cmd
cd C:\path\to\canals_workbench
C:\Python311\python.exe bin\build_windows.bat
```

### "PyInstaller not found"

The .bat installs it, but if that step failed (e.g. no internet), install
manually:

```cmd
pip install pyinstaller
```

### "Canals.exe crashes on launch"

Most likely a missing hidden import. Edit `canals.spec` and add the missing
module to `hiddenimports`. The full list of currently-imported modules is:

```
PySide6.QtCore, PySide6.QtWidgets, PySide6.QtGui, PySide6.QtPrintSupport,
PySide6.QtNetwork, numpy, scipy, matplotlib, matplotlib.backends.backend_qtagg,
matplotlib.backends.backend_agg,
canals, canals.cli, canals.ui, canals.ui.forms,
canals.ui.forms.open_channel_form,
canals.ui.forms.structures_form,
canals.ui.forms.earth_canal_form,
canals.ui.forms.flow_profile_form,
canals.ui.forms.hydraulic_jump_form,
canals.ui.forms.water_hammer_form,
canals.ui.forms._widgets,
canals.open_channel, canals.structures, canals.earth_canal,
canals.flow_profile, canals.hydraulic_jump, canals.water_hammer
```

### "Windows Defender flags the .exe as suspicious"

This is a common false-positive with PyInstaller binaries. Solutions:

1. **Code-sign the .exe** (requires a code-signing certificate, $200-400/year)
2. **Submit to Microsoft** for analysis: https://www.microsoft.com/en-us/wdsi/filesubmission
3. **Distribute as a zip** — Defender is less aggressive with zip files
4. **Use `--onedir` mode** instead of `--onefile` — produces a directory of
   files instead of a single exe. The directory is less likely to trigger
   heuristics. Edit `canals.spec` and change `EXE(...)` to use `COLLECT(...)`.

## Building from CI / GitHub Actions

For automated builds, see `.github/workflows/build.yml` (to be created) or
use this minimal workflow:

```yaml
name: Build Windows exe
on: [push]
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pyinstaller PySide6 numpy scipy matplotlib
      - run: pyinstaller --clean --noconfirm canals.spec
      - uses: actions/upload-artifact@v3
        with:
          name: Canals-Windows-x64
          path: dist/Canals.exe
```

This produces a downloadable `Canals-Windows-x64.zip` artifact on every push.

## License

MIT — see LICENSE.
