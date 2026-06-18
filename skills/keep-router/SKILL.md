---
name: keep-router
description: Route labeled Google Keep notes into Notion. Use when the user says "route my notes", "process my labeled notes", "move my notes to Notion", or /keep-router. Finds archived notes with routing labels (notion task, notion new project idea, notion add to project, today, tomorrow, next 3 days), proposes placements via HTML preview pane, and executes on confirmation. Uses the bundled `keep` CLI for Keep and the connected Notion MCP for all Notion writes.
---

# Keep Router

Routes archived Google Keep notes that carry routing labels into Notion. the user confirms all placements before any writes happen. (Calendar is no longer part of this flow — the user blocks his own time in Google Calendar off his Notion to-do list.)

## Prerequisites

- `keep` CLI working (same as keep-organizer)
- The **Notion MCP** connector added to this Claude Code, signed into the user's own Notion workspace (set up in `second-brain-notion`)
- Routing labels exist in Keep (created by keep-organizer or manually)

## The `keep` CLI

Same CLI as keep-organizer (`~/.local/bin/keep`). Key commands for routing:

```
keep labels                     All labels (id + name)
keep find --label "<name>" --archived   Find archived notes with a specific label
keep get <note_id>              Full note content
keep add-label <note_id> <label_id>
keep remove-label <note_id> <label_id>  Strip a label from a note
keep archive <note_id>...       Archive note(s)
```

## Notion via the MCP (no CLI)

All Notion reads and writes go through the **connected Notion MCP**. There is no `norg`/`notion-pp-cli` and no `config.json` — the MCP is OAuth-scoped to the user's workspace, so writes can only land there. Resolve everything by name at the start of the run and cache it for the session:

- **My Task List** + **My Projects** data sources — `notion-search` each name (`query_type: "internal"`), take the `database` hit, keep the id (used as `data_source_id` / `collection://<id>`). *(See `notion-project-skill` for the same resolution pattern.)*
- **Project list (name → page url)** — `notion-search`/`notion-fetch` the My Projects data source; cache the project names + page URLs to infer destinations and to populate the review pane's project picker.

MCP tools this skill uses: `notion-search`, `notion-fetch`, `notion-create-pages`, `notion-update-page`. Adding a task = `notion-create-pages` into the My Task List data source (properties below). Appending to a project = `notion-update-page` with `command: "insert_content"`.

### Task properties (My Task List)

When creating a task row, set:
- **`Task`** (title) — the note title / first line.
- **`When?`** (select) — `Today` / `Tomorrow` / `Next 3 Days`, only for a timing label; omit for plain `notion task`.
- **`Project`** (relation) — JSON-array string of the project page URL, when a project is assigned.
- **`Bucket`** (relation) — match the project's bucket if a project is set; otherwise omit.
- **icon** — the grey circle `icons/circle-alternate_gray`.
- **notes body** — note body (+ any `route_notes`) go in the page `content`, not a property.

(Importance / Urgency / State are left blank here — routed tasks are quick captures; the user triages them later. `notion-project-skill` sets those when building a full project.)

## Routing Labels

Everything routes to Notion. A **timing label** (`today` / `tomorrow` / `next 3 days`) creates a task in My Task List staged via the `When?` field — it implies the "task" destination.

| Label | Destination |
|---|---|
| `notion task` | Notion → My Task List (no timing) |
| `today` | Notion → My Task List · `When? = Today` |
| `tomorrow` | Notion → My Task List · `When? = Tomorrow` |
| `next 3 days` | Notion → My Task List · `When? = Next 3 Days` |
| `notion new project idea` | Notion → Projects (new page) |
| `notion add to project` | Notion → Projects (existing) |

## Workflow

```
1. Gather: find all archived notes with routing labels
2. Propose Notion placements (HTML review pane) → the user confirms
3. Execute confirmed writes
4. Cleanup: strip routing labels from processed notes
5. Report
```

### 1. Gather

Run `keep labels` to get label IDs. Build a **label map** (name → id) for the 6 routing labels — retain this map for Step 4 cleanup. For each routing label, run `keep find --label "<name>" --archived --full`. Collect all matching notes with full text. If none found across all 6: say "Nothing to route." and stop.

Retain the full proposals array (note_id → note_text, routing_label, etc.) throughout — the review page decisions only return IDs and confirmed values, so the original note text must be joined back by `note_id` at execution time.

### 2. Propose Notion placements

For each labeled note:

**`notion task`** — Propose as a new row in My Task List, no `When?`. Title = note title or first line if untitled. Note body goes into `--notes`.

**`today` / `tomorrow` / `next 3 days`** — Same as `notion task` but staged with `When?` = Today / Tomorrow / Next 3 Days (the label sets it).

**`notion new project idea`** — Propose as a new project page. Title from note, body content as project description.

**`notion add to project`** — Infer which existing project by matching note content against the cached project list (from `notion-search`/`notion-fetch` on My Projects). Flag with ⚠️ if ambiguous and ask the user during confirmation.

**Present proposals** via HTML review pane:
1. Build input JSON for the router review page (see Review Page below)
2. Render: `python3 ~/.claude/skills/keep-router/scripts/keep_router_page.py /tmp/keep_router_input.json`
3. Ensure `.claude/launch.json` has the **keep-router-review** entry:
   `{"name":"keep-router-review","runtimeExecutable":"python3","runtimeArgs":["-m","http.server","8767","--directory","~/.claude/skills/keep-router/review"],"port":8767}`
4. `preview_start("keep-router-review")` → serverId. `preview_screenshot` to confirm.
5. Tell the user: "Review placements in the side pane, then say **done**."
6. On "done": `preview_eval(serverId, "JSON.stringify(window.getReview())")` → decisions
7. `preview_stop(serverId)`

### 3. Execute confirmed writes (Notion MCP)

- **`notion task`** — `notion-create-pages` into the My Task List data source. `Task` = title; note body (+ `route_notes`) → page `content`; `Project` relation if assigned; grey-circle icon. No `When?`.
- **`today` / `tomorrow` / `next 3 days`** — same `notion-create-pages` call, plus `"When?": "Today" | "Tomorrow" | "Next 3 Days"` (exact strings) set from the timing label.
- **`notion new project idea`** — create the project **via the `notion-project-skill` recipe** (`notion-create-pages` with the discovered `template_id` into the My Projects data source), so the "Project Tasks" linked view renders. Don't hand-roll a templateless page. Use the note title as the project name and the body/`route_notes` as the outcome.
- **`notion add to project`** — `notion-update-page` with `command: "insert_content"` on the matched project page, appending the note body (+ `route_notes`) as a paragraph block.

**Inline context from the keep-organizer review** (`route_notes` / `route_project`): when a decision carries these fields — voice-dumped by the user in the keep-organizer review pane and handed off via the chained end-of-day flow — fold them in:
- **`route_notes`** → the task/project body. Append it to the original note body (`<note body>\n\n<route_notes>`), or use it alone if there's no useful original text. Applies to all `notion …` routes; for `notion new project idea` / `notion add to project` it becomes the project outcome / appended block content.
- **`route_project`** → the `Project` relation (only ever set for `notion task`). Takes precedence over any project inferred here; if both are absent, omit the relation.

### 4. Cleanup

For every note that was successfully processed (Notion write confirmed):
- `keep remove-label <note_id> <routing_label_id>` — strip the routing label
- Leave the note archived with its topic labels intact

### 5. Report

"Routed N notes to Notion (tasks: A — today: T, tomorrow: M, next-3: D, untimed: U; projects: B). Z items skipped."

## Edge Cases

- **No notes with routing labels:** "Nothing to route." Stop.
- **Ambiguous project match:** Flag ⚠️, ask the user during confirmation.
- **Auth error (Notion):** Stop, report error, don't partial-execute.
- **Note has routing label but no actionable content:** Ask the user during confirmation.
- **Multiple routing labels on one note:** A timing label + `notion add to project` means "add to that project AND stage it"; otherwise process the most specific destination and ask if unclear. Strip all routing labels after processing.
- **Note already processed (label but content already in Notion):** Should not happen if labels are stripped on success. If it does, the user skips in review.

## Review Page

The review page script at `scripts/keep_router_page.py` renders proposals. Input JSON format:

```json
{
  "proposals": [
    {
      "note_id": "...",
      "note_title": "...",
      "note_text": "...",
      "routing_label": "notion task",
      "proposed_title": "...",
      "proposed_project": null,
      "uncertain": false
    }
  ],
  "projects": ["Project A", "Project B", ...]
}
```

Decisions JSON from `window.getReview()`:

```json
{
  "decisions": [
    {
      "note_id": "...",
      "action": "confirm" | "skip",
      "title": "...",
      "destination": "My Task List" | "New Project" | "Add to Project",
      "project": "Project Name",
      "when": "today" | "tomorrow" | "next-3" | null
    }
  ]
}
```

`when` is derived from the routing label (timing labels only); `destination` is "My Task List" for `notion task` and all timing labels. Join decisions back to the original proposals array by `note_id` to recover `note_text` and `routing_label` at execution time.
