# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for FAI Inspection Tool
# Build with:  pyinstaller fai_tool.spec --clean --noconfirm
# Or run:      build.bat

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates',    'templates'),
        ('static',       'static'),
        ('aliases.json', '.'),
        ('tooltips.json', '.'),
    ],
    hiddenimports=[
        'flask',
        'markupsafe',
        'openpyxl',
        'openpyxl.styles.builtins',
        'flaskwebgui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='FAI_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,        # no terminal window — native GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='static/icon.ico',  # uncomment and add a .ico file to enable a custom icon
)
