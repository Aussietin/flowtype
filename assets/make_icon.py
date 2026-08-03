"""Generates icon.ico from the same donut-render used by the tray icon (GREY 'FT')."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tray_indicator import State, GREY, _build_icon

state = State(fraction=1.0, text="FT", color=GREY, tooltip="flowtype")
img = _build_icon(state, "C:/Windows/Fonts/segoeuib.ttf")
out = Path(__file__).resolve().parent / "icon.ico"
img.save(out, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"wrote {out}")
