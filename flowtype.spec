# PyInstaller spec — flowtype onedir freeze.
#
#   venv\Scripts\python.exe build\fetch_model.py      # once, populates build/model
#   venv\Scripts\pyinstaller flowtype.spec --noconfirm
#
# onedir (not onefile): the CTranslate2 / PyAV native DLLs plus the 145 MB model
# make onefile's per-launch temp-extract slow and antivirus-prone.
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files

SPEC_DIR = Path(SPECPATH)

datas = [
    ("config.json", "."),                       # bundled default config (seeds %APPDATA% on first run)
    ("assets/icon.ico", "assets"),
]
binaries = []
hiddenimports = ["pystray._win32"]

# Native-heavy deps: grab everything (python modules, data, DLLs).
for pkg in ("ctranslate2", "av", "faster_whisper", "onnxruntime", "sounddevice"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# Bundled whisper model — paths.py expects models/base.en/model.bin under _MEIPASS.
model_dir = SPEC_DIR / "build" / "model" / "base.en"
if not (model_dir / "model.bin").exists():
    raise SystemExit("build/model/base.en/model.bin missing — run build/fetch_model.py first")
datas += [(str(p), "models/base.en") for p in model_dir.iterdir() if p.is_file()]

a = Analysis(
    ["flowtype.py"],
    pathex=[str(SPEC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="flowtype",
    console=False,             # windowed — matches the pythonw launch
    icon="assets/icon.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="flowtype",
)
