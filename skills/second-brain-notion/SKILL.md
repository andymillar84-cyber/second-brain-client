---
name: second-brain-notion
description: Step 2 of 3 — set up the NOTION half when cloning the Keep→Notion "second brain" onto a client's Mac. Use after second-brain-keep, when Andrew says "do the Notion setup", "wire the client's Notion", "point the flow at their Notion", or runs /second-brain-notion. Connects the client's Notion MCP connector, duplicates the public template into their workspace, and confirms their buckets — so the flow skills (keep-router, notion-project-skill) operate entirely on the CLIENT's own Notion. No CLI, no config file. Then hand off to second-brain-verify. NOT for creating a single project (use notion-project-skill).
---

# Second Brain — Notion Setup (Step 2 of 3)

Second of three: second-brain-keep → **second-brain-notion** → second-brain-verify. Prereq: **step 1 done** (`keep inbox` works, labels created). Run inside the **client's Claude Code**.

## How isolation works now (read this first)
The flow skills (`keep-router`, `notion-project-skill`) talk to Notion **only through the connected Notion MCP**, and resolve every database **by name at runtime**. There is **no `norg`/`notion-pp-cli` CLI and no `~/.config/freshie/config.json`**. Because the MCP is OAuth-scoped to whichever workspace the client signs into, a write **can only ever land in the client's own Notion** — isolation is structural, not a config file you have to get right. So this step is just: connect their MCP, duplicate the template, confirm buckets. No IDs to capture, no config to write.

---

## Phase 1 — Connect the client's Notion MCP (~3 min)
1. Add the **Notion MCP connector** to the client's Claude Code, signed into the **client's own Notion account/workspace** (their login, not Andrew's). This single connection is what every Notion read/write in the flow uses.
2. Confirm it's live: `notion-search` for anything and check results come back from **their** workspace.

*(No internal integration, no `ntn_` token, no `config.toml` — those were only for the old CLI path and are gone.)*

## Phase 2 — Duplicate the template (~3 min)
1. Open the **public Notion template** below in the client's browser (signed into **their** Notion) → click **Duplicate** (top-right) → choose their workspace:

   **https://paint-dugong-696.notion.site/Second-Brain-OS-Template-38250211b922815e9ef1e9582e8f5983**

   This URL is baked into the repo — it's the canonical handover link, nothing to carry over separately.
2. ⚠️ The New-Project template's inline "Project Tasks" **linked views** may not survive cross-workspace duplication. After duplicating, open a project and confirm the linked view still filters. If broken, recreate the linked view in the duplicated template.

## Phase 3 — Confirm buckets (~3 min)
The duplicated template ships with a set of **life buckets**. Light interview (no need for `process-interviewer` here):
- Show the client the template's buckets and ask: keep as-is, or **rename** any to fit their life/work?
- Don't invent a new schema unless they ask. Renames just work — buckets resolve by name at runtime.

## Phase 4 — Confirm the flow can find everything (~2 min)
No config to write — just prove find-by-name resolves cleanly in their workspace:
- `notion-search "My Task List"`, `"My Projects"`, `"My Life Buckets"` each return **exactly one** database hit (the duplicated template's). If a name returns **zero**, the duplicate didn't land / the MCP is on the wrong workspace — fix before continuing. If it returns **more than one**, note which one belongs to the Second Brain hub so the skills (and `second-brain-verify`) pick the right one.
- `notion-fetch` the **My Projects** data source and confirm `default_page_template` is present (that's the New Project template `notion-project-skill` applies).

## Next
✅ Notion side done. **→ Run `second-brain-verify`** to prove the whole flow writes to the client's data.

## Gotchas
- **Isolation is the MCP login, not a config file.** If something looks like it's writing to the wrong place, the Notion MCP is signed into the wrong workspace — re-check Phase 1, don't go hunting for IDs.
- **Name collisions:** if the client already had their own "My Projects"/"My Task List" before duplicating, find-by-name can be ambiguous — flag which one is the Second Brain template's so the skills don't pick the wrong one.
- **Linked views breaking on duplication** is the known Notion risk — verify in Phase 2.
