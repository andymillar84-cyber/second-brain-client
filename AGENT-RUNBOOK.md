# AGENT RUNBOOK — read this FIRST, follow it exactly

You are a **fresh, vanilla Claude Code agent** in a **throwaway macOS user account**. You have NO
installed skills, NO MCP connectors, NO memory, and NO context beyond this repo. This is a **TEST
RUN** (dress rehearsal) of installing Andrew's "second brain" system onto a client's Mac. Your job:
replicate the system, run its setup skills, and **record everything in writing** so problems are
captured — not left to anyone's memory.

A test run that ends in *"it failed at Phase 3 with this exact error"* is a **SUCCESS**. Finding the
breakages is the whole point. Do not paper over them.

---

## Golden rules

**DO**
- Follow the phases below **in order**. After each step, append the result to the RUN-LOG (see Recording).
- Run terminal commands yourself (you have Bash) and show Andrew what you run.
- Use **only** the throwaway accounts (new Google / Notion / Claude). 
- When a step fails: **STOP**, write a debug doc, tell Andrew. Don't push past a failure.

**DO NOT**
- ❌ Do NOT improvise, "improve", refactor, or install anything beyond what this runbook names.
- ❌ Do NOT retry a failing step more than **once**. Log it and stop — retries hide the real cause.
- ❌ Do NOT guess at missing pieces. A missing file/command/account is a **FINDING** — record it.
- ❌ Do NOT touch the main user account or any path under `/Users/andrewmillar/`.
- ❌ Do NOT `git push` or modify this repo.

---

## Recording (this is half the job)

All logs go to **`/Users/Shared/sb-test-logs/`** — both macOS accounts can read it, so Andrew
reviews from his account without you handing anything over.

1. First action: `mkdir -p /Users/Shared/sb-test-logs`.
2. **`RUN-LOG.md`** — append a block after **every** step:
   ```
   ## [HH:MM] Phase N — <step name>
   - ran: <command or action>
   - result: ✅ pass / ❌ fail
   - evidence: <key output line, file created, or exact error text>
   - next: <what you're doing next>
   ```
3. **On any failure → `debug-<short-issue>.md`** with these 4 sections (Andrew's debugging protocol):
   **Known Facts** (with evidence) · **Ruled Out** · **Current Hypothesis** · **Evidence Needed**.
   Then STOP and tell Andrew.

> Get times by running `date "+%H:%M"`. Don't guess the clock.

---

## ⚠️ The restart handoff (read before Phase 3)

Skills copied into `~/.claude/skills/` are **NOT visible until Claude Code RESTARTS** — and a restart
**ends your session**. So:
- Finish Phases 1–2, **write progress to RUN-LOG**, then tell Andrew: *"restart Claude Code now."*
- The **next** session (you, after restart) must **read `/Users/Shared/sb-test-logs/RUN-LOG.md` FIRST**
  to see what's done, then resume at Phase 3. **The RUN-LOG is your memory across the restart.**

---

## Phases

**Phase 0 — Sanity.** Run `whoami` — confirm it's the throwaway account, NOT `andrewmillar`. Create the
log dir. Confirm this repo is cloned and you're inside it. Log it.

**Phase 1 — Supporting software.** Install per **README §1** (brew, python, uv, hammerspoon, a Chromium
browser). Verify each with `which`. Log each result (and any that were already present).

**Phase 2 — Copy the system files.** Do **README §2** exactly (skills → `~/.claude/skills/`, `norg` +
`notion-pp-cli` to their paths, the `keep` symlink, capture, autolabeller, PATH). Verify
`which keep norg notion-pp-cli` all resolve. Log.
→ **Then STOP. Ask Andrew to restart Claude Code.** Log the handoff line.

**Phase 3 — (after restart) Keep side.** Read RUN-LOG first. Add the **Notion MCP connector** in Claude
Code. Run **`/second-brain-keep`** (Keep auth, cookie→master token — the flakiest step; if it fails,
write `debug-keep-auth.md` and stop). Log the labels created.

**Phase 4 — Notion side.** Run **`/second-brain-notion`** (needs the published template URL — ask
Andrew). Confirm `~/.config/freshie/config.json` exists and holds the **NEW** Notion's IDs. Log.

**Phase 5 — Capture.** Do **README §3** (Keep PWA, `detect-bundle-id.sh`, load `capture/extension/`,
reload Hammerspoon). Test the double-tap-Left-Ctrl card. Log.

**Phase 6 — Auto-labeller.** Run `~/second-brain-automation/install.sh`. Confirm the launchd job loaded
and the log file is writing. Log.

**Phase 7 — ISOLATION GATE.** Run **`/second-brain-verify`**. The gate: a routed task lands in the
**NEW** Notion account and **NOTHING** in Andrew's. Log PASS/FAIL with evidence. This defines "done".

---

## Finishing (done OR stuck)

Write a final **`## SUMMARY`** block in RUN-LOG: what passed, what failed, what's unresolved, and which
debug docs you created. That summary is the deliverable of this test run — Andrew reads it from his
account and we fix from there.
