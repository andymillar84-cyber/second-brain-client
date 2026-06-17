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
Copy over (USB / git / AirDrop): `keep_cli.py`, `norg`, `notion-pp-cli` (Mac binary — check arch), `exchange_token.py`, the flow skills (`keep-organizer`, `keep-router`, `notion-project-skill`), and the three `second-brain-*` skills. (The public Notion template URL is baked into `second-brain-notion` Phase 2 — nothing to carry over.) Sources on Andrew's machine: `keep`→`~/.claude/skills/keep-organizer/scripts/keep_cli.py`; `norg`→`~/.local/bin/norg`; `notion-pp-cli`→`~/printing-press/library/notion/notion-pp-cli`; `exchange_token.py`→`active/keep-organizer/`.

---

## Phase 0 — Install assets (~3 min)
1. Copy the flow skills + the three `second-brain-*` skills into `~/.claude/skills/`.
2. Place binaries/scripts:
   - `keep_cli.py` → `~/.claude/skills/keep-organizer/scripts/keep_cli.py`; `ln -sf` it to `~/.local/bin/keep`.
   - `norg` → `~/.local/bin/norg` (`chmod +x`).
   - `notion-pp-cli` → **`~/printing-press/library/notion/notion-pp-cli`** (this exact path — `norg` calls it there; `mkdir -p` the dirs). Confirm Mac arch; `go build` if mismatched. *(Used in step 2, but place it now.)*
   - `exchange_token.py` → anywhere handy (used in Phase 1).
3. Ensure `~/.local/bin` is on `PATH`. `uv tool install keep-mcp` (Keep MCP, for the connector).
4. Check: `keep --help` and `norg --help` both run.

## Phase 1 — Keep auth (the flakiest step) (~5 min)
Get the client's Google **master token** so `keep` can read/write their Keep:
1. In the client's Chrome, open `accounts.google.com/EmbeddedSetup`, sign in as the client, copy the `oauth_token` cookie (`oauth2_4/...`).
2. Exchange it for a master token (see `keep-organizer` SKILL.md "Token refresh", or `exchange_token.py`):
   ```bash
   GKEEP_EMAIL="<client@email>" GKEEP_OAUTH_TOKEN="oauth2_4/..." \
   uv run --no-project --with gpsoauth python3 -c '
   import os,gpsoauth
   r=gpsoauth.exchange_token(os.environ["GKEEP_EMAIL"],os.environ["GKEEP_OAUTH_TOKEN"],"0123456789abcdef")
   print(r.get("Token") or r)'
   ```
3. Write the `aas_et/...` token to `~/.config/keep-cli/token` (and into the keep-mcp env block in `~/.claude.json` if using the connector). The CLI reads it fresh each call.
4. **Verify:** `keep inbox` returns JSON (their notes), not an auth error. **Do not proceed until this passes.**

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
✅ Keep side done. **→ Run `second-brain-notion`** to wire Notion and point the flow at the client's databases.

## Gotchas
- **Master-token extraction is the flakiest step** — if `keep inbox` errors, redo Phase 1; don't push past it.
- **Don't rename the 6 routing labels** — they're hardcoded across the flow.
- **`notion-pp-cli` path is hardcoded in `norg`** — Phase 0 must place it at `~/printing-press/library/notion/notion-pp-cli` (needed in step 2).
