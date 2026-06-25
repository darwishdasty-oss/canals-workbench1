# -*- mode: python ; coding: utf-8 -*-
"""
canals.spec - PyInstaller spec for Canals Workbench.

Run via build_windows.bat / build_linux.sh / build_macos.sh which
call PyInstaller with --collect-all for PySide6 and matplotlib.
"""
import sys
import os

block_cipher = None

IS_WINDOWS = (sys.platform == 'win32')
EXE_NAME = 'Canals.exe' if IS_WINDOWS else 'Canals'

SPECPATH = os.path.abspath(SPECPATH)
PROJECT_ROOT = os.path.dirname(SPECPATH)

hiddenimports = [
    'canals', 'canals.cli',
    'canals.ui', 'canals.ui.forms',
    'canals.ui.forms.open_channel_form',
    'canals.ui.forms.structures_form',
    'canals.ui.forms.earth_canal_form',
    'canals.ui.forms.flow_profile_form',
    'canals.ui.forms.hydraulic_jump_form',
    'canals.ui.forms.water_hammer_form',
    'canals.ui.forms._widgets', 'canals.ui.forms._report_helper',
    'canals.reports',
    'canals.open_channel', 'canals.structures', 'canals.earth_canal',
    'canals.flow_profile', 'canals.hydraulic_jump', 'canals.water_hammer',
]

datas = [('canals', 'canals')]

icon_path = os.path.join(PROJECT_ROOT, 'figures', 'icon.ico' if IS_WINDOWS else 'icon.png')
icon = icon_path if os.path.exists(icon_path) else None

a = Analysis(
    ['canals_mdi.py'],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib.tests', 'numpy.tests', 'scipy.tests', 'pytest', 'IPython', 'jupyter', 'pandas'],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [], name=EXE_NAME,
    debug=False, strip=False, upx=True, console=False, icon=icon)
