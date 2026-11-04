# flowtype itch ship-check

Checked 2026-10-26 against base `c75fc88` (head of PR #8, branch `buy-button-release`). Answers the open boxes in the itch page draft (`ProjectVault/Outbox/2026-10-19 itch page - flowtype.md`) and launch sheet section 2c that the code or CI can settle. Anything only a human can settle is marked **Austin**.

**Stale local build.** `C:\Users\AustinCrozier\Dev\flowtype\installer-output\flowtype-setup.exe` on this PC is a stale 23 Sep build (202,697,548 bytes, mtime Sep 23 12:20), from before the neutral glossary, EULA, notices and GPL source offer. It is NOT the release. Upload only the PR #8 CI artifact (or a rebuild from the merged commit), never this file.

## Summary

| | Item | Result |
|---|---|---|
| a | `known_terms` neutral | **Partly.** Shipped `config.json` is neutral. The code default in `config.py` is NOT, and the Settings "Reset" button inserts it. Fix before ship. |
| b | Keyboard-hook antivirus line | **Not accurate as worded.** Needs a rewording (below). |
| c | Windows / 64-bit | 64-bit confirmed. Windows 10/11 is plausible but not enforced. Clean-install test: **Austin**. |
| d | Installer size and SHA256 | Artifact 201,359,141 bytes (zip). Artifact digest below. Installer-exe SHA256: **Austin** (not in logs, no download allowed). |
| e | EULA, notices, GPL offer | Present and installed. EULA is proprietary, repo LICENSE is MIT: **Austin** to pick the wording. |
| f | transcripts.jsonl disclosed | Yes, in EULA section 3 (and README). Page text matches. |

## (a) known_terms

Grep for `Austin|Crozier|Homebush|Marwood|Clairview|Rangeview|Blue Mountain|Racecourse|RCP` (case-insensitive):

- `config.json`: no matches (grep exit 1). The list is `config.json:12-14`: flowtype, GitHub, Python, JavaScript, Windows, Wi-Fi, PDF, email. Neutral. The installer bundles this file (`flowtype.spec:17`) and seeds `%APPDATA%\flowtype\config.json` from it on first run (`config.py:76-84`).
- `config.py:38-45` `DEFAULT_KNOWN_TERMS` is personal: "ProjectVault", "T3RRA", "RCP", "Racecourse Projects", "Ops Center", "Marwood", "Blue Mountain", "Rangeview", "Clairview", "Homebush", "Mackay", "Burdekin", "Lili Dwyer", and more.
  - It is used when `known_terms` is absent from the user's config (`config.py:66`, `config.py:97-100`) or the config is unreadable (`config.py:76-93`).
  - `settings_gui.py:235` (`_reset_terms`, the Reset button on the vocabulary box) writes this list into the user's vocabulary, and from there it is saved to their config and fed to Whisper as hotwords (`flowtype.py:156`).
  - Impact: a buyer who presses Reset sees Austin's employer, sites and a person's name. The page's "neutral list" line is false for that path.
  - Fix (not in this task's owned files): replace `DEFAULT_KNOWN_TERMS` in `config.py` with the `config.json` list. `test_config.py` / `test_settings_gui.py` may need matching updates.

## (b) Keyboard hook and antivirus line

Page says: "It only listens for your chosen keys." Not accurate.

- Hotkeys use the `keyboard` package (`requirements.txt:2`, `keyboard==0.13.5`) via `keyboard.on_press_key` / `on_release_key` with `suppress=True` (`flowtype.py:328-331`), plus `on_press_key(CFG.quit_key)` for the Esc double-tap quit (`flowtype.py:343`) and `keyboard.send("ctrl+v")` to paste (`flowtype.py:209`).
- `keyboard` installs one system-wide low-level keyboard hook on Windows. That hook receives every keystroke system-wide; the library filters by key name in Python afterwards. So the process can see all keys, but the code acts only on the configured hotkeys and Esc. It does not log or store other keys (the only keyboard calls in the app are the lines above and `settings_gui.py:206-213`).
- `settings_gui.py:213` `keyboard.read_event(suppress=False)` reads the next keypress, but only while the user clicks "Detect keypress" in Settings.
- Caps Lock is suppressed (`suppress=True`), which is why caps no longer toggles. This matches the page's "Caps Lock stops toggling" line.
- Suggested wording: "flowtype uses a global keyboard hook to see the hotkey, which some antivirus tools flag. The hook can see every key press on the PC, but flowtype only acts on your hotkey and Esc, and never stores or sends other keys."
- Not tested against any antivirus. SmartScreen / AV result on the CI build: **Austin** (clean-install test).

## (c) Windows version and 64-bit

- 64-bit only: `installer.iss:27-28` `ArchitecturesAllowed=x64compatible`, `ArchitecturesInstallIn64BitMode=x64compatible`. CI builds on `windows-latest` x64 with Python 3.11.9 (`release.yml`; log "setup-python-Windows-x64-python-3.11.9").
- No `MinVersion` in `installer.iss`, and `flowtype.spec` sets none, so the installer itself does not block any specific Windows 10/11 build. Python 3.11 itself needs Windows 8.1 or later; the "Windows 10 or 11, 64-bit" page wording is a safe claim but is not enforced by the code. Per-user install, no admin: `installer.iss:18` `PrivilegesRequired=lowest`.
- Verified on a clean Windows 10/11 account: **Austin** (launch sheet gate, about 20 min). Disk space after install: **Austin** (measure at the clean install; the installer is about 200 MB compressed and the unpacked folder is larger).

## (d) Installer size and SHA256 (PR #8 CI)

Source: `gh run list -R Aussietin/flowtype --branch buy-button-release --workflow "Windows installer"` gives run `39204104382`, head SHA `c75fc889507ef04ab5b579e2983622b67f1c80da` (matches PR #8 head), conclusion success, 2026-10-19T05:21:12Z. The earlier run `39203547625` was on `2191bd2`, before the GPL notices, and is not the one to use.

`gh api repos/Aussietin/flowtype/actions/runs/39204104382/artifacts`:

| field | value |
|---|---|
| artifact id / name | 12164768584 / `flowtype-setup` |
| size_in_bytes | 201,359,141 (about 192 MiB, the zip containing the exe and the .sha256 file) |
| digest | `sha256:582b0361ea73098b0368702f9b38d9d7c5b814aafa60c3285ecb32458424ddcc` (hash of the ZIP, not of the exe) |
| expires_at | 2026-11-18T05:23:00Z (30 day retention; rebuild if it lapses) |

- The digest above is of the artifact zip. Do not paste it on the itch page as the installer's SHA256.
- The installer exe's own SHA256 is computed in the "SHA256" step (`release.yml`) and written to `flowtype-setup.exe.sha256` inside the artifact and to the job step summary only. It is not echoed in the job log (checked via `gh api repos/Aussietin/flowtype/actions/jobs/117903077220/logs`), and the REST API does not expose step summaries. Getting it needs the artifact download or the Actions run page: **Austin**. The exe size is not in the log either; it is about the artifact size (about 200 MB), matching the page's "About 200 MB".
- The download Austin uploads to itch must be the same file whose hash is on the page. Compare the `.sha256` file in the artifact with `Get-FileHash` of the uploaded exe.

## (e) EULA, notices, GPL source offer

- Installed files: `installer.iss:35-37` copies `EULA.txt`, `THIRD-PARTY-NOTICES.txt` and `LICENSE` (as `LICENSE.txt`) into `{app}`. `installer.iss:22` `LicenseFile=EULA.txt` shows the EULA at install.
- `THIRD-PARTY-NOTICES.txt`: lists x264/x265 as GPL-2.0-or-later (lines 36-42), a "Source code offer (GPL-2.0 components)" with source URLs and a written three-year offer (line 59 on), and the full GPL-2.0 text from line 79. CI appends full licence texts of bundled packages (`release.yml`, step "Append full licence texts"). CI run `39204104382` log confirms the x264 and x265 DLLs ship: `libx264-164-b33ed15d1f262a67c0da331c9f86f918.dll`, `libx265-668b2e71a6cd3b80e84445adafe9696a.dll`.
- pystray (LGPL-3.0) ships as plain `.py` files, and CI fails if not (`release.yml` "Freeze" step).
- Licence state is mixed: `LICENSE` is MIT (copyright Austin Crozier), while `EULA.txt` is "All rights reserved except as stated" with personal or commercial use on machines you own. Which one the page says: **Austin** (the page's `[DECIDE: MIT vs proprietary]`). Pick one, then align LICENSE, EULA.txt and the page; shipping both unreconciled is contradictory.
- The source offer points to the itch page or `github.com/Aussietin/flowtype/issues`. Needs the GitHub repo to accept issues, or the itch page to exist: **Austin**.
- Whether the full-licence-text section actually appears in the shipped file: not verified, since the artifact must not be downloaded. Check after downloading.

## (f) transcripts.jsonl disclosure

- Behaviour: every transcript is appended in plain text (`flowtype.py:189-200`, path `paths.py:32`: `%APPDATA%\flowtype\logs\transcripts.jsonl` when frozen).
- `EULA.txt` section 3 (Privacy) states the file name and path, that it is plain text, that anyone with access to the Windows account can read it, that it can be deleted, and that uninstall removes the logs folder.
- Uninstall: `installer.iss:47` `[UninstallDelete]` removes `{userappdata}\flowtype\logs`. Consistent with the EULA and the page.
- README line 174 also discloses it. The page's Privacy section matches.
- The log has no off switch. The page does not claim one.

## Austin-only

- Clean-account Windows install and dictation test (about 20 min); SmartScreen and antivirus behaviour; disk space after install.
- Final USD price (the page says about A$15, about US$10).
- Support email and refund wording.
- MIT vs proprietary wording; AI-assistance wording.
- Installer-exe SHA256 from the artifact (or from the rebuild you upload).
- Quick search for the older "Flowtype" web-typography project.

## Cover

`itch/cover.png`, 630x500, built with Pillow from `assets/icon.ico` and the page tagline.
