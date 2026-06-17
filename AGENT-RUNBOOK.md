# AGENT RUNBOOK — segmented test install

You are a **fresh, vanilla Claude Code agent** in a **throwaway macOS user account**. No installed
skills, no MCP connectors, no memory, no context beyond this repo. This is a **TEST RUN** of
installing Andrew's "second brain" onto a client's Mac.

The install is split into **5 segments (A–E)**. **Each segment is run by a SEPARATE fresh agent
session** so no single context gets overloaded. You are doing **ONE segment, then stopping.** The
shared `RUN-LOG.md` is how each segment hands state to the next — it is the memory none of you have.

A test run that ends in *"failed at Segment C with this exact error"* is a **SUCCESS**. Finding
breakages is the point. Don't paper over them.

---

## 🚀 KICKOFF PROMPTS (Andrew pastes these, one per session, in order)

Run each in a **new Claude Code session** in the throwaway account. Wait for one to finish and do its
hand-off action before starting the next.

**A — Foundation:**
> Test install, Segment A. Read `~/second-brain-client/AGENT-RUNBOOK.md`, follow the Golden Rules +
> Recording protocol, and do **Segment A only**. Stop at the end and tell me the hand-off action.

**B — Keep:**
> Test install, Segment B. First read `/Users/Shared/sb-test-logs/RUN-LOG.md` for state, then in
> `~/second-brain-client/AGENT-RUNBOOK.md` do **Segment B only**. Follow the Golden Rules + Recording. Stop at the end.

**C — Notion:**
> Test install, Segment C. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment C only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Stop at the end.

**D — Capture & Auto-labeller:**
> Test install, Segment D. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment D only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Stop at the end.

**E — Verify:**
> Test install, Segment E. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment E only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Write the final summary.

---

## Golden Rules

**DO** — follow your segment's steps in order · run terminal commands yourself & show Andrew · use
ONLY the throwaway accounts · on failure, STOP + write a debug doc + tell Andrew.

**DO NOT** — ❌ improvise / "improve" / install anything not named here · ❌ retry a failing step more
than once (retries hide the cause) · ❌ guess at missing pieces (a missing file/command = a FINDING,
log it) · ❌ touch the main account or any `/Users/andrewmillar/` path · ❌ `git push` or edit this repo
· ❌ run any segment other than the one you were told to.

---

## Recording (half the job)

Logs go to **`/Users/Shared/sb-test-logs/`** — both macOS accounts read it, so Andrew reviews from his.

1. First action of Segment A: `mkdir -p /Users/Shared/sb-test-logs`.
2. **`RUN-LOG.md`** — append a block after **every** step (get the time with `date "+%H:%M"`):
   ```
   ## [HH:MM] Segment X — <step>
   - ran: <command/action>     - result: ✅ / ❌
   - evidence: <key output line / file created / exact error>
   - next: <what's next>
   ```
3. **On failure → `debug-<short-issue>.md`**: **Known Facts** (w/ evidence) · **Ruled Out** ·
   **Current Hypothesis** · **Evidence Needed**. Then STOP and tell Andrew.

---

## ⚠️ The one restart (end of Segment A)

Skills copied into `~/.claude/skills/` and a newly-added Notion connector are **NOT visible until
Claude Code restarts** — which ends the session. That's *why* A and B are separate sessions: the
restart is the seam. Segment A ends by asking Andrew to add the connector + restart; Segment B is a
fresh post-restart session that reads RUN-LOG and carries on.

---

# THE SEGMENTS

## Segment A — Foundation  *(no skills needed yet)*
1. `whoami` → confirm it's the throwaway account, **not `andrewmillar`**. `mkdir -p /Users/Shared/sb-test-logs`. Log.
2. Install supporting software per **README §1**; verify each with `which`. Log each (note any already present).
3. Copy the system per **README §2** exactly; verify `which keep norg notion-pp-cli` all resolve. Log.
4. **Hand-off:** write a RUN-LOG line, then tell Andrew:
   *"Add the Notion MCP connector in Claude Code, restart it, then paste Kickoff B."* **STOP.**

## Segment B — Keep  *(post-restart)*
1. Read RUN-LOG. Confirm the skills are now visible (a `/second-brain-keep` skill exists). If not → debug doc, stop.
2. Run **`/second-brain-keep`** — Keep auth (cookie → master token, the flakiest step) + create labels.
   If the token exchange fails → `debug-keep-auth.md`, stop.
3. Log the labels created. **Hand-off:** tell Andrew to paste Kickoff C. **STOP.**

## Segment C — Notion
1. Read RUN-LOG. Confirm the Notion MCP connector tools are present. If not → debug doc, stop.
2. Run **`/second-brain-notion`** — duplicate the published template (ask Andrew for the URL) + write
   `~/.config/freshie/config.json`.
3. Verify `config.json` exists and holds the **NEW** Notion's IDs (not Andrew's). Log it. **Hand-off:** Kickoff D. **STOP.**

## Segment D — Capture & Auto-labeller
1. Read RUN-LOG. Do **README §3** capture steps (Keep PWA → `detect-bundle-id.sh` → load
   `capture/extension/` → reload Hammerspoon); test the double-tap-Left-Ctrl card. Log.
2. Run `~/second-brain-automation/install.sh`; confirm the launchd job loaded + log file writing. Log.
   **Hand-off:** Kickoff E. **STOP.**

## Segment E — Verify  *(the gate)*
1. Read RUN-LOG. Run **`/second-brain-verify`**.
2. The gate: a routed task lands in the **NEW** Notion account and **NOTHING** in Andrew's. Log PASS/FAIL + evidence.
3. Write a final **`## SUMMARY`** block in RUN-LOG: what passed, what failed, unresolved items, debug docs created.
   That summary is the deliverable — Andrew reads it from his account and we fix from there.
