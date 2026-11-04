# flowtype — itch.io listing pack (v1.0.0)

Everything on the itch.io page is decided here, in the order itch's
"Edit project" form asks for it. Paste each block into its field. The only
choice left is **the licence line** (§9), which is picked from two options.

Sources: `README.md`, `EULA.txt`, `docs/SHIPCHECK.md` (#10),
`docs/TRUST-AUDIT.md` (#13), `installer.iss`, `flowtype.py`, and CI run
[41770943984](https://github.com/Aussietin/flowtype/actions/runs/41770943984)
(Windows installer on #13's head `ebb6cbb`).

---

## The 10-minute run-through

1. **Build to upload:** the `flowtype-setup` artifact from the Windows
   installer run on the **combined** release stack (#8 → #10 → #11 → #13 →
   #14): run
   [41779687765](https://github.com/Aussietin/flowtype/actions/runs/41779687765),
   artifact 13297874140 (it expires 2026-12-04). If that has expired, or
   anything else lands first, run the "Windows installer" workflow on `main`
   after merging and use that artifact instead. **Never** upload the stale
   23 Sep build in your local `installer-output\` (see SHIPCHECK).
2. Unzip it. `flowtype-setup.exe.sha256` holds one line, written by the
   workflow as `<64 lowercase hex chars>  flowtype-setup.exe` (two spaces, no
   newline). Copy only the 64-character hash, not the file name, and paste it
   in place of `<SHA256>` in the Description (§3).
3. *Optional, 15 min, recommended:* submit `flowtype-setup.exe` to the
   Defender portal first (TRUST-AUDIT §1a).
4. itch.io → **Create new project**, and fill the fields from §1–§8 below.
   Replace `<SUPPORT_EMAIL>` (two places) and pick the licence line (§9).
5. Upload `itch/cover.png` (from #10) and the four screenshots in
   `itch/screens/` (§7).
6. Save as **Draft**, open the page and read it once. Then set it to
   **Public**.

---

## 1. Basics

| itch field | Value |
|---|---|
| Title | `flowtype` |
| Project URL | `<your-itch-username>.itch.io/flowtype` |
| Short description or tagline | `Offline dictation for Windows. Hold Caps Lock, talk, let go. Pay once.` |
| Classification | **Tools** |
| Kind of project | **Downloadable** |
| Release status | **Released** |

The name stays `flowtype`. The older "Flowtype" web-typography project is a
jQuery plugin for web pages, not a desktop app or an itch listing, so the two
won't be confused.

## 2. Pricing

| itch field | Value |
|---|---|
| Pricing | **Paid** |
| Price | **$10.00 USD** (≈ A$15) |
| Minimum price | **$10.00** (the same as the price) |
| "Let people pay more" | **On** (itch's default; leave it) |
| Sales / bundles / rewards | None at launch |
| Revenue share to itch | Leave itch's default (10%) |

## 3. Description (paste as-is)

> Lead paragraph is ~150 words and opens with "Offline, private, hold Caps
> Lock to dictate". The sections under it are short and plain so the page
> scans.

```markdown
**Offline, private, hold Caps Lock to dictate.** flowtype types what you say into any Windows app: email, Word, Notepad, chat, your browser. Hold Caps Lock, speak, let go, and your words appear at the cursor a moment later.

Everything runs on your PC. The speech model is built in, so flowtype never connects to the internet. There's no account and no subscription, and your voice is never uploaded.

It sits quietly in the system tray. A small diamond turns red while you talk and amber while it works. No window to manage. Whatever you had copied is put back on the clipboard after each paste.

Add the names and jargon you use, such as people, products and places, and it spells them right. Prefer another key? Pick one in Settings.

Pay once and it's yours. English only. Windows 10 and 11, 64-bit. No admin rights or graphics card needed.

## Features

- **Hold-to-talk anywhere.** Hold Caps Lock (or any key you choose), speak, release. The text is pasted wherever your cursor is.
- **100% offline.** Speech recognition runs on your own CPU using OpenAI's Whisper model (base.en), bundled in the installer. Nothing to download after install, no internet needed.
- **Private by design.** No account, no telemetry, no cloud. Audio is kept only while you hold the key and is never saved to disk.
- **Your clipboard is safe.** flowtype puts back whatever you had copied after each paste.
- **Spells your words right.** Add names, places and jargon in Settings, and flowtype leans towards them when it hears something close.
- **Tray status at a glance.** Grey = ready, red = listening, amber = typing, red "!" = something's wrong (such as no microphone), with a pop-up that says why.
- **Simple settings window.** Choose your hotkey (with a "Detect keypress" button), the longest a recording can run, and whether to add a space after each dictation.
- **Quiet installer.** Per-user install, no admin prompt. Optional "start with Windows" box, unticked by default. Uninstalling removes everything, including your settings.
- **Optional AI clean-up (advanced).** If you already run [Ollama](https://ollama.com) on your PC, flowtype can tidy filler words before pasting. Off by default.

## System requirements

- Windows 10 or Windows 11, **64-bit**
- Any 64-bit Intel or AMD processor. **No graphics card needed.**
- **4 GB RAM** (flowtype itself uses about half a gigabyte while running)
- **1 GB free disk space** (the download is about 193 MB, and it installs to roughly 600 MB)
- A microphone (built-in laptop mics work)
- No internet connection needed after you download it
- English speech only

## Good to know

- **Caps Lock won't toggle capitals while flowtype is running**, because flowtype uses the key for talking. Pick a different hotkey in Settings if you need Caps Lock.
- **The microphone light stays on** while flowtype runs. It keeps the mic open so your first word isn't cut off, but it only keeps audio while you hold the key.
- Tap **Esc twice** to quit quickly, or right-click the tray diamond → **Quit**.

## Windows will warn you the first time

flowtype isn't code-signed yet, so SmartScreen says "Windows protected your PC". Click **More info → Run anyway**. The SHA256 below lets you confirm the file is the one I uploaded.

**Why antivirus may look twice:** hold-to-talk needs to see when you press and release your hotkey, so flowtype installs a keyboard hook. It pastes your words by putting them on the clipboard and pressing Ctrl+V for you. Those are the same Windows features keyloggers use. flowtype makes no network connections at all. Windows also shows the microphone-in-use indicator the whole time flowtype is running, because it keeps the mic open so your first word isn't clipped; it only keeps audio while you hold the key.

The keyboard hook can see every key press on the PC, but flowtype only acts on your hotkey and Esc, and never stores or sends any other keys.

**SHA256 of flowtype-setup.exe (v1.0.0):**
`<SHA256>`

To check it, open PowerShell in your Downloads folder and run `(Get-FileHash .\flowtype-setup.exe).Hash.ToLower()`. The string it prints should match the one above. (Plain `Get-FileHash` shows the same hash in capitals.)

## Privacy

- Audio is recorded only while you hold the hotkey, turned into text on your PC, and then thrown away. Nothing is uploaded, and there is no telemetry or analytics.
- Each transcript is saved in plain text to `%APPDATA%\flowtype\logs\transcripts.jsonl` so you can find something you said earlier. Anyone with access to your Windows account can read it. Delete it whenever you like.
- Uninstalling removes the whole `%APPDATA%\flowtype` folder, including that file and your settings.
- flowtype pastes by using the clipboard. If you've turned on Windows clipboard history (Win+V), dictated text shows up there like anything else you copy, and if you've also turned on "Sync across your devices", Windows syncs it to your Microsoft account.
- The optional AI clean-up is off by default. If you turn it on, the text goes to the Ollama server named in Settings, which is your own PC unless you change it.

## Refunds

If flowtype doesn't work on your PC, email me within 30 days of buying and I'll refund you in full. Nothing here limits your rights under the Australian Consumer Law.

## Support

Email **<SUPPORT_EMAIL>** or leave a comment below. Please include your Windows version and what happened.

## Licence

<LICENCE LINE: paste option A or B from ITCH-LISTING.md §9>

flowtype includes third-party software and the Whisper speech model under their own licences, listed in THIRD-PARTY-NOTICES.txt (installed next to flowtype.exe), including the GPL source offer.

## Changelog

**v1.0.0** (first release)
- Hold-to-talk dictation into any app, with Caps Lock as the default key
- Whisper base.en model bundled; works fully offline
- Tray icon with idle, recording, transcribing and error states
- Settings window: hotkeys with keypress detection, known-terms list, recording limit, trailing space, optional Ollama clean-up
- Clipboard restored after every paste
- Per-user installer (no admin), optional start with Windows, full clean-up on uninstall
- Version details on the exe and installer (Properties → Details)
```

Word count of the lead (first five paragraphs, ending "…graphics card
needed."): 149.

## 4. Uploads

| Field | Value |
|---|---|
| File | `flowtype-setup.exe` (keep this exact name so it matches `flowtype-setup.exe.sha256` and the description) |
| Display name | `flowtype 1.0.0 — Windows installer (64-bit)` |
| Platform checkbox | **Windows** only |
| "This file will be played in the browser" | Off |
| Pre-order / hide | Off |
| Other files | None. The SHA256 goes in the description, not as a separate upload. |

Size check: the CI artifact for #13 is 202,324,055 bytes zipped (the exe plus
its `.sha256`). The exe is slightly smaller, about 193 MB, which is the figure
in §3. If the real exe differs by more than ~10 MB, change "about 193 MB".

## 5. Details, tags and metadata

| itch field | Value |
|---|---|
| Platforms | **Windows** |
| Tags (10, itch's maximum) | `dictation`, `speech-to-text`, `voice-typing`, `offline`, `privacy`, `productivity`, `accessibility`, `transcription`, `whisper`, `utility` |
| Languages | English |
| Inputs | Keyboard, Microphone |
| Accessibility | (leave blank, as itch's options are game-focused) |
| AI generation disclosure | **Yes**: text and code were written with AI assistance. No AI-generated graphics or audio. (The Whisper speech model is a recognition model, not generated content.) |
| Links | `https://github.com/Aussietin/flowtype` (only if you pick licence option A; leave blank under option B) |

## 6. Community and visibility

| itch field | Value |
|---|---|
| Community | **Comments** on (support and the GPL source offer point at this page) |
| Visibility | **Draft** while filling in, then **Public** |
| Custom noun ("Download", "Buy") | itch default |

## 7. Media

| Slot | File | Caption / alt text | What it is |
|---|---|---|---|
| Cover image (630×500) | `itch/cover.png` (from #10) | flowtype: offline dictation for Windows | — |
| Screenshot 1 | `itch/screens/01-dictate-in-notepad.png` | Hold Caps Lock, talk, let go: your words appear in Notepad. | **Mockup** (drawn) |
| Screenshot 2 | `itch/screens/02-tray-menu.png` | flowtype lives in the system tray. Right-click for Settings. | **Mockup** (drawn; menu labels from `flowtype.py`, icon from `tray_indicator.py`) |
| Screenshot 3 | `itch/screens/03-settings.png` | The settings window. | **Real UI**, rendered from `settings_gui.py` with Tk on Linux, so fonts and widget styling differ slightly from Windows |
| Screenshot 4 | `itch/screens/04-tray-states.png` | The tray diamond shows when it's listening and typing. | Icons drawn by the app's own code, shown enlarged |
| Theme colours | Background `#14162a`, text `#eceef5`, links/accent `#6ebeff` | — | Matches the cover |

Each image carries a small corner label saying what it is, so no one mistakes
a mockup for a real screenshot. `itch/screens/settings-render-raw.png` is the
unframed Tk capture that screenshot 3 is built from; don't upload it.

**Regenerating:** `python itch/make_screens.py itch/screens/settings-render-raw.png`
(needs Pillow). To refresh the raw settings capture on Windows, run
`venv\Scripts\python.exe flowtype.py --settings`, press Alt+PrtScn, and save
it over `settings-render-raw.png`. That also gives you a real Windows-styled
screenshot 3. When you have a real install, real captures of 1 and 2 can
replace the mockups whenever you like; it isn't needed for launch.

## 8. Where the numbers come from

- **Download size (~193 MB):** CI artifact 13295126051 is 202,324,055 bytes
  (the exe and the `.sha256` file, zipped). The installer is LZMA-compressed
  already, so the zip barely shrinks it.
- **Installed size (~600 MB, "1 GB free" requirement):** this is an
  *estimate*, because the sandbox could not download the artifact or the model.
  The pinned dependencies (faster-whisper 1.0.3, CTranslate2, PyAV,
  onnxruntime, NumPy 1.26) come to about 460 MB as installed wheels, the
  bundled `base.en` model is about 145 MB (`build/fetch_model.py`), and
  PyInstaller onedir adds roughly 20 MB of Python runtime. Windows wheels run a
  little smaller than Linux ones. The 1 GB figure leaves headroom. Your
  clean-install test (SHIPCHECK §c) will show the real number in
  Settings → Apps; change "roughly 600 MB" if it's far off.
- **RAM (~0.5 GB in use, 4 GB requirement):** an *estimate* for Whisper
  base.en, int8 on CPU (the shipped `config.json`), plus the Python runtime.
  Task Manager on the clean install will show the real figure. 4 GB is a safe
  floor for Windows 10/11 plus flowtype.
- **Windows 10/11 x64:** `installer.iss` allows only `x64compatible`. There is
  no `MinVersion`, so the installer doesn't block older Windows; "10 or 11" is
  what we support, not what's enforced (SHIPCHECK §c).
- **Price:** A$15 at about A$1.5 per US$ = US$10, the same rate TRUST-AUDIT
  uses.
- **SmartScreen and antivirus wording:** TRUST-AUDIT §1c, word for word, plus
  SHIPCHECK §b's sentence about what the hook can see.
- **Privacy:** EULA §3 and README "Privacy", plus TRUST-AUDIT §2's
  clipboard-history note.

## 9. Licence (the one open choice)

Pick one and paste it over `<LICENCE LINE…>` in §3. TRUST-AUDIT §3 lists what
else changes with each (`LICENSE`, `EULA.txt`, the installer, and which
code-signing certificate you can buy). Whichever you pick, the installer should
ship exactly one licence for flowtype's own code.

- [ ] **Option A: MIT (open source, you pay for the ready-made build)**
  > flowtype's source code is MIT-licensed and on GitHub: github.com/Aussietin/flowtype. Buying here gets you the ready-to-run installer with the speech model built in, plus updates and support, and it keeps the project going.

  Also: set the §5 link to the GitHub repo, and trim `EULA.txt` to the
  non-licence terms (TRUST-AUDIT §3 option A).

- [ ] **Option B: EULA (proprietary)**
  > flowtype is licensed, not sold. You may install and use it on computers you own or control, for personal or commercial dictation work. The full terms are in EULA.txt, shown when you install.

  Also: leave the §5 link blank, and replace the MIT `LICENSE` and stop
  installing it (TRUST-AUDIT §3 option B).
