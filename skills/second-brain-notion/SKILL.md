---
name: second-brain-notion
description: Step 2 of 3 — set up the NOTION half when cloning Andrew's Keep→Notion "second brain" onto a client's Mac. Use after second-brain-keep, when Andrew says "do the Notion setup", "wire the client's Notion", "point the flow at their Notion", or runs /second-brain-notion. Wires the client's Notion auth, duplicates the public template, confirms their buckets, and writes ~/.config/freshie/config.json so norg + notion-project-skill operate on the CLIENT's databases — never Andrew's. Then hand off to second-brain-verify. NOT for creating a single project (use notion-project-skill).
---

# Second Brain — Notion Setup (Step 2 of 3)

Second of three: second-brain-keep → **second-brain-notion** → second-brain-verify. Prereq: **step 1 done** (`keep inbox` works, labels created). Run inside the **client's Claude Code**.

## The one thing that must be right
`norg` ships pointed at **Andrew's** Notion database IDs. If you skip this step, the client's tasks silently write into **Andrew's** Notion. This step repoints the flow by writing the client's IDs to `~/.config/freshie/config.json`, which `norg` reads on startup (absent file → Andrew's defaults). That config file is **the entire Notion-side personalisation** — the skills themselves are never edited.

`notion-project-skill` resolves buckets **by name at runtime**, so it auto-adapts to whatever buckets exist in the client's workspace — no code change.

---

## Phase 1 — Notion auth (~4 min)
1. At notion.so/my-integrations, create an **internal integration** in the **client's** workspace; connect it to their hub page.
2. Store the `ntn_...` token in `~/.config/notion-pp-cli/config.toml` with `Notion-Version = "2025-09-03"` (this is what `norg`/`notion-pp-cli` authenticate with).
3. Add the **Notion MCP connector** to the client's Claude Code — `notion-project-skill` needs it for template-applied project creation.

## Phase 2 — Duplicate the template (~3 min)
1. Open the **public Notion template** below in the client's browser (signed into **their** Notion) → click **Duplicate** (top-right) → choose their workspace:

   **https://paint-dugong-696.notion.site/Second-Brain-OS-Template-38250211b922815e9ef1e9582e8f5983**

   This URL is baked into the repo — it's the canonical handover link, nothing to carry over separately.
2. ⚠️ The New-Project template's inline "Project Tasks" **linked views** may not survive cross-workspace duplication. After duplicating, open a project and confirm the linked view still filters. If broken, recreate the linked view in the duplicated template (or script the DBs via the API).

## Phase 3 — Confirm buckets (~3 min)
The duplicated template ships with a set of **life buckets**. Light interview (no need for `process-interviewer` here):
- Show the client the template's buckets and ask: keep as-is, or **rename** any to fit their life/work?
- Don't invent a new schema unless they ask. Renames just work — buckets resolve by name at runtime.

## Phase 4 — Read IDs → write the config (~3 min)
Read back the IDs of the **duplicated** databases (via `notion-search` / `notion-fetch` MCP against the client's workspace): the **task list**, **projects**, and **life buckets** data sources, the **New Project template** page id, and the **hub** page id. Then write:

```bash
mkdir -p ~/.config/freshie
```
```json
// ~/.config/freshie/config.json
{
  "task_ds": "<client task-list data-source id>",
  "proj_ds": "<client projects data-source id>",
  "bucket_ds": "<client life-buckets data-source id>",
  "project_template_id": "<client New Project template page id>",
  "hub_page_id": "<client hub page id>"
}
```

Now `norg` points at the client's Notion, and `notion-project-skill` uses `project_template_id` + `bucket_ds` from here when creating projects.

Quick check: `norg projects` should return the **client's** projects (likely empty/template-only), proving the repoint took.

## Next
✅ Notion side done. **→ Run `second-brain-verify`** to prove the whole flow writes to the client's data, not Andrew's.

## Gotchas
- **Wrong DB IDs = client tasks write into Andrew's Notion.** The `norg projects` check here, and the task-row check in `second-brain-verify`, are the gates.
- **`config.json` is per-machine** — it lives only on the client's Mac. Andrew's own machine has no such file and keeps using his hardcoded defaults.
- **Linked views breaking on duplication** is the known Notion risk — verify in Phase 2.
