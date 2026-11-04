# Trust and AV audit — flowtype 1.0.0

Checked 2026-11-04 against the release stack (#8 `buy-button-release` → #11
`orch/revenue/b3-20261026-flowtype-terms`). This branch is cut from #11's head.
#10 (`docs/SHIPCHECK.md` + `itch/cover.png`) is a sibling of #11, not its
parent, so it is **not** in this branch. Neither touches the same files, so the
merge order doesn't matter.

Question: will Windows Defender or SmartScreen put buyers off, and what is the
cheapest fix?

## Short answer

- **SmartScreen:** yes, every buyer sees it. An unsigned, newly built
  `flowtype-setup.exe` has no reputation, so Windows shows "Windows protected
  your PC" and the buyer has to click *More info → Run anyway*. Nothing free
  removes that. Signing removes "Unknown publisher" and lets reputation build,
  but a new certificate can still trigger the warning for the first weeks.
  EV certificates [no longer skip this step][ms-ev].
- **Defender / other AV detections:** moderate risk. A low-level keyboard
  hook, synthetic Ctrl+V, clipboard reads, and the stock PyInstaller bootloader
  together match the profile of a keylogger or clipboard stealer. Expect an
  occasional heuristic hit (`Wacatac`, `Kepavll!rfn` and similar ML labels),
  most likely on a new build before Microsoft has seen it.
- **Cheapest path, in order:**
  1. Free fixes in this PR: version resource, UPX pinned off, AppMutex,
     full uninstall cleanup, HF offline guard, CI checks.
  2. Free, about 15 minutes per release: submit each release's
     `flowtype-setup.exe` to the Defender developer portal before posting it.
  3. Free: put SmartScreen and "why it needs a keyboard hook" copy on the itch
     page, next to the SHA256.
  4. Paid, when sales justify it: a Certum individual code-signing certificate
     (cloud/SimplySign). About €49–69/yr for the Open Source variant, which only
     fits licence option A below. About US$99–115/yr for the standard variant
     through resellers, or about US$249 direct. Azure Artifact Signing
     (US$9.99/mo) is **not open to Australian individuals**.

## 1. Antivirus false-positive risk

What heuristics see, roughly worst first. *Cost* means Austin's time or money.

| # | Signal in flowtype | Where | Mitigation | Cost | Status |
|---|---|---|---|---|---|
| 1 | **Global low-level keyboard hook** (`keyboard` → `SetWindowsHookEx(WH_KEYBOARD_LL)`), sees every keystroke, `suppress=True` on Caps Lock | `flowtype.py` `main()` | Can't drop it: hold-to-talk needs key-up events, and `RegisterHotKey` only gives key-down. Disclose it plainly (itch page and EULA), sign the build, and submit it to Defender. | Free (copy) | Copy suggested below |
| 2 | **Synthetic input + clipboard read/write**: reads the clipboard, writes the transcript, `SendInput` Ctrl+V, writes the old contents back | `flowtype.py` `_paste()` | Same as #1. Longer term, see the clipboard-history item in §2. | Free | Disclose |
| 3 | **Stock PyInstaller bootloader.** Thousands of malware samples share the same prebuilt `run.exe` stub, so ML/similarity engines mark it down | `flowtype.spec` | Build the bootloader from source in CI (`PYINSTALLER_COMPILE_BOOTLOADER=1 pip install --no-binary pyinstaller pyinstaller==6.22.3`; windows-latest has MSVC). That changes the stub's bytes and hash. | Free, ~1–2 h plus a CI retest | **Not done**: changes the build, wants its own test run |
| 4 | **Unsigned exe and unsigned installer/uninstaller** | `installer.iss` | Code-signing certificate (see §1b). `SignTool=`/`SignedUninstaller=yes` lines are staged, commented out, in `installer.iss`. | US$~100–250/yr | Staged |
| 5 | **No version resource**: blank Company/Product/Version under Properties → Details | `flowtype.spec`, `installer.iss` | `build/version_info.txt` on `flowtype.exe`; `VersionInfo*` directives on `flowtype-setup.exe`; `test_version.py` keeps them in step with `AppVersion`; CI fails if the exe metadata is blank | Free | **Done** |
| 6 | **UPX packing** | `flowtype.spec` | Already off (PyInstaller 6 defaults `upx=False`). Now pinned on `EXE` and `COLLECT`, and CI fails if any `UPX0`/`UPX!` header shows up in the freeze. | Free | **Done** |
| 7 | **Network-capable code bundled with a hook** (`requests`, `huggingface_hub`). A static scanner sees "keyboard hook + clipboard + HTTP", which is an info-stealer shape. | faster-whisper imports both | Can't strip them cleanly (faster-whisper imports `huggingface_hub` at module load). The frozen build now forces `HF_HUB_OFFLINE=1`, which helps privacy but won't change a static scan. | — | Partial |
| 8 | **Opt-in Startup shortcut** (persistence) | `installer.iss` `[Tasks]` | Already the low-key version: a shortcut in the user's Startup folder, opt-in and unticked by default, no `Run` registry key, no scheduled task. | — | OK as is |
| 9 | **Writes to `%APPDATA%`** | `paths.py` | Normal for any per-user app; heuristics don't care about this alone. No `%TEMP%` extraction, because the build is onedir rather than onefile, which is the right choice for AV. | — | OK as is |
| 10 | **Re-spawns itself** (`--settings`, restart) | `flowtype.py` | Benign, and runs the same signed exe once it's signed. | — | OK as is |
| 11 | **Manifest / UAC** | PyInstaller default | PyInstaller embeds an `asInvoker` manifest, and the installer is `PrivilegesRequired=lowest`, so there's no UAC prompt and no elevation. That's the low-suspicion setup already. | — | OK as is |

### 1a. Defender false-positive portal (free, every release)

- Go to <https://www.microsoft.com/en-us/wdsi/filesubmission> (short link
  `aka.ms/wdsi`) and sign in with a Microsoft account. Choose **Software
  developer** and **Incorrectly detected as malware/malicious**. Upload
  `flowtype-setup.exe`, and also a zip of `build\dist\flowtype\` if
  `flowtype.exe` itself is flagged. The portal has a size cap (users report
  around 500 MB), so check the installer's size first.
- Do it **before** posting each new build. A fresh hash is when Defender's
  cloud ML is least sure about the file.
- This only fixes **detections**. It does not stop the SmartScreen
  "unrecognised app" prompt, which comes from reputation, not detection.
  Expect replies in hours to days ([Microsoft guidance][ms-fp]).
- **VirusTotal:** a hash lookup is fine. Uploading the file shares the paid
  binary with every vendor and VT premium user, so treat that as Austin's
  call, not a default.

### 1b. Code signing for an Australian solo seller (checked 2026-11-04)

Some vendor pages (`shop.certum.eu`, `learn.microsoft.com`) were not reachable
from the audit session. The prices below come from search results that quote
those pages, so re-check them on the vendor site before buying. AUD figures
assume about A$1.5 per US$.

| Route | Price | Fits Austin? | Notes |
|---|---|---|---|
| **Azure Artifact Signing** (formerly Trusted Signing) | US$9.99/mo Basic ([pricing][az-price]) | **No, not as an individual.** Microsoft's quickstart limits individual public-trust identities to the US and Canada ([quickstart][az-qs], [Q&A][az-qa]). Australian *organisations* are listed. | Cheapest and best if Austin ever trades through a registered business entity that passes org validation. Check the org history requirements first. |
| **Certum Open Source Code Signing** (cloud, SimplySign) | ~€49–69/yr + VAT ([Certum OSS][certum-oss]) | **Only with licence option A.** Issued to natural persons for a public open-source project. The certificate reads "Open Source Developer, Austin Crozier". | Cheapest real certificate. Using it to sign a proprietary, all-rights-reserved build would misrepresent the project. |
| **Certum Standard Code Signing**, individual, cloud | ~US$99–115/yr via resellers; ~US$249 direct ([summary][certum-std]) | Yes | Cheapest route under licence option B. SimplySign is a cloud HSM plus a phone app, so there's no USB token to buy, but signing needs the phone. Hard to use from CI. |
| SSL.com OV | US$129/yr + eSigner cloud ~US$180/yr (or a token) | Yes | ~US$300+/yr all-in. Easier to use from CI. |
| Sectigo OV (reseller) | ~US$219–226/yr | Yes | Pricier than Certum for the same SmartScreen result. |
| EV (any CA) | US$300–600+/yr | Not worth it | EV [lost its instant SmartScreen reputation in 2024][ms-ev]. |

Also note: since March 2026 the CA/B Forum caps code-signing certificates at
about 460 days, so plan on yearly renewals. SmartScreen reputation carries over
best when renewals keep the same subject name.

**Is it worth it at A$15?** A ~US$100/yr certificate is about A$150, which is
about 10–12 sales a year after itch's cut. Until sales are steady, the free
steps in §1/§1a plus clear itch copy cover most of the trust gap. Signing
mainly changes the dialog from "Unknown publisher" to "Austin Crozier"; it does
not make the dialog go away on day one.

### 1c. Suggested itch page copy (free)

> **Windows will warn you the first time.** flowtype isn't code-signed yet, so
> SmartScreen says "Windows protected your PC". Click **More info → Run
> anyway**. The SHA256 below lets you confirm the file is the one I uploaded.
>
> **Why antivirus may look twice:** hold-to-talk needs to see when you press
> and release your hotkey, so flowtype installs a keyboard hook. It pastes
> your words by putting them on the clipboard and pressing Ctrl+V for you.
> Those are the same Windows features keyloggers use. flowtype makes no
> network connections at all. Windows also shows the microphone-in-use
> indicator the whole time flowtype is running, because it keeps the mic open
> so your first word isn't clipped; it only keeps audio while you hold the key.

## 2. Privacy and security

### Audio and transcripts stay on the machine (verified in code)

Grepped every shipped `.py` for `requests`, `urllib`, `socket`, `http`,
`huggingface`, `download`, `webbrowser`, `telemetry`, `subprocess`:

- **The only network call is `llm_cleanup.clean_up()`**, a `requests.post` to
  `cfg.ollama_host`. It's gated on `llm_cleanup.enabled`, which defaults to
  `false` in both `config.json` and `config.py`. When the user turns it on,
  the transcript goes to whatever host they typed, over plain HTTP. The
  default is `localhost`, but nothing stops a remote host. *Follow-up:* have
  Settings warn when the host isn't loopback.
- **Whisper model:** the frozen build passes `paths.MODEL_DIR` (the bundled
  `base.en` directory) to `WhisperModel`. faster-whisper 1.0.3 takes the
  `os.path.isdir` branch and never calls `snapshot_download`. **New in this
  PR:** the frozen build sets `HF_HUB_OFFLINE=1` and
  `HF_HUB_DISABLE_TELEMETRY=1` before faster-whisper is imported, so even a
  missing model can't trigger a download. Running from source still downloads
  once from Hugging Face, which the README already says.
  - Side finding (UX, not privacy): Settings offers
    tiny/base/small/medium, but the frozen build always loads the bundled
    `base.en`, so changing the model in an installed copy does nothing.
    Worth hiding that field when frozen, after launch.
- `subprocess.Popen` only relaunches `flowtype.exe` itself (settings window,
  restart). No other process, browser or updater.
- **Audio** never touches disk. Frames are kept in memory only while
  `_recording` is true, concatenated, transcribed and dropped.

### What *can* leave the machine, outside flowtype's code: the clipboard

`_paste()` puts every transcript on the system clipboard. If the buyer has
**clipboard history** (Win+V) on, each dictation is stored there. If they also
have **"Sync across your devices"** on, Windows uploads it to Microsoft's cloud
clipboard. The restore step also re-copies the buyer's previous clipboard
content. If that was a password from a password manager, the re-copy drops the
manager's "exclude from history" flag, so the password ends up in history or
cloud sync, and the manager's auto-clear may stop working.

*Fix (not in this PR, because it needs testing on Windows):* replace
`pyperclip.copy` with a ~40-line ctypes writer that also sets the
`ExcludeClipboardContentFromMonitorProcessing`, `CanIncludeInClipboardHistory=0`
and `CanUploadToCloudClipboard=0` formats. Until then, the EULA/README privacy
line "does not upload audio or text" is true of flowtype's own code, but a
sentence about clipboard history would make it airtight.

### Microphone

The input stream stays open for the app's whole lifetime (a deliberate fix for
clipped first words, documented in `_open_persistent_stream`). The callback
throws away every buffer unless the hotkey is held. Buyers will still see
Windows' mic-in-use indicator all the time, which reads as "always listening".
The EULA wording "records audio only while you hold the hotkey" is accurate
about what's kept. Say why the indicator stays on (itch copy above).

### Logs folder and what's stored in plain text

| File | Contents | Protection |
|---|---|---|
| `%APPDATA%\flowtype\logs\transcripts.jsonl` | Every dictation: UTC timestamp and text, forever, no rotation | Plain text. Inherits the user-profile ACL (the user, SYSTEM and Administrators get full control; other standard users get no access). Any process running as the user can read it, and so can admins and backups. In domain environments Roaming AppData follows the user to other machines. |
| `%APPDATA%\flowtype\config.json` | Hotkeys, glossary (`known_terms`, which may hold personal names), Ollama host | Same ACL. No secrets or credentials. |

No other on-disk state: the windowed build sends stdout/stderr to `devnull`
(there's no debug log), and it doesn't use the HF cache.
The ACL is the Windows default for `%APPDATA%` (nothing in `paths.py` changes
it). Austin can confirm on a real install with `icacls "%APPDATA%\flowtype"`.

*Follow-up worth considering (product call):* a `save_transcripts` setting,
possibly off by default for a privacy-first product. The current log is a
holdover from when this was a personal tool ("raw material for SOPs").

### Uninstall

Before this PR the uninstaller removed the install dir, the Start Menu entry,
the Startup shortcut (an `[Icons]` entry, so Inno removes it automatically)
and `%APPDATA%\flowtype\logs`. It left behind:

- `%APPDATA%\flowtype\config.json`, plus the folder itself.
- A **running** flowtype. Its exe and DLLs are locked, so the uninstall
  couldn't remove them, and the keyboard hook stayed live until sign-out.

**Fixed here:**

- `[UninstallDelete]` now removes all of `%APPDATA%\flowtype`.
- `AppMutex=Global\flowtype_singleton` (the mutex flowtype already holds)
  makes setup and the uninstaller ask the user to quit flowtype first.
- The EULA §3, README Privacy section and the verification checklist in
  `docs/build-installer.md` now say the same thing.

There are no registry writes beyond Inno's own uninstall key, which the
uninstaller removes.

## 3. Licence conflict: MIT `LICENSE` vs proprietary `EULA.txt`

Today the installer copies `LICENSE` → `LICENSE.txt` (MIT: anyone may copy,
modify and **sell** the software) into the same folder as `EULA.txt`
("All rights reserved except as stated below"; use only on computers you own
or control). A buyer can't tell which one applies to flowtype's own code, and
the MIT grant covers anything the EULA tries to restrict. This audit doesn't
pick one; the choice is Austin's. Not legal advice.

**Option A: stay MIT (open source, paid for convenience)**

- *Public repo:* stays public under MIT. Anyone may build flowtype, and may
  legally resell it.
- *itch build:* buyers pay for the ready-made installer, the bundled model,
  updates and support, not for exclusive rights. Fits "pay what you want with
  a minimum", or an "it's open source, buying supports it" pitch.
- *Docs to change:* cut `EULA.txt` down to non-licence terms (privacy,
  no-warranty, ACL, unsigned-installer note), drop "All rights reserved" and
  the clause 1 restriction, and present `LICENSE` as *the* licence for
  flowtype's code.
- *Signing:* qualifies for the cheap Certum Open Source certificate (§1b).

**Option B: proprietary (paid app, rights reserved)**

- *Public repo:* replace `LICENSE` with an all-rights-reserved notice (or a
  source-available licence such as PolyForm Strict/Noncommercial), and stop
  installing the MIT text. Either make the repo private, or keep it public
  knowing anyone can still build it for free.
- *Already-published commits:* anything already published stays MIT for
  anyone who copied it. A relicence only applies from that point forward.
- *CI cost if private:* private repos pay GitHub Actions minutes, and Windows
  runners count double against the free quota.
- *itch build:* the EULA as written becomes accurate. Third-party obligations
  stay the same either way (LGPL pystray as loose `.py` files, the GPL
  x264/x265 notice and source offer from #8).
- *Signing:* needs a standard (non-OSS) certificate.

Either way, the shipped installer should carry exactly one licence for
flowtype's own code.

## Changes in this PR

- `build/version_info.txt` (new) wired into `flowtype.spec`, plus `upx=False`
  on `EXE` and `COLLECT`.
- `installer.iss`: `VersionInfo*`/`AppCopyright`, `AppMutex`, commented
  `SignTool`/`SignedUninstaller` lines, and full `%APPDATA%\flowtype` removal
  on uninstall.
- `flowtype.py`: `HF_HUB_OFFLINE=1` and `HF_HUB_DISABLE_TELEMETRY=1` in the
  frozen build.
- `.github/workflows/release.yml`: fail if `flowtype.exe` has no version
  resource or any frozen binary is UPX-packed; write both exes' metadata to the
  job summary.
- `test_version.py` (new): installer and exe versions must match; the spec
  must keep the version resource and must not use UPX.
- EULA §3, README Privacy and `docs/build-installer.md` checklist synced to the
  new uninstall behaviour.

## Not done (needs a decision, Windows testing, or money)

- Rebuild the PyInstaller bootloader from source (§1 #3).
- Clipboard-history/cloud exclusion formats (§2).
- `save_transcripts` toggle; Settings warning for a non-loopback Ollama host;
  hide the model picker in the frozen build.
- Buying a certificate; Defender submission (each needs Austin's account).
- The licence choice (§3).

[ms-ev]: https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation
[ms-fp]: https://learn.microsoft.com/en-us/defender-endpoint/defender-endpoint-false-positives-negatives
[az-price]: https://azure.microsoft.com/en-au/pricing/details/artifact-signing/
[az-qs]: https://learn.microsoft.com/en-us/azure/artifact-signing/quickstart
[az-qa]: https://learn.microsoft.com/en-us/answers/questions/6055327/azure-artifact-signing-for-international-applicant
[certum-oss]: https://shop.certum.eu/open-source-code-signing.html
[certum-std]: https://my-ssl.com/learn/code-signing-certificate-price
