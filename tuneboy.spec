# -*- mode: python ; coding: utf-8 -*-

import os
import sys

block_cipher = None
project_root = os.path.dirname(os.path.abspath(sys.argv[0]))

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    datas=[
        ('config.py', '.'),
        ('audio_engine.py', '.'),
        ('components.py', '.'),
        ('screens.py', '.'),
    ],
    hiddenimports=[
        'numpy.core._dtype_ctypes',
        'pygame.midi',
        'json',
    ],
    excludes=['_tkinter', 'PyQt5.QtDesigner', 'scipy', 'matplotlib'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='tuneboy',
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon='tuneboy.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='tuneboy'
)
