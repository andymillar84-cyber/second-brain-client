---
name: keep-router
description: Route labeled Google Keep notes into Notion. Use when the user says "route my notes", "process my labeled notes", "move my notes to Notion", or /keep-router. Finds archived notes with routing labels (notion task, notion new project idea, notion add to project, today, tomorrow, next 3 days), proposes placements via HTML preview pane, and executes on confirmation. Uses the bundled `keep` CLI and `norg` CLI for Notion.
---

# Keep Router

Routes archived Google Keep notes that carry routing labels into Notion. the user confirms all placements before any writes happen. (Calendar is no longer part of this flow — the user blocks his own time in Google Calendar off his Notion to-do list.)

## Prerequisites

- `keep` CLI working (same as keep-organizer)
- `norg` CLI at `~/.local/bin/norg` (Notion wrapper)
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

## The `norg` CLI

Notion wrapper at `~/.local/bin/norg`. Key commands used by this skill:

```
norg task add "<title>" [--notes "body text"] [--project "Project Name"] [--when today|tomorrow|next-3]
norg tasks [--json]
norg projects [--json]
norg project show "<name>"
norg project find "<query>"
```

**norg cannot** create project pages or append content to existing projects. For those operations, use `notion-pp-cli` (see below).

## Notion writes via `notion-pp-cli` (gap-filler)

For operations norg can't do, use **`notion-pp-cli`** (`~/printing-press/library/notion/notion-pp-cli`) — the same Notion integration norg authenticates with (configured per-machine via its `config.toml`). **Do not** use the Notion MCP connector for these writes: that connector has a known account-mismatch and may land in a stale/wrong workspace. Add `--agent` for JSON, non-interactive output.

- **`notion-pp-cli pages post --stdin`** — create a new project page under the Projects database (for `notion new project idea`). Body sets `parent` = `{"database_id":"<Projects DB id>"}` plus the title property; pass the full JSON body on stdin.
- **`notion-pp-cli blocks children patch-block <page_id> --stdin`** — append content blocks to an existing project (for `notion add to project`).
- **`notion-pp-cli notion-search "<query>"`** — fallback for finding pages/databases by name.

**Discovering IDs:** Run `norg --json projects` at the start. The output contains each project's `id` (page ID) and `parent.database_id` (Projects database ID). Cache both the database ID and the project name→page_id map for the session.

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

**`notion add to project`** — Infer which existing project by matching note content against `norg projects`. Flag with ⚠️ if ambiguous and ask the user during confirmation.

**Present proposals** via HTML review pane:
1. Build input JSON for the router review page (see Review Page below)
2. Render: `python3 ~/.claude/skills/keep-router/scripts/keep_router_page.py /tmp/keep_router_input.json`
3. Ensure `.claude/launch.json` has the **keep-router-review** entry:
   `{"name":"keep-router-review","runtimeExecutable":"python3","runtimeArgs":["-m","http.server","8767","--directory","~/.claude/skills/keep-router/review"],"port":8767}`
4. `preview_start("keep-router-review")` → serverId. `preview_screenshot` to confirm.
5. Tell the user: "Review placements in the side pane, then say **done**."
6. On "done": `preview_eval(serverId, "JSON.stringify(window.getReview())")` → decisions
7. `preview_stop(serverId)`

### 3. Execute confirmed writes

- `notion task`: `norg task add "<title>" [--notes "<body>"] [--project "<project>"]`
- `today` / `tomorrow` / `next 3 days`: `norg task add "<title>" [--notes "<body>"] [--project "<project>"] --when <today|tomorrow|next-3>`
- `notion new project idea`: `notion-pp-cli pages post --stdin` — create under the Projects database (parent = `{"database_id":"<Projects DB id>"}`)
- `notion add to project`: `notion-pp-cli blocks children patch-block <page_id> --stdin` — append a content block to the matched project page

**Inline context from the keep-organizer review** (`route_notes` / `route_project`): when a decision carries these fields — voice-dumped by the user in the keep-organizer review pane and handed off via the chained end-of-day flow — fold them into the call:
- **`route_notes`** → the `--notes` body. Append it to the original note body (`--notes "<note body>\n\n<route_notes>"`), or use it alone as the body if there's no useful original text. Applies to all `notion …` routes; for `notion new project idea` / `notion add to project` it becomes the project description / appended block content.
- **`route_project`** → `--project "<route_project>"` (only ever set for `notion task`). Takes precedence over any project inferred here; if both are absent, omit `--project`.

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
