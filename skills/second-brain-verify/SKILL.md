---
name: second-brain-verify
description: Step 3 of 3 — smoke-test a freshly cloned Keep→Notion "second brain" on a client's Mac. Use after second-brain-keep + second-brain-notion, when Andrew says "verify the second brain", "smoke test the client setup", "check the clone works", or runs /second-brain-verify. Runs an end-to-end test proving the flow classifies into the client's labels and writes tasks into the CLIENT's Notion — not Andrew's — and optionally installs the auto-labeller + capture UX extras.
---

# Second Brain — Verify (Step 3 of 3)

Final of three: second-brain-keep → second-brain-notion → **second-brain-verify**. Prereqs: steps 1 and 2 done (`keep inbox` works, labels created, `~/.config/freshie/config.json` written). Run inside the **client's Claude Code**.

This step proves the clone is wired to the **client's** data, with one non-negotiable gate: a task must land in the **client's** Notion, never Andrew's.

---

## Smoke test (~10 min)
Run in order; stop and fix if any step fails.

1. **Config repoint:** `norg projects` → returns the **client's** projects (template-only/empty is fine). Proves `norg` reads their `config.json`, not Andrew's defaults.
2. **Keep classification:** create a note in the client's Google Keep → `/keep-organizer` → it files the note under one of **their** Phase-2 topic labels.
3. **🚩 The critical gate — Notion write goes to the CLIENT:** `/keep-router` on a note carrying a routing label → on confirm, a **task row appears in the CLIENT's task list** (open their Notion and confirm it's there, NOT in Andrew's). If it lands in Andrew's hub, the `config.json` IDs are wrong — fix `second-brain-notion` Phase 4 before anything else.
4. **Template-applied project:** `/notion-project-skill` once → a project page is created in the client's Notion **with the template applied** (the "Project Tasks" linked view renders). Proves `project_template_id` + DB ids come from config.
5. **Task linked to project:** confirm the project's tasks show the grey-circle icon and link back correctly.

If all five pass, the clone is live. ✅

## Optional extras (only if the client wants them)
Both are already **staged by the package's `install.sh`** — these are just the activation steps.
- **Auto-labeller** (hourly headless labelling so end-of-day is just *verify → route*): `install.sh` already staged it to `~/second-brain-automation/`. Activate: `cd ~/second-brain-automation && ./install.sh` (loads the hourly LaunchAgent with their paths). Same local master token, no API key — but it shells out to `claude` hourly, so that CLI must be installed and authed on this Mac. Their Keep already has the labels from step 1, so it works as-is. Verify: add a note, then `python3 ~/second-brain-automation/autolabel.py` (or wait one poll cycle), confirm it's labelled + logged to `~/.config/keep-autolabel/daily-*.log`.
- **Capture UX** (double-tap Left-Control → Keep PWA + minimal dark capture card): Hammerspoon `init.lua` (staged by `install.sh`) + the **MV3 browser extension**, Mac-only. Per-machine: run `capture/detect-bundle-id.sh` for the PWA bundle ID, load the unpacked extension, grant Accessibility, reload Hammerspoon. If double-Ctrl also fires macOS Dictation, turn that shortcut off (System Settings → Keyboard → Dictation). Full steps: `capture/INSTALL.md`.

## Done
The client now has: their Keep labels, the 6 routing labels, Notion wired to their own databases, and a working capture → organise → route → Notion flow. Hand them the operator notes (which skills to run when) and they're self-serve.

## Gotchas
- **Step 3 is the whole point** — never declare done until a task row is confirmed in the *client's* Notion.
- If `/keep-organizer`'s review pane doesn't open, it's only available in Claude Code (not the Desktop app) — fall back to the pop-up / clipboard flow.
- Linked view not rendering in step 4 → the template duplication dropped it; recreate per `second-brain-notion` Phase 2.
