from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata


project_dir = Path(SPECPATH)
model_path = Path.home() / ".rembg" / "models" / "u2net" / "u2net.onnx"

if not model_path.is_file():
    raise FileNotFoundError(
        "The offline u2net model was not found. Run AI mode once before building: "
        f"{model_path}"
    )

rembg_datas, rembg_binaries, rembg_hiddenimports = collect_all("rembg")

app_data = [
    (str(project_dir / "assets" / "EraserLogo.png"), "assets"),
    (str(project_dir / "assets" / "cherryBlossomTop.png"), "assets"),
    (str(project_dir / "assets" / "cherryBlossomBottom.png"), "assets"),
    (str(model_path), "models/u2net"),
] + copy_metadata("pymatting")

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=rembg_binaries,
    datas=app_data + rembg_datas,
    hiddenimports=rembg_hiddenimports,
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
    [],
    exclude_binaries=True,
    name="iErase",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="iErase",
)
