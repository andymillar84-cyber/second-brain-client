# Lean Second-Brain Transfer — Test Runbook (Andrew's copy)

> **The one constraint this doc exists for:** once you log into the throwaway macOS account,
> this Claude can't follow you. The *agent* has the repo; **you** have this. Read it from your
> phone on GitHub while you run the test — it's pushed to the repo as `OPERATOR-RUNBOOK.md`:
> **https://github.com/andymillar84-cyber/second-brain-client/blob/main/OPERATOR-RUNBOOK.md**
>
> You are the conductor. The fresh agent does the mechanical work; you supply the things it
> can't — logins, consent clicks, secrets — and you watch the one gate that matters (isolation).

---

## TL;DR — what "passed" looks like

A vanilla Claude Code agent, given **only the repo**, stands up the Keep→Notion second brain in
the throwaway account. The test is GREEN when: **a routed Keep note lands in the NEW Notion, and
NOTHING lands in Andrew's Notion.** A run that dies at "Segment C, this exact error" is also a
success — finding the break is the point. You then come back to *this* account and we fix it.

This run tests the **MCP-based system**: Notion is now reached **only through the Notion MCP**, with
every database resolved **by name** — there's no `norg`/`notion-pp-cli` binary and no
`~/.config/freshie/config.json`. Isolation is structural (the MCP is OAuth-scoped to whatever Notion
account the agent connects), so a write can only land in the throwaway workspace you sign into.

---

## The map — 3 places + GitHub

| Place | Role during the test |
|---|---|
| **This account** (`andrewmillar`) | Where the system was built. **Untouched** during the test. Don't let the agent near `/Users/andrewmillar/`. |
| **Throwaway macOS account** | Pristine client stand-in. **The whole test happens here.** Fresh Claude/Google/Notion. |
| **`/Users/Shared/sb-test-logs/`** | The bridge. The agent writes `RUN-LOG.md` here, so you can read the run from *either* account. |
| **GitHub repo** | The transfer vehicle (agent clones it) **and** this runbook (you read it from your phone). |

---

## PHASE 0 — Prep from THIS account, before you go dark

Do all of this *before* you switch users. Once you're in the throwaway account you can't get it back.

- [ ] **macOS:** create the throwaway user account (System Settings → Users & Groups). Note its username (must **not** be `andrewmillar`).
- [ ] **Google:** create a throwaway Google account (this is the Keep half).
- [ ] **Notion:** create a throwaway Notion account (free).
- [ ] **Claude Code:** it's **per-user — it does NOT carry over** to the throwaway account (yours lives at `~/.local/bin/claude`). In a Terminal *in the throwaway account*, install it: `curl -fsSL https://claude.ai/install.sh | bash` (native, same as yours) — or `npm install -g @anthropic-ai/claude-code`. Then open a fresh terminal, run `claude`, and sign in (your own login is fine — the empty `~/.claude` already gives the vanilla skill environment). Confirm with `which claude`. *(Fresh = no skills/MCP/memory, which is exactly what we're testing.)*
- [x] **🔑 Notion template published — public Duplicate URL is baked into the repo.** Done. The URL is hardcoded into `second-brain-notion` Phase 2, so the agent has it directly in Segment C — no hand-over needed. For reference:
  - `PUBLIC TEMPLATE URL → https://paint-dugong-696.notion.site/Second-Brain-OS-Template-38250211b922815e9ef1e9582e8f5983`
- [x] **Repo is pushed & current** — confirmed (`main` in sync with origin, latest = guardrail flip). Nothing to do.
- [ ] **Skim this whole doc once**, plus the agent's side (`AGENT-RUNBOOK.md` in the repo) so you recognise where it stops and asks you.

---

## THE RUN — 5 segments, one fresh Claude session each

Each segment is a **separate fresh Claude Code session** (so no single context overloads). You paste
the kickoff prompt, the agent does its part and **stops**, you do the connection/consent it needs,
then start the next session. The agent reads/writes `RUN-LOG.md` to carry state across the seam.

> **Why separate sessions:** skills you copy in + a new MCP connector are **invisible until Claude
> Code restarts.** The restart at the end of Segment A *is* the seam. That's the design, not a bug.

### ▶ Segment A — Foundation *(start here; this one clones the repo)*
**You paste:**
> You're helping with a test install. Clone the public system repo, then follow its runbook:
> `git clone https://github.com/andymillar84-cyber/second-brain-client.git ~/second-brain-client`
> Then read `~/second-brain-client/AGENT-RUNBOOK.md`, follow its Golden Rules + Recording protocol,
> and do **Segment A only**. Stop at the end and tell me the hand-off action.
> *(Public repo — the clone needs no login.)*

**Agent does:** installs Homebrew/python/uv/hammerspoon/Edge, copies the skills (incl. **`process-interviewer`**, a dependency — no Notion binaries, Notion is MCP-only), and **installs the superpowers plugin** (`systematic-debugging` + skill auto-priming).
**You do at the stop:** **add the Notion MCP connector** in Claude Code, then **restart Claude Code** — this loads the skills **and** superpowers together. *(If the agent couldn't install superpowers via CLI, run `/plugin` → install **superpowers** yourself here.)*
**Watch for:** nothing auth-related — the repo's public, so the clone just works.

### ▶ Segment B — Keep *(post-restart)*
**You paste:**
> Test install, Segment B. First read `/Users/Shared/sb-test-logs/RUN-LOG.md` for state, then in
> `~/second-brain-client/AGENT-RUNBOOK.md` do **Segment B only**. Follow the Golden Rules + Recording. Stop at the end.

**Agent does:** runs `/second-brain-keep` → Keep auth + creates labels.
**🔑 You do:** supply the **Google master token** (cookie → master token — the flakiest step). It goes into the **keep-mcp env block in `~/.claude.json`** *together with* `GOOGLE_EMAIL`. The token alone, without the email, fails — don't let the agent loop on "flaky token."

### ▶ Segment C — Notion *(the connections-heavy one)*
**You paste:**
> Test install, Segment C. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment C only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Stop at the end.

**Agent does:** runs `/second-brain-notion` → connect the client's Notion MCP, duplicate template, confirm buckets.
**🔑 You do, in order:**
1. Make sure the **Notion MCP connector** (added at the Segment-A restart) is signed into the **throwaway** Notion account — that single OAuth connection is the only Notion auth there is (no integration token, no `config.toml`).
2. The **public template URL** is baked into the `second-brain-notion` skill — the agent already has it and will have you **Duplicate** it in. (Nothing to hand over.)
3. ⚠️ **Check linked views survived the duplicate.** Open a project in the duplicated template, confirm its "Project Tasks" view still filters. Cross-workspace duplication sometimes breaks them — if broken, that's a finding to log.
**The gate here:** the agent runs `notion-search "My Projects"` + `notion-fetch` — it must return the **NEW** account's database (likely empty/template-only) with a `default_page_template`. If it can't find it, the MCP is on the wrong workspace — **STOP**.

### ▶ Segment D — Capture & Auto-labeller
**You paste:**
> Test install, Segment D. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment D only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Stop at the end.

**Agent does:** installs Keep PWA, loads the capture extension, reloads Hammerspoon, loads the hourly auto-labeller (launchd).
**🖱️ You do:** the GUI consents — **Hammerspoon Accessibility** permission, **install the Keep PWA**, **"Load unpacked"** the extension. Then test the **double-tap-Left-Ctrl** capture card.

### ▶ Segment E — Verify *(the gate)*
**You paste:**
> Test install, Segment E. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` first, then do **Segment E only**
> from `~/second-brain-client/AGENT-RUNBOOK.md`. Golden Rules + Recording apply. Write the final summary.

**Agent does:** runs `/second-brain-verify` → routes a test task → checks it landed in the **NEW** Notion and **nothing** in Andrew's → writes the final `## SUMMARY` to `RUN-LOG.md`.
**That SUMMARY is the deliverable.** You read it from your account afterward and we fix from there.

---

## The connections cheat-sheet (everything the agent stops for)

| # | Connection | Where it lands | Who does it | When |
|---|---|---|---|---|
| 1 | Claude Code login (throwaway) | the app | **You** | before Segment A |
| 2 | Notion **MCP connector** (OAuth, → throwaway Notion) | Claude Code | **You** | end of Segment A (the restart) |
| 3 | **Google master token** + email | `~/.claude.json` keep-mcp env | **You** | Segment B |
| 4 | **Duplicate the template** | throwaway Notion | **You** (agent guides) | Segment C |
| 5 | GUI consents (Accessibility, PWA, unpacked ext) | macOS / browser | **You** | Segment D |

> Notion is **one** connection now (#2, the MCP) — no integration token, no `config.toml`, no
> `config.json`. The OAuth scope on that single connection *is* the isolation guarantee.

---

## Gotchas — recognise these, DON'T rabbit-hole

- **`keep inbox` fails right after writing the token** → it's almost always the **email**, not the token. `GOOGLE_MASTER_TOKEN` **and** `GOOGLE_EMAIL` must sit *together* in the keep-mcp env block in `~/.claude.json`. Don't redo auth on a loop.
- **Notion is MCP-only** — no `norg`/`notion-pp-cli` binary, no `config.json`. Don't go looking for them.
- **The hourly auto-labeller shells `claude -p`** — must work headless. If its first run logs a claude error, that's a real *finding* (note it); the rest of the system still works without the hourly layer.
- **Isolation is the MCP login.** If a write looks like it's going to the wrong place, the Notion connector is signed into the wrong workspace — re-check it, don't hunt for IDs.
- **Linked views may break on cross-workspace duplicate** (Segment C) — known Notion risk, verify it.

---

## PASS / FAIL gate

✅ **PASS:** the Segment E test task is visible in the **NEW** Notion.
❌ **FAIL (any of):** the task doesn't appear in the NEW Notion · find-by-name can't resolve the databases · the run stalls and the agent can't self-heal.

Either way the agent writes the `## SUMMARY` block to `RUN-LOG.md`. **That's what you bring back.**

---

## AFTER the test — come back to this account

1. Read `/Users/Shared/sb-test-logs/RUN-LOG.md` (+ any `debug-*.md`) from your own account.
2. We fix whatever broke — in the **repo**, never your live `~/.claude`.
3. Re-run only the segments that changed.

---

## Reference — agent-side files in the repo

- `AGENT-RUNBOOK.md` — the agent's instructions (segments, Golden Rules, recording, gotchas).
- `README.md` — what's in the repo + where each file lands.
- `OPERATOR-RUNBOOK.md` — **this doc**, for cross-account / phone reading.
