# -*- mode: python ; coding: utf-8 -*-
# Foster_Structural.spec — VERSION FINALE (avec .env intégré)

from PyInstaller.utils.hooks import collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icons', 'icons'),
        ('settings.json', '.'),
        ('diagrams_settings.json', '.'),
        ('load_combinations.json', '.'),
        ('.env', '.'),                    # ← AJOUTÉ : ton fichier .env
    ],
    hiddenimports=[
        'PySide6', 'PySide6.QtWidgets', 'PySide6.QtCore', 'PySide6.QtGui',
        'PySide6.QtSvg', 'PySide6.QtNetwork',
        'openai', 'ezdxf', 'Pynite', 'numpy', 'dotenv', 'certifi',
        'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends.backend_agg',
        'matplotlib.backends.backend_qtagg',
        'PIL', 'PIL._imaging', 'PIL.Image',
        'scipy', 'scipy.linalg', 'scipy.integrate', 'scipy.optimize',
    ],
    runtime_hooks=['runtime_hook_openblas.py'],
    excludes=['tkinter', 'PyQt5', 'PyQt6', 'torch', 'matplotlib.tests'],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Foster_Structural',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    icon='icons/worker.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Foster_Structural'
)