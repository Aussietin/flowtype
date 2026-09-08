"""flowtype settings — a small Tk editor for config.json.

Opened from the tray menu ("Settings…") or standalone:

    venv\\Scripts\\python.exe settings_gui.py

It edits the same config.json that config.py reads (in a frozen install that's
%APPDATA%\\flowtype\\config.json — see paths.py). Keys it doesn't know about are
left untouched on save. Nothing here is applied live: after saving, use the
tray menu's "Restart flowtype" to pick the changes up.
"""
import json
import queue
import shutil
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import keyboard

from config import DEFAULT_KNOWN_TERMS, load_config
from paths import CONFIG_PATH

MODEL_SIZES = ["tiny.en", "base.en", "small.en", "medium.en"]
# Keys with no left/right scan-code ambiguity on Windows — safe hotkey picks.
# (see config.py's docstring for why "right ctrl"/"right alt" are traps)
SUGGESTED_HOTKEYS = ["caps lock", "right shift", "scroll lock", "pause", "f13"]


def _valid_key(name: str) -> bool:
    try:
        keyboard.key_to_scan_codes(name)
        return True
    except (ValueError, KeyError):
        return False


def _load_raw() -> dict:
    """The on-disk JSON as a dict, so unknown keys survive a save. A corrupt
    file is backed up to config.json.bak rather than silently overwritten."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        try:
            shutil.copyfile(CONFIG_PATH, CONFIG_PATH.with_suffix(".json.bak"))
        except OSError:
            pass
        return {}


class SettingsWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.raw = _load_raw()
        self.cfg = load_config()  # resolved values (raw + defaults) for the form
        root.title("flowtype settings")
        root.resizable(False, False)

        frm = ttk.Frame(root, padding=12)
        frm.grid(sticky="nsew")
        row = 0

        # --- hotkeys -----------------------------------------------------
        ttk.Label(frm, text="Hold-to-talk key(s)", font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=(0, 2))
        row += 1
        ttk.Label(frm, text="Hold any of these and speak; release to paste.",
                  foreground="#666").grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        self.hotkey_list = tk.Listbox(frm, height=4, width=30, exportselection=False)
        for hk in self.cfg.hotkeys:
            self.hotkey_list.insert(tk.END, hk)
        self.hotkey_list.grid(row=row, column=0, sticky="w", pady=4)

        btns = ttk.Frame(frm)
        btns.grid(row=row, column=1, columnspan=2, sticky="w", padx=6)
        self.hotkey_entry = ttk.Combobox(btns, values=SUGGESTED_HOTKEYS, width=16)
        self.hotkey_entry.grid(row=0, column=0, columnspan=2, pady=2)
        ttk.Button(btns, text="Add", width=8, command=self._add_hotkey).grid(
            row=1, column=0, pady=2)
        ttk.Button(btns, text="Remove", width=8, command=self._remove_hotkey).grid(
            row=1, column=1, pady=2)
        self.detect_btn = ttk.Button(btns, text="Detect keypress…", width=17,
                                     command=self._detect_key)
        self.detect_btn.grid(row=2, column=0, columnspan=2, pady=2)
        row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        # --- simple fields --------------------------------------------------
        ttk.Label(frm, text="Model").grid(row=row, column=0, sticky="w")
        self.model_var = tk.StringVar(value=self.cfg.model_size)
        ttk.Combobox(frm, textvariable=self.model_var, values=MODEL_SIZES,
                     width=14, state="readonly").grid(row=row, column=1, sticky="w")
        ttk.Label(frm, text="bigger = slower, not always better",
                  foreground="#666").grid(row=row, column=2, sticky="w")
        row += 1

        ttk.Label(frm, text="Quit key (tap twice)").grid(row=row, column=0, sticky="w")
        self.quit_var = tk.StringVar(value=self.cfg.quit_key)
        ttk.Entry(frm, textvariable=self.quit_var, width=16).grid(
            row=row, column=1, sticky="w", pady=2)
        row += 1

        ttk.Label(frm, text="Max hold (seconds)").grid(row=row, column=0, sticky="w")
        self.maxrec_var = tk.IntVar(value=self.cfg.max_record_seconds)
        ttk.Spinbox(frm, from_=5, to=600, textvariable=self.maxrec_var,
                    width=14).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        ttk.Label(frm, text="Search beams").grid(row=row, column=0, sticky="w")
        self.beam_var = tk.IntVar(value=self.cfg.beam_size)
        ttk.Spinbox(frm, from_=1, to=5, textvariable=self.beam_var,
                    width=14).grid(row=row, column=1, sticky="w", pady=2)
        ttk.Label(frm, text="1 = fastest", foreground="#666").grid(
            row=row, column=2, sticky="w")
        row += 1

        self.trailing_var = tk.BooleanVar(value=self.cfg.append_trailing_space)
        ttk.Checkbutton(frm, text="Add a space after each dictation",
                        variable=self.trailing_var).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1

        self.context_var = tk.BooleanVar(value=self.cfg.condition_on_previous_text)
        ttk.Checkbutton(frm, text="Use cross-segment context (slower, rarely helps)",
                        variable=self.context_var).grid(
            row=row, column=0, columnspan=3, sticky="w", pady=2)
        row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        # --- known terms --------------------------------------------------
        ttk.Label(frm, text="Known terms (one per line)",
                  font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, columnspan=3, sticky="w")
        row += 1
        ttk.Label(frm, text="Names and jargon Whisper mishears. Keep it tight — "
                  "everyday words here cause misfires.", foreground="#666").grid(
            row=row, column=0, columnspan=3, sticky="w")
        row += 1
        self.terms_text = tk.Text(frm, height=8, width=44, wrap="none")
        self.terms_text.insert("1.0", "\n".join(self.cfg.known_terms))
        self.terms_text.grid(row=row, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Button(frm, text="Reset to defaults", command=self._reset_terms).grid(
            row=row, column=2, sticky="n", pady=4)
        row += 1

        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1

        # --- LLM cleanup -------------------------------------------------
        self.llm_var = tk.BooleanVar(value=self.cfg.llm_cleanup.enabled)
        ttk.Checkbutton(frm, text="LLM cleanup pass (needs Ollama; adds latency)",
                        variable=self.llm_var, command=self._sync_llm).grid(
            row=row, column=0, columnspan=3, sticky="w")
        row += 1
        ttk.Label(frm, text="Ollama host").grid(row=row, column=0, sticky="w")
        self.ollama_host_var = tk.StringVar(value=self.cfg.llm_cleanup.ollama_host)
        self.ollama_host_entry = ttk.Entry(frm, textvariable=self.ollama_host_var, width=28)
        self.ollama_host_entry.grid(row=row, column=1, columnspan=2, sticky="w", pady=2)
        row += 1
        ttk.Label(frm, text="Ollama model").grid(row=row, column=0, sticky="w")
        self.ollama_model_var = tk.StringVar(value=self.cfg.llm_cleanup.model)
        self.ollama_model_entry = ttk.Entry(frm, textvariable=self.ollama_model_var, width=28)
        self.ollama_model_entry.grid(row=row, column=1, columnspan=2, sticky="w", pady=2)
        row += 1
        self._sync_llm()

        # --- actions ---------------------------------------------------------
        ttk.Separator(frm, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=8)
        row += 1
        actions = ttk.Frame(frm)
        actions.grid(row=row, column=0, columnspan=3, sticky="e")
        ttk.Button(actions, text="Cancel", command=root.destroy).grid(row=0, column=0, padx=4)
        ttk.Button(actions, text="Save", command=self._save).grid(row=0, column=1, padx=4)

    # --- hotkey helpers ----------------------------------------------------
    def _add_hotkey(self):
        name = self.hotkey_entry.get().strip().lower()
        if not name:
            return
        if not _valid_key(name):
            messagebox.showerror("flowtype", f"{name!r} isn't a key name the "
                                 "keyboard library recognises.")
            return
        if name not in self.hotkey_list.get(0, tk.END):
            self.hotkey_list.insert(tk.END, name)
        self.hotkey_entry.set("")

    def _remove_hotkey(self):
        sel = self.hotkey_list.curselection()
        if sel:
            self.hotkey_list.delete(sel[0])

    def _detect_key(self):
        """Grab the next keypress on a worker thread (keyboard.read_event
        blocks), hand it back to the Tk thread through a queue."""
        self.detect_btn.config(state="disabled", text="press a key…")
        q: queue.Queue = queue.Queue()

        def worker():
            try:
                ev = keyboard.read_event(suppress=False)
                q.put(ev.name)
            except Exception as e:  # noqa: BLE001 - surface anything as a no-op
                q.put(None)

        threading.Thread(target=worker, daemon=True).start()

        def check():
            try:
                name = q.get_nowait()
            except queue.Empty:
                self.root.after(80, check)
                return
            self.detect_btn.config(state="normal", text="Detect keypress…")
            if name and _valid_key(name):
                self.hotkey_entry.set(name)

        self.root.after(80, check)

    # --- other helpers ---------------------------------------------------
    def _reset_terms(self):
        self.terms_text.delete("1.0", tk.END)
        self.terms_text.insert("1.0", "\n".join(DEFAULT_KNOWN_TERMS))

    def _sync_llm(self):
        state = "normal" if self.llm_var.get() else "disabled"
        self.ollama_host_entry.config(state=state)
        self.ollama_model_entry.config(state=state)

    # --- save --------------------------------------------------------------
    def _save(self):
        hotkeys = list(self.hotkey_list.get(0, tk.END))
        if not hotkeys:
            messagebox.showerror("flowtype", "Add at least one hold-to-talk key.")
            return
        quit_key = self.quit_var.get().strip().lower()
        if not _valid_key(quit_key):
            messagebox.showerror("flowtype", f"Quit key {quit_key!r} isn't recognised.")
            return

        terms = [t.strip() for t in self.terms_text.get("1.0", tk.END).splitlines()
                 if t.strip()]

        self.raw.update({
            "hotkeys": hotkeys,
            "quit_key": quit_key,
            "model_size": self.model_var.get(),
            "max_record_seconds": int(self.maxrec_var.get()),
            "beam_size": int(self.beam_var.get()),
            "condition_on_previous_text": bool(self.context_var.get()),
            "append_trailing_space": bool(self.trailing_var.get()),
            "known_terms": terms,
        })
        self.raw.pop("hotkey", None)  # drop the legacy singular key if present

        llm = dict(self.raw.get("llm_cleanup") or {})
        llm.update({
            "enabled": bool(self.llm_var.get()),
            "ollama_host": self.ollama_host_var.get().strip(),
            "model": self.ollama_model_var.get().strip(),
        })
        llm.pop("known_terms", None)  # glossary is top-level now
        self.raw["llm_cleanup"] = llm

        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(self.raw, indent=2, ensure_ascii=False),
                                   encoding="utf-8")
        except OSError as e:
            messagebox.showerror("flowtype", f"Couldn't write config.json:\n{e}")
            return

        messagebox.showinfo(
            "flowtype",
            "Settings saved.\n\nRight-click the flowtype tray icon and choose "
            "“Restart flowtype” to apply them.")
        self.root.destroy()


def main():
    root = tk.Tk()
    SettingsWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
