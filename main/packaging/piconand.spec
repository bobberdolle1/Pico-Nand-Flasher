# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

assets_dir = os.path.abspath(os.path.join(project_root, 'main', 'assets'))
icon_path = None
if os.path.isdir(assets_dir):
    # Prefer .ico on Windows, .icns on macOS, .png otherwise
    if sys.platform.startswith('win'):
        cand = os.path.join(assets_dir, 'app.ico')
        if os.path.exists(cand):
            icon_path = cand
    elif sys.platform == 'darwin':
        cand = os.path.join(assets_dir, 'app.icns')
        if os.path.exists(cand):
            icon_path = cand
    else:
        cand = os.path.join(assets_dir, 'app.png')
        if os.path.exists(cand):
            icon_path = cand

extra_datas = []
if os.path.isdir(assets_dir):
    # bundle entire assets directory
    extra_datas.append((assets_dir, 'assets'))

a = Analysis(
    ['main/gui/main_app.py'],
    pathex=[project_root],
    binaries=[],
    datas=extra_datas,
    hiddenimports=['PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.QtCore', 'serial', 'serial.tools.list_ports'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PicoNANDFlasher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PicoNANDFlasher')
