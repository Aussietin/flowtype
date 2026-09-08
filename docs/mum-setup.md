# flowtype — setup

flowtype turns speech into typed text anywhere on your PC. Hold a key, talk,
let go — the words appear wherever your cursor is. It runs entirely on your
computer; nothing is sent anywhere.

## Install

1. Download **flowtype-setup.exe** from the family hub.
2. Double-click it. Windows may show a blue **"Windows protected your PC"** box —
   this is normal for software that isn't from the Microsoft Store. Click
   **More info**, then **Run anyway**.
3. Click through the installer. Tick **"Start flowtype automatically when I sign in"**
   if you want it always ready.
4. When it finishes, flowtype starts. Look for a small **grey diamond** in the
   system tray (bottom-right of the screen, near the clock — you may need to
   click the little `^` arrow to see it).

## Using it

- **Hold the Caps Lock key**, speak a sentence, then **let go**. A second later
  the text is typed at your cursor.
- The tray diamond changes colour while it works: **red** = listening,
  **amber** = writing it out, **grey** = ready again.
- While flowtype is running, tapping Caps Lock won't toggle capitals — it's the
  talk key now. You can change which key it uses in Settings (below).

## Settings

Right-click the tray diamond → **Settings…**. You can change the talk key, pick
a different model, and add names or words it keeps getting wrong. After you
save, choose **Restart flowtype** from the same menu for the change to apply.

## First time you talk

Windows will ask **"Allow flowtype to use your microphone?"** — click **Yes**.
If you miss it, the tray icon turns into a red **"!"** — right-click it, quit,
and reopen from the Start menu, then allow the microphone.

## Quitting / reopening

- Right-click the tray diamond → **Quit**. (**Restart flowtype** on that menu
  relaunches it without a full quit — use it after changing settings.)
- Reopen from **Start menu → flowtype**.

## If something's wrong

Tell Austin. The file `%APPDATA%\flowtype\logs\transcripts.jsonl` has a record of
what it heard, which helps with "it typed the wrong thing" reports.
