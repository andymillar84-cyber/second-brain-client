---
name: second-brain-keep
description: Step 1 of 3 — set up the GOOGLE KEEP half when cloning Andrew's Keep→Notion "second brain" onto a client's Mac. Use when Andrew says "set up the second brain for a client", "onboard <name> to the Keep system", "clone my second brain", "do the Keep setup", or runs /second-brain-keep. Installs the flow assets, wires the client's Keep auth (cookie → master token), interviews the client for THEIR topic labels, and creates those labels (plus the 6 routing labels) in their Keep. Then hand off to second-brain-notion. NOT for organising an existing inbox (use keep-organizer).
---

# Second Brain — Keep Setup (Step 1 of 3)

First of three: **second-brain-keep → second-brain-notion → second-brain-verify.** Run inside the **client's Claude Code** on their Mac. Andrew drives; the client answers questions and pastes tokens.

This step installs the shared flow + stands up the client's **Keep** side. The flow skills are **already client-agnostic** — `keep-organizer`/`keep-router` classify by reading labels **live** from whatever Keep account they point at. So the whole Keep-side personalisation is: get auth working, then create the client's labels in their Keep.

## Routing labels are infrastructure — never rename
These 6 are hardcoded in `keep-organizer`, `keep-router`, and `autolabel.py`. Create them **exactly** as-is; the interview personalises **topic labels only** (buckets come in step 2).

```
notion task · today · tomorrow · next 3 days · notion new project idea · notion add to project
```

## Handover folder (Andrew brings to the client's Mac)
Copy over (USB / git / AirDrop): `keep_cli.py`, `exchange_token.py`, the flow skills (`keep-organizer`, `keep-router`, `notion-project-skill`), and the three `second-brain-*` skills. **Notion needs no binaries** — it runs entirely through the client's Notion MCP connector (set up in `second-brain-notion`). (The public Notion template URL is baked into `second-brain-notion` Phase 2 — nothing to carry over.) Sources on Andrew's machine: `keep`→`~/.claude/skills/keep-organizer/scripts/keep_cli.py`; `exchange_token.py`→`active/keep-organizer/`.

---

## Phase 0 — Install assets (~3 min)
1. Copy the flow skills + the three `second-brain-*` skills into `~/.claude/skills/`.
2. Place scripts:
   - `keep_cli.py` → `~/.claude/skills/keep-organizer/scripts/keep_cli.py`; `ln -sf` it to `~/.local/bin/keep`.
   - `exchange_token.py` → anywhere handy (used in Phase 1).
   *(No Notion binaries — Notion is MCP-only, wired in `second-brain-notion`.)*
3. Ensure `~/.local/bin` is on `PATH`. `uv tool install keep-mcp` (Keep MCP, for the connector).
4. Check: `keep --help` runs.

## Phase 1 — Keep auth (the flakiest step) (~5 min)
Get the client's Google **master token** so `keep` can read/write their Keep.

> ⏱️ **Why this is flaky — and how to beat it.** The `oauth_token` cookie (`oauth2_4/…`) is a **single-use, short-lived authorization code**. It gets "denied" during setup for three reasons, all about handling — not a bad account:
> 1. **Latency** — you grab the cookie, then fumble windows/pasting, and by the time the exchange runs it has **expired** (the window is ~1–2 min).
> 2. **Reuse** — once exchanged (or once Google's own flow consumes it), the **same value can never be exchanged again**; retrying it always denies.
> 3. **Partial copy** — the value got truncated or URL-mangled.
>
> **So do this:** stage the exchange command **first** (email filled in, cursor ready), **then** grab a **fresh** cookie and exchange it within seconds. **One cookie = one attempt** — if it denies, don't retry the same value: **reload `EmbeddedSetup` to mint a new cookie** and exchange that.

1. **Stage the command first.** Paste this into the terminal with the client's email filled in, but **don't run it yet** — leave the cursor after `GKEEP_OAUTH_TOKEN="` ready to drop the token in:
   ```bash
   GKEEP_EMAIL="<client@email>" GKEEP_OAUTH_TOKEN="oauth2_4/..." \
   uv run --no-project --with gpsoauth python3 -c '
   import os,gpsoauth
   r=gpsoauth.exchange_token(os.environ["GKEEP_EMAIL"],os.environ["GKEEP_OAUTH_TOKEN"],"0123456789abcdef")
   print(r.get("Token") or r)'
   ```
2. **Grab a fresh cookie, then run immediately.** In the client's Chrome, open `accounts.google.com/EmbeddedSetup`, sign in as the client, copy the **full** `oauth_token` cookie value (`oauth2_4/…`), paste it into the staged command, and **run it now** — minimise the gap.
3. **If it denies / `Token` not in the response:** the cookie's spent. **Reload `EmbeddedSetup`** to get a fresh `oauth_token` and retry step 2 — never re-paste the old value.
4. On success, write the `aas_et/...` token to `~/.config/keep-cli/token` (and into the keep-mcp env block in `~/.claude.json` if using the connector — alongside `GKEEP_EMAIL`, or `keep inbox` fails *looking like* a bad token). The CLI reads it fresh each call.
5. **Verify:** `keep inbox` returns JSON (their notes), not an auth error. **Do not proceed until this passes.**

## Phase 2 — Interview the client for topic labels (~8 min) — blend `process-interviewer`
Invoke `process-interviewer` for the questioning discipline, scoped to ONE thing: their **topic-label vocabulary**. One question at a time, plain language:

- "What broad areas of life and work do you capture notes about?" Help them land on **6–12 topic labels**.
- Let them choose their own convention — Andrew uses `[01] Name`, `[07] Youtube`; a client may prefer plain `Health`, `Clients`, `Ideas`. Both work (classification is content/exemplar-based, not name-based).
- Optionally capture a one-line "what goes here" per label to read back for confirmation.

Read back the final list and get a **yes** before creating anything.

## Phase 3 — Create the labels in their Keep (~2 min)
Idempotent — check `keep labels` first, skip any that already exist:
```bash
keep labels                          # what already exists
keep create-label "<topic label>"     # one per Phase-2 topic label
keep create-label "notion task"; keep create-label "today"; keep create-label "tomorrow"
keep create-label "next 3 days"; keep create-label "notion new project idea"; keep create-label "notion add to project"
```
Confirm with `keep labels` — their Keep now carries their topic labels + the 6 routing labels. `keep-organizer`/`autolabel` will classify into these with zero code change.

## Next
✅ Keep side done. **→ Run `second-brain-notion`** to connect the client's Notion MCP and duplicate the template.

## Gotchas
- **Master-token extraction is the flakiest step.** The `oauth_token` cookie is single-use and expires in ~1–2 min — stage the exchange command first, grab a **fresh** cookie, run within seconds, and if it denies reload `EmbeddedSetup` for a new cookie rather than retrying the spent one (full detail in Phase 1). If `keep inbox` still errors, redo Phase 1; don't push past it.
- **`keep inbox` failing can be a missing email, not a bad token** — the keep-mcp env block in `~/.claude.json` needs `GKEEP_EMAIL` set alongside the token.
- **Don't rename the 6 routing labels** — they're hardcoded across the flow.
