# Keep Instant Capture — Install Guide

**For Andrew to follow on the client's Mac.** ~10 minutes. Works with any Chromium
browser (Edge, Chrome, Brave, Arc). **Not Safari** — see the note at the bottom.

End result: double-tap **Left Ctrl** anywhere → Keep snaps to a fullscreen, dark,
minimal new-note card → type the thought → double-tap **Left Ctrl** → back to what
they were doing.

There are two halves: the **hotkey** (Hammerspoon) and the **minimal look** (a tiny
browser extension). Do them in order.

---

## 1. Install Hammerspoon (the hotkey engine)

```bash
brew install --cask hammerspoon
```
(No Homebrew? Download from https://www.hammerspoon.org and drag to Applications.)

- Launch Hammerspoon once.
- Grant **Accessibility**: System Settings → Privacy & Security → **Accessibility** →
  toggle **Hammerspoon** on. (Without this the hotkey can't see keypresses.)

## 2. Install Keep as a PWA (in the client's browser)

Open **keep.google.com** and **sign into the client's Google account**. Then:

- **Edge:** `⋯` menu (top-right) → **Apps** → **Install this site as an app** → Install.
- **Chrome:** click the **install icon** in the address bar (or `⋮` → Cast, save, and
  share → **Install page as app**).

A standalone "Keep" app window opens. Leave it installed; you can close the window.

## 3. Detect the PWA's bundle ID

Each PWA install gets a unique ID. This script finds it automatically and saves it
where the hotkey config expects it.

```bash
cd "<this folder>"
chmod +x detect-bundle-id.sh        # first run only
./detect-bundle-id.sh
```

Expect `✓ Wrote: ~/.hammerspoon/keep_bundle_id.txt`. If it says "No Keep PWA found",
go back to step 2 and make sure the PWA actually installed, then re-run.

## 4. Install the hotkey config

```bash
mkdir -p ~/.hammerspoon
# If ~/.hammerspoon/init.lua already exists, back it up first:
#   mv ~/.hammerspoon/init.lua ~/.hammerspoon/init.lua.bak
cp init.lua ~/.hammerspoon/init.lua
```

Reload: Hammerspoon menubar icon → **Reload Config**. You should see a
**"Hammerspoon ready · ⌃⌃ Keep"** flash. (If instead you see "bundle ID not set",
redo step 3 then reload.)

## 5. Load the minimal-look extension

- **Edge:** go to `edge://extensions` → turn on **Developer mode** (bottom-left) →
  **Load unpacked** → select the **`extension`** folder in this package.
- **Chrome:** go to `chrome://extensions` → turn on **Developer mode** (top-right) →
  **Load unpacked** → select the **`extension`** folder.

The extension only changes Keep when it's running as the **PWA** — a normal
keep.google.com browser tab stays completely normal.

## 6. Test it

1. From any app, **double-tap Left Ctrl**. Keep should fill the screen showing only a
   dark, centered new-note card (no sidebar, no top bar, no other notes).
2. Type a quick note.
3. **Double-tap Left Ctrl** again — you return to the previous app. The note is saved
   in the client's Keep.

If the card looks normal (full Keep UI) instead of minimal, the extension didn't load
— recheck step 5. If nothing happens on the double-tap, recheck Accessibility (step 1)
and that the reload showed the "ready" flash (step 4).

---

## Notes

- **Double-tap Left-Ctrl triggers Dictation (or does nothing):** macOS may bind
  *Press Control twice* to Dictation, which hijacks the double-tap. Turn it off —
  System Settings → Keyboard → **Dictation** → set the shortcut to **Off** (or rebind
  it) — then retest.
- **Re-running:** if the client ever reinstalls the Keep PWA, just re-run
  `detect-bundle-id.sh` (step 3) and Reload Config. Nothing else changes.
- **Safari:** this method needs a Chromium browser (Edge/Chrome/Brave/Arc) for the PWA
  + unpacked extension. Safari can't do it the same way — if the client is Safari-only,
  install one of those browsers for Keep, or stop before this and tell Andrew.
- **The look is tuned to Keep's current layout.** See `README.md` for the one
  maintenance gotcha if Google reshuffles Keep's UI down the track.
