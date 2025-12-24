# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('model', 'model'), ('stopwords.txt', '.'), ('health_corpus.txt', '.')],
    hiddenimports=['sklearn.pipeline', 'sklearn.feature_extraction.text', 'sklearn.linear_model', 'sklearn.linear_model._logistic', 'sklearn.utils._cython_blas', 'sklearn.utils._typedefs', 'sklearn.metrics._classification'],
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
    name='DocumentAnalyzer',
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
)
