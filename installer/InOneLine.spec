# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

spec_dir = Path(SPECPATH).resolve()
root = spec_dir.parent
web_dir = root / "streaming_manager" / "web"
icon_master = root / "assets" / "InOneLine_icon_master.png"
icon_ico = root / "assets" / "InOneLine.ico"

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtMultimedia",
    "websocket",
    "mutagen",
    "mutagen.id3",
    "mutagen.mp3",
    "mutagen.wave",
    "mutagen.oggvorbis",
    "mutagen.oggopus",
    "mutagen.oggflac",
    "mutagen.flac",
]

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(web_dir), "streaming_manager/web"),
        (str(icon_master), "assets"),
        (str(root / "assets" / "InOneLine_wheel_default.png"), "assets"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pytest"],
    noarchive=False,
    optimize=1,
)

# A host-wide Poppler installation may contribute incompatible ICU DLLs to
# PyInstaller's dependency search path. They are unrelated to this Qt app and
# override Qt's own ICU dependencies when placed beside the executable.
a.binaries = [item for item in a.binaries if item[0].lower() not in {
    "icuuc.dll", "icudt78.dll",
}]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InOneLine",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    contents_directory="_internal",
    icon=str(icon_ico),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="InOneLine",
)
