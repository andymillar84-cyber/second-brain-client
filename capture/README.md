# Keep Instant Capture (client handoff package)

A self-contained package to put Andrew's "instant capture" Keep setup on a client's
Mac. Double-tap **Left Ctrl** → the Google Keep PWA snaps to a fullscreen, dark,
minimal new-note card → type → double-tap again → back to the previous app.

This is **install-by-hand by Andrew**. The step-by-step is in **[INSTALL.md](INSTALL.md)**.

## What's in here

| File | What it is |
|------|-----------|
| `INSTALL.md` | The guide Andrew follows on the client's Mac. Start here. |
| `init.lua` | Hammerspoon config — Keep capture hotkey only (double-tap Left Ctrl). Bundle ID is read from a file, not hardcoded. |
| `detect-bundle-id.sh` | Auto-detects the Keep PWA's bundle ID (any Chromium browser) and writes `~/.hammerspoon/keep_bundle_id.txt`. |
| `extension/manifest.json` | Minimal MV3 extension that injects the CSS. Loads unpacked in Edge or Chrome. |
| `extension/capture.css` | The minimal-capture styling. PWA-only via `@media (display-mode: standalone)`. |

## How it works (two halves)

1. **Hotkey** — Hammerspoon watches for a double-tap of Left Ctrl and toggles the Keep
   PWA into a fullscreen Space, pressing `c` to open a new note. The PWA's bundle ID is
   per-install, so `detect-bundle-id.sh` finds it and `init.lua` reads it from
   `~/.hammerspoon/keep_bundle_id.txt`.
2. **Minimal look** — the extension injects `capture.css` on keep.google.com. The CSS is
   wrapped in `@media (display-mode: standalone)`, so it **only** restyles the PWA window
   — a normal keep.google.com tab is untouched.

No Google API access, master token, or login automation is involved. The client just
signs into their own Google account in the PWA.

## Browser support

Any **Chromium** browser: Edge, Chrome, Brave, Arc. **Not Safari** (no unpacked
extensions / different PWA model) — install a Chromium browser for Keep if needed.

## Maintenance gotcha

The new-note area in `extension/capture.css` is targeted by position-based selectors
(`.RfDI4d-bN97Pc > div:nth-child(n)`). These are tuned to Keep's **current** DOM. If
Google reshuffles Keep's layout, a hidden section may reappear or the wrong block may
hide — re-inspect the page in DevTools and adjust the `nth-child` numbers. (This is the
same fragility Andrew already lives with on his own machine.)

## Source

Derived from Andrew's own setup: `~/.hammerspoon/init.lua` (full version also has a
Calendar toggle + Caps-Lock space switching, both omitted here) and
`active/keep-hotkey/capture.css` (CSS copied unchanged). The original delivers the CSS
via the Stylus extension; this package replaces that with a self-contained extension so
there's no third-party dependency on the client's machine.
