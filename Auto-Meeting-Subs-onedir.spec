# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_dynamic_libs

# Collect dynamic libraries from onnxruntime
binaries = collect_dynamic_libs('onnxruntime', destdir='onnxruntime/capi')

a = Analysis(
    ['D:/Github Repos/Personal Projects/Auto-Meeting-Subs/Auto-Meeting-Subs.py'],
    pathex=[],
    binaries=binaries,
    datas=[('C:/Python/Environments/auto-meeting-sub-env/Lib/site-packages/lightning_fabric/version.info', 'lightning_fabric'),
           ('C:/Python/Environments/auto-meeting-sub-env/Lib/site-packages/whisperx/assets/mel_filters.npz', 'whisperx/assets')],
    hiddenimports=['pytorch-cuda', 'tty', 'posix', 'multiprocessing', 'matplotlib', 'pyreadline3', 'pyparsing', 'setuptools', 'numpy', 'six', 'dateutil', 'scipy', 'curses', 'sympy', 'numba', 'pygments', 'pandas', 'sqlalchemy', 'nltk', 'urllib3', 'torch', 'aiohttp', 'lightning', 'transformers', 'optuna', 'librosa', 'einops', 'pyannote', 'pyannote.audio.models.segmentation', 'pyannote.audio.models.embedding'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Auto-Meeting-Subs',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\Github Repos\\Personal Projects\\Auto-Meeting-Subs\\Auto-Meeting-Subs.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Auto-Meeting-Subs'
)