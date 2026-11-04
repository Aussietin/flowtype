"""Build the itch.io screenshots in itch/screens/ (1280x720 PNG).

    python itch/make_screens.py [settings_render.png]

01, 02 and 04 are drawn mockups: the menu labels, icon shapes and colours come
from flowtype.py and tray_indicator.py, but the Windows chrome around them is
drawn here. 03 frames a real render of settings_gui.SettingsWindow (pass the
PNG captured from it; see ITCH-LISTING.md "Screenshots" for how). Each image is
labelled in its corner so nobody mistakes a mockup for a screen capture.
Needs Pillow only; fonts fall back to Pillow's default if the named ones are
missing.
"""
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "itch" / "screens"
W, H = 1280, 720

# tray_indicator imports pystray at module load; we only need the icon drawer.
sys.modules.setdefault("pystray", types.ModuleType("pystray"))
sys.path.insert(0, str(ROOT))
from tray_indicator import AMBER, GREY, RED, State, _build_icon

FONT_DIRS = ["/usr/share/fonts", "C:/Windows/Fonts"]


def _font(names, size):
    for d in FONT_DIRS:
        for n in names:
            for p in Path(d).rglob(n):
                try:
                    return ImageFont.truetype(str(p), size)
                except OSError:
                    pass
    return ImageFont.load_default(size)


def ui(size, bold=False):  # Windows-ish UI face (Segoe UI, else Carlito)
    return _font(["segoeuib.ttf" if bold else "segoeui.ttf",
                  "Carlito-Bold.ttf" if bold else "Carlito-Regular.ttf"], size)


def head(size, bold=True):  # caption face, matches itch/cover.png
    return _font(["segoeuib.ttf" if bold else "segoeui.ttf",
                  "Inter-Bold.otf" if bold else "Inter-Regular.otf"], size)


def mono(size):
    return _font(["consola.ttf", "JetBrainsMono-Regular.ttf", "DejaVuSansMono.ttf"], size)


GLYPH_FONT = next((str(p) for d in FONT_DIRS for n in ("seguisym.ttf", "DejaVuSans-Bold.ttf")
                   for p in Path(d).rglob(n)), "")

ACCENT = (110, 190, 255)
TEXT = (236, 238, 245)
MUTED = (165, 172, 195)


def background(title, subtitle):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    top, bot = (18, 20, 32), (28, 28, 52)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(top, bot)))
    d.rectangle([0, H - 6, W, H], fill=ACCENT)
    d.text((56, 40), title, font=head(40), fill=TEXT)
    d.text((56, 92), subtitle, font=head(22, bold=False), fill=MUTED)
    return img


def label(img, text):
    d = ImageDraw.Draw(img)
    f = head(15, bold=False)
    tw = d.textlength(text, font=f)
    x, y = W - tw - 36, H - 40
    d.rounded_rectangle([x - 10, y - 6, x + tw + 10, y + 22], radius=6, fill=(45, 48, 75))
    d.text((x, y - 1), text, font=f, fill=MUTED)


def shadow(img, box, radius=10, off=8):
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [box[0] + off // 2, box[1] + off, box[2] + off // 2, box[3] + off],
        radius=radius, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.paste(sh, (0, 0), sh)


def window(img, box, title, menu=("File", "Edit", "View")):
    """A Windows 11-style light window frame; returns the client-area top y."""
    shadow(img, box)
    d = ImageDraw.Draw(img)
    x0, y0, x1, _ = box
    d.rounded_rectangle(box, radius=8, fill=(255, 255, 255), outline=(200, 200, 205))
    d.rounded_rectangle([x0, y0, x1, y0 + 40], radius=8, fill=(238, 238, 242))
    d.rectangle([x0, y0 + 30, x1, y0 + 40], fill=(238, 238, 242))
    d.text((x0 + 16, y0 + 10), title, font=ui(15), fill=(30, 30, 30))
    for i, g in enumerate(("✕", "☐", "—")):
        d.text((x1 - 40 - i * 46, y0 + 8), g, font=_font(["DejaVuSans.ttf", "seguisym.ttf"], 15),
               fill=(60, 60, 60))
    y = y0 + 40
    if menu:
        mx = x0 + 14
        for m in menu:
            d.text((mx, y + 8), m, font=ui(15), fill=(40, 40, 40))
            mx += d.textlength(m, font=ui(15)) + 22
        y += 36
        d.line([(x0, y), (x1, y)], fill=(225, 225, 230))
    return y


def tray_icon(state, size):
    return _build_icon(state, GLYPH_FONT, shape="diamond").resize((size, size), Image.LANCZOS)


IDLE = State(text="", color=GREY)
RECORDING = State(text="●", color=RED)
TRANSCRIBING = State(text="…", color=AMBER)
ERROR = State(text="!", color=RED)


def taskbar_corner(img, x1, y, state, clock="9:41 AM"):
    """Right end of a Windows 11 taskbar with the flowtype diamond in the tray."""
    d = ImageDraw.Draw(img)
    x0 = x1 - 300
    d.rounded_rectangle([x0, y, x1, y + 48], radius=8, fill=(32, 32, 36))
    d.text((x0 + 18, y + 13), "^", font=ui(18), fill=(200, 200, 200))
    ic = tray_icon(state, 26)
    img.paste(ic, (x0 + 52, y + 11), ic)
    d.text((x0 + 98, y + 14), "ENG", font=ui(14), fill=(220, 220, 220))
    d.text((x1 - 90, y + 6), clock, font=ui(14), fill=(220, 220, 220))
    d.text((x1 - 90, y + 25), "4/11/2026", font=ui(14), fill=(220, 220, 220))
    return x0 + 65  # icon centre x


# --- 01: before / after in Notepad --------------------------------------------
SPOKEN = ("remind me to send the invoice to jordan on friday "
          "and book the car in for a service")
TYPED = ("Remind me to send the invoice to Jordan on Friday "
         "and book the car in for a service.")


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def notepad_panel(img, x, heading, state, body_lines, caret_after, bubble=None):
    d = ImageDraw.Draw(img)
    d.text((x, 150), heading, font=head(22), fill=ACCENT)
    box = (x, 190, x + 560, 560)
    cy = window(img, box, "Notes.txt - Notepad")
    d = ImageDraw.Draw(img)
    f = mono(18)
    ty = cy + 18
    for line in body_lines:
        d.text((x + 18, ty), line, font=f, fill=(25, 25, 25))
        ty += 28
    last = body_lines[-1] if caret_after else ""
    cx = x + 18 + d.textlength(last, font=f) + 2
    cyy = ty - 28 if caret_after else ty
    d.line([(cx, cyy + 2), (cx, cyy + 24)], fill=(0, 0, 0), width=2)
    icx = taskbar_corner(img, x + 560, 590, state)
    if bubble:
        bf = ui(17)
        lines = wrap(d, bubble, bf, 330)
        bh = 22 * len(lines) + 46
        bx1, by1 = x + 560, 575
        bx0, by0 = bx1 - 380, by1 - bh - 10
        shadow(img, (bx0, by0, bx1, by1 - 10), off=4)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([bx0, by0, bx1, by1 - 10], radius=12, fill=(255, 245, 245),
                            outline=RED[:3], width=2)
        d.polygon([(icx - 10, by1 - 11), (icx + 10, by1 - 11), (icx, by1 + 2)],
                  fill=(255, 245, 245))
        d.text((bx0 + 16, by0 + 10), "Holding Caps Lock, speaking:", font=ui(15, True),
               fill=RED[:3])
        for i, ln in enumerate(lines):
            d.text((bx0 + 16, by0 + 34 + i * 22), ln, font=bf, fill=(60, 30, 30))


def screen_dictation():
    img = background("Hold Caps Lock, talk, let go.",
                     "Your words are typed where your cursor is, in any app. Nothing leaves your PC.")
    notepad_panel(img, 56, "Before: hold Caps Lock and speak", RECORDING,
                  ["Friday:", ""], caret_after=True,
                  bubble="\u201c" + SPOKEN + "\u201d")
    d = ImageDraw.Draw(img)
    after_lines = ["Friday:"] + wrap(d, TYPED, mono(18), 520)
    notepad_panel(img, 664, "After: release the key", IDLE, after_lines, caret_after=True)
    d = ImageDraw.Draw(img)
    d.text((626, 360), "→", font=_font(["DejaVuSans-Bold.ttf", "seguisym.ttf"], 34), fill=ACCENT)
    label(img, "Mockup: drawn, not a screen capture")
    return img


# --- 02: tray icon and menu ------------------------------------------------------
MENU = [("Idle — hold caps lock to talk", "disabled"), ("-", None), ("Settings…", None),
        ("Restart flowtype", None), ("Refresh now", None), ("Quit", None)]


def screen_tray():
    img = background("Lives in your system tray.",
                     "Right-click the diamond for Settings, Restart and Quit. No window to manage.")
    d = ImageDraw.Draw(img)
    # desktop strip
    d.rounded_rectangle([300, 150, 980, 640], radius=14, fill=(58, 78, 120))
    for i in range(490):
        t = i / 490
        d.line([(300, 150 + i), (980, 150 + i)],
               fill=(int(70 + 40 * t), int(96 + 30 * t), int(150 + 20 * t)))
    icx = taskbar_corner(img, 960, 572, IDLE)
    # context menu above the icon
    f = ui(17)
    mw = 300
    rows = [(t, s) for t, s in MENU]
    mh = sum(14 if t == "-" else 40 for t, _ in rows) + 12
    mx0 = icx - 60
    mx1 = mx0 + mw
    if mx1 > 960:
        mx1 = 960
        mx0 = mx1 - mw
    my1 = 560
    my0 = my1 - mh
    shadow(img, (mx0, my0, mx1, my1), off=4)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([mx0, my0, mx1, my1], radius=8, fill=(249, 249, 251),
                        outline=(205, 205, 212))
    y = my0 + 6
    for t, s in rows:
        if t == "-":
            d.line([(mx0 + 10, y + 7), (mx1 - 10, y + 7)], fill=(215, 215, 220))
            y += 14
            continue
        if t == "Settings…":
            d.rounded_rectangle([mx0 + 6, y + 2, mx1 - 6, y + 38], radius=5, fill=(228, 236, 248))
        d.text((mx0 + 22, y + 9), t, font=f, fill=(150, 150, 155) if s else (25, 25, 25))
        y += 40
    # callout for the icon
    d.text((990, 560), "← flowtype sits\n    in your tray", font=head(18, bold=False), fill=TEXT,
           spacing=6)
    big = tray_icon(IDLE, 96)
    img.paste(big, (90, 300), big)
    d.text((70, 410), "Idle", font=head(20), fill=TEXT)
    d.text((70, 440), "Grey diamond =\nready to listen.", font=head(17, bold=False),
           fill=MUTED, spacing=6)
    label(img, "Mockup: menu labels from flowtype.py, icon from tray_indicator.py")
    return img


# --- 03: settings window (real render) ----------------------------------------
def screen_settings(render_path):
    img = background("Settings in plain English.",
                     "Change the hotkey, add names and jargon it should spell right. Restart from the tray to apply.")
    shot = Image.open(render_path).convert("RGB")
    max_h = 530
    if shot.height + 40 > max_h:
        s = (max_h - 40) / shot.height
        shot = shot.resize((int(shot.width * s), int(shot.height * s)), Image.LANCZOS)
    x0 = (W - shot.width) // 2 + 170
    y0 = 130
    box = (x0, y0, x0 + shot.width, y0 + 40 + shot.height)
    cy = window(img, box, "flowtype settings", menu=())
    img.paste(shot, (x0, cy))
    d = ImageDraw.Draw(img)
    notes = [("Hotkey", "Caps Lock by default.\nAdd others, or press\n“Detect keypress…”."),
             ("Known terms", "Names and jargon you\nsay a lot. Whisper\nspells them right."),
             ("LLM cleanup", "Optional, off by default.\nNeeds your own local\nOllama.")]
    y = 170
    for t, body in notes:
        d.text((70, y), t, font=head(21), fill=ACCENT)
        d.multiline_text((70, y + 32), body, font=head(17, bold=False), fill=TEXT, spacing=6)
        y += 140
    label(img, "Rendered from settings_gui.py (Tk on Linux; Windows uses native styling)")
    return img


# --- 04: tray states -----------------------------------------------------------
def screen_states():
    img = background("Always know what it's doing.",
                     "The tray diamond changes colour while it listens and types.")
    d = ImageDraw.Draw(img)
    states = [(IDLE, "Idle", "Ready. Hold Caps Lock\nto talk."),
              (RECORDING, "Recording", "Key held. Speak now;\nlet go when done."),
              (TRANSCRIBING, "Transcribing", "Turning your speech\ninto text, right here\non your PC."),
              (ERROR, "Problem", "No microphone, for\nexample. A message pops\nup and says why.")]
    cw = 270
    x = (W - cw * 4) // 2
    for st, name, body in states:
        d.rounded_rectangle([x + 10, 180, x + cw - 10, 600], radius=16, fill=(36, 38, 62))
        ic = tray_icon(st, 140)
        img.paste(ic, (x + (cw - 140) // 2, 220), ic)
        tw = d.textlength(name, font=head(26))
        d.text((x + (cw - tw) / 2, 390), name, font=head(26), fill=TEXT)
        for i, ln in enumerate(body.split("\n")):
            lw = d.textlength(ln, font=head(17, bold=False))
            d.text((x + (cw - lw) / 2, 440 + i * 26), ln, font=head(17, bold=False), fill=MUTED)
        x += cw
    label(img, "Icons drawn by tray_indicator.py, shown enlarged")
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    screen_dictation().save(OUT / "01-dictate-in-notepad.png")
    screen_tray().save(OUT / "02-tray-menu.png")
    if len(sys.argv) > 1:
        screen_settings(sys.argv[1]).save(OUT / "03-settings.png")
    screen_states().save(OUT / "04-tray-states.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))


if __name__ == "__main__":
    main()
