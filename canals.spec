# -*- mode: python ; coding: utf-8 -*-
"""
canals.spec - PyInstaller spec for Canals Workbench.

Builds a standalone Windows .exe (when run on Windows) or Linux ELF (when run on Linux).

Build commands:
    pyinstaller --clean canals.spec

Produces:
    dist/Canals                (Linux, ~50 MB)
    dist/Canals.exe            (Windows, ~50 MB)
"""
import sys
import os

block_cipher = None

IS_WINDOWS = (sys.platform == 'win32')
EXE_NAME = 'Canals.exe' if IS_WINDOWS else 'Canals'

SPECPATH = os.path.abspath(SPECPATH)
PROJECT_ROOT = os.path.dirname(SPECPATH)

# Explicit list of hidden imports
hiddenimports = [
    # PySide6
    'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
    'PySide6.QtPrintSupport', 'PySide6.QtNetwork',
    # numpy / scipy / matplotlib
    'numpy', 'scipy', 'matplotlib',
    'matplotlib.backends.backend_qtagg',
    'matplotlib.backends.backend_agg',
    # Canals
    'canals', 'canals.cli',
    'canals.ui', 'canals.ui.forms',
    'canals.ui.forms.open_channel_form',
    'canals.ui.forms.structures_form',
    'canals.ui.forms.earth_canal_form',
    'canals.ui.forms.flow_profile_form',
    'canals.ui.forms.hydraulic_jump_form',
    'canals.ui.forms.water_hammer_form',
    'canals.ui.forms._widgets',
    'canals.open_channel', 'canals.structures', 'canals.earth_canal',
    'canals.flow_profile', 'canals.hydraulic_jump', 'canals.water_hammer',
]

datas = [
    ('canals', 'canals'),
]

icon_path = os.path.join(PROJECT_ROOT, 'figures', 'icon.ico' if IS_WINDOWS else 'icon.png')
icon = icon_path if os.path.exists(icon_path) else None

a = Analysis(
    ['canals_mdi.py'],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.tests',
        'numpy.tests',
        'scipy.tests',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=EXE_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)
