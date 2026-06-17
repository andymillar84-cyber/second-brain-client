---
name: keep-organizer
description: Organise the user's Google Keep inbox. Use when he says "organise/process my Keep", "clean up my notes", "label my Keep inbox", "sort my notes", or /keep-organizer. Lists inbox notes (not pinned, not archived), suggests a label for each by matching the notes already under each label, lets him confirm/correct/delete (HTML review pane for big inboxes, pop-up for small), then labels + archives in one pass. Uses the bundled `keep` CLI.
---

# Keep Organizer

Automates the user's end-of-day filing: label each inbox note (or make a new label), then archive it. From his pinned HOW TO note.

## The `keep` CLI

All Keep access goes through `scripts/keep_cli.py`, symlinked as **`keep`** (`~/.local/bin/keep`). gkeepapi via `uv`. Fallback: `python3 ~/.claude/skills/keep-organizer/scripts/keep_cli.py <args>`. Auth reuses the master token (`$GOOGLE_MASTER_TOKEN` → `~/.config/keep-cli/token` → keep-mcp env in `~/.claude.json`). All output is JSON.

```
keep inbox                      Notes NOT pinned AND NOT archived  ← the work queue
keep labels                     All labels (id + name)
keep profiles                   Per-label exemplars (title+snippet of existing notes) for classification
keep add-label <note_id> <label_id>
keep remove-label <note_id> <label_id>
keep create-label "<name>"      (returns id)
keep archive <note_id>...       Archive note(s)
keep trash <note_id>...         Trash note(s) — recoverable in Keep trash
keep get <note_id>              Full note
keep find [--label "<name>"] [--archived] [--full]
```

Review page generator (for big inboxes): `python3 ~/.claude/skills/keep-organizer/scripts/keep_review_page.py <input.json>` → writes `review/index.html`.

## Key facts (don't re-derive)
- **Inbox = `keep inbox`** = not pinned AND not archived. That list IS the work queue. Pinned notes are permanent quick-reference — never touch them. Already-archived notes are out of scope.
- **Filing = add label → archive** (the user's HOW TO step 2).
- **Some inbox notes already carry a label.** Surface the current label as the suggested one (action = archive-only). Only re-suggest a different label if the current clearly doesn't fit.
- **Classify from references, not names:** use `keep profiles` to see what notes already live under each label; match each inbox note to the label its content most resembles.
- **Label vocabulary:** prefer an existing label (his `[NN] Name` taxonomy). Propose a 🆕 new label (named `[NN] …`) only when nothing fits; create on approval.
- Address notes/labels by **id**; show **titles/names** to the user. Work inline.
- **CLI and keep-mcp have independent caches.** This skill uses the `keep` CLI exclusively. Don't mix in `mcp__keep-mcp__*` writes mid-run.
- **Self-improving:** before classifying, read `~/.claude/skills/keep-organizer/learnings.md` (past corrections) and honour it. When the user overrides a suggestion and types a `why`, append a new entry there at execution time so future suggestions improve.

## Workflow

```
1. keep inbox  (empty? "Inbox is clear." stop)
2. keep labels + keep profiles + read learnings.md
3. Classify notes:
   - ≤8 notes → classify inline (Sonnet, sequential)
   - >8 notes → dispatch Haiku sub-agents in parallel (batches of 5-6 notes each)
4. Review — pop-up if ≤5 notes, else HTML preview pane
5. Resolve choices into a plan
6. Compact final summary
7. Execute: create new labels → add labels → archive labelled → trash deleted
8. Report
```

### Routing labels (the 6 action-routing labels)

These coexist with topic labels on the same note. They signal where a note should go after archiving:

| Label | Destination |
|---|---|
| `notion task` | Notion My Task List database (no timing) |
| `today` | Notion My Task List · `When? = Today` |
| `tomorrow` | Notion My Task List · `When? = Tomorrow` |
| `next 3 days` | Notion My Task List · `When? = Next 3 Days` |
| `notion new project idea` | Notion new project page |
| `notion add to project` | Notion existing project page |

Classification rule: suggest a routing label only when the note contains an actionable item (task or project idea). For a task that needs doing in a set window, prefer the timing label (`today` / `tomorrow` / `next 3 days`) — it becomes a Notion task staged in that window. Use `notion task` for an actionable task with no fixed window. Default is `none` for reference/informational notes. (Everything routes to Notion — the user blocks his own calendar time off his Notion list.)

### 1–3. Fetch + classify

`keep inbox` (stop if empty). `keep labels` + `keep profiles`. **Read `learnings.md`** (past corrections) and honour it.

**If ≤8 notes — classify inline (Sonnet):**
For each note:
- **Topic label:** compare title+text to the exemplars (and learnings) and pick the single best-fit label (existing, or `🆕 [NN] Name` if novel); pick 1–2 alternates; flag `⚠️` when unsure.
- **Routing label:** ask "does this note contain an actionable task, event, or project idea?" If yes, suggest one of the 6 routing labels above. If no (reference-only), set `routing_suggested` to `none`.

**If >8 notes — parallel Haiku sub-agents:**
1. Split notes into batches of 5–6. Spawn one Haiku sub-agent per batch using the `Agent` tool with `model: "haiku"`. Send all batches in a single tool call so they run concurrently.
2. Each sub-agent receives:
   - Its batch of notes (id, title, full text, current labels)
   - All label names + profiles (the full output of `keep profiles`)
   - Full contents of `learnings.md`
   - This exact classification prompt:

     > Classify each note. For each note return a JSON object with these fields:
     > `id` (note id), `suggested` (single best label name from the provided list, or "🆕 [NN] Name" if novel), `alts` (array of 1–2 alternate label names), `uncertain` (true/false), `routing_suggested` (one of: "notion task", "today", "tomorrow", "next 3 days", "notion new project idea", "notion add to project", or null).
     > Rules: Prefer existing labels. Use profiles to match by content similarity. Use learnings to override where noted. Suggest routing only for notes with an actionable task or project idea. Return a JSON array only — no other text.

3. Collect all sub-agent responses. Parse JSON arrays and merge into a single flat array of classification objects, keyed by note id.
4. If any sub-agent returns malformed JSON or errors, fall back to classifying that batch inline.

### 4a. Review — small inbox (≤5): AskUserQuestion
Two passes:
1. **Topic labels** — one question per note, multiSelect, options ≤4: suggested label first, then 1–2 alternates, then `🗑 Delete`. "Other" is auto. Batch up to 4 notes per AskUserQuestion call.
2. **Routing labels** — one question per note, single-select, options: the 6 routing labels + `none (skip routing)`. Pre-select `routing_suggested`. Batch up to 4 notes per call. Skip notes marked for trash in pass 1.

### 4b. Review — big inbox (>5): HTML preview pane
1. Build input JSON: `{ "labels":[all label names], "projects":[Notion project names], "notes":[{id,title,text(full),current:[names],suggested,alts:[1-2],uncertain,routing_suggested}] }`. `routing_suggested` = one of the 6 routing label names or `null`. `projects` = the project-name list from `norg --json projects` (used to populate the per-note project picker shown for `notion task` routes); pull each name from its `properties` title field, or just run `norg projects` and take the name before the trailing `  [State]`. Write to `/tmp/keep_review_input.json`.
2. Render: `python3 ~/.claude/skills/keep-organizer/scripts/keep_review_page.py /tmp/keep_review_input.json` (writes `review/index.html`).
3. Ensure the current project's `.claude/launch.json` has the **keep-review** entry (create/merge if missing):
   `{"name":"keep-review","runtimeExecutable":"python3","runtimeArgs":["-m","http.server","8766","--directory","~/.claude/skills/keep-organizer/review"],"port":8766}`
4. `preview_start("keep-review")` → serverId. `preview_screenshot` to confirm it rendered.
5. Tell the user: "Review in the side pane (scroll the whole list), then say **done**." Wait.
6. On "done": `preview_eval(serverId, "JSON.stringify(window.getReview())")` →
   `{ decisions:[{id,title,suggested,action,labels,instruction,why,routing_label,route_notes,route_project}], batch }`. `action` ∈ `label|trash|instruct|skip`. `routing_label` = one of the 6 routing label names or `null`. `why` = reason the user typed when he overrode the topic label suggestion. **`route_notes`** = free-text detail the user voice-dumped for a Notion-bound note (any `notion …` route) — `null` otherwise; becomes `norg task add --notes "<route_notes>"` at routing time. **`route_project`** = Notion project name the user assigned (only ever set for the `notion task` route, chosen from the `projects` picker) — `null` otherwise; becomes `norg task add --project "<route_project>"`.
7. `preview_stop(serverId)` once decisions are captured.

### 5–6. Resolve + summarise
Per decision: `label` → add `labels` + `routing_label` (skip ones already on the note); `trash` → trash; `instruct` → do what `instruction` says (e.g. "create label [NN] X and file here", "merge with note N", "split"); `skip` → leave untouched. **Retain `route_notes` / `route_project`** per decision alongside `routing_label` — these are the inline Notion context the user typed and must be carried into the routing step (they don't change Keep behaviour). Apply the `batch` instruction across all notes if present. Create any 🆕/instructed new labels (on approval). Show a compact summary grouped by destination (new labels, # archived, # trashed, # with routing labels). Ticks are the approval; ask one final "go" if anything is being trashed.

### 7. Execute (keep CLI)
1. New labels: `keep create-label "<name>"` → capture id.
2. `keep add-label <note_id> <label_id>` per note→topic label (skip if already present).
3. **Routing label:** if `routing_label` is non-null, look up the routing label id from `keep labels` and `keep add-label <note_id> <routing_label_id>` (skip if already present). The actual Notion write happens later in **keep-router** (or the chained end-of-day flow). If you proceed straight into routing in the same session, carry `route_notes` → `norg task add --notes "<route_notes>"` and `route_project` → `norg task add --project "<route_project>"` for each Notion-bound note. Otherwise `route_notes`/`route_project` are non-persistent (they live in this session's decisions only) — run routing in the same pass to use them.
4. `keep archive <note_id>...` for every labelled note (batch).
5. `keep trash <note_id>...` for delete-marked notes (batch).
6. **Learnings:** for each decision where `action=label` AND the chosen topic labels don't include `suggested` (an override) AND `why` is non-empty, append an entry to `~/.claude/skills/keep-organizer/learnings.md`:
   `- "<title or text gist>" → suggested **<suggested>**, chose **<labels>**. Why: <why>` (under a `## <today>` heading, newest at bottom).
   Also append routing overrides: if `routing_label` differs from `routing_suggested` and the user typed a why, append: `- routing: suggested **<routing_suggested>**, chose **<routing_label>**. Why: <why>`.

### 8. Report
"Filed N (label → count), created M labels, trashed K, skipped S. Routing labels applied to R notes. Inbox now has X." Re-runnable anytime.

## Token refresh (~when expired/revoked)
Same as the `google-keep` skill: open `accounts.google.com/EmbeddedSetup`, copy the `oauth_token` cookie, then:
```bash
GKEEP_EMAIL="<client@email>" GKEEP_OAUTH_TOKEN="oauth2_4/..." \
uv run --no-project --with gpsoauth python3 -c '
import os,gpsoauth
r=gpsoauth.exchange_token(os.environ["GKEEP_EMAIL"],os.environ["GKEEP_OAUTH_TOKEN"],"0123456789abcdef")
print(r.get("Token") or r)'
```
Write the `aas_et/…` token to `~/.config/keep-cli/token` (or update keep-mcp's env in `~/.claude.json`). The CLI reads it fresh each call.

## Edge cases
- Empty inbox → say so, stop.
- No title → use a text gist as the row label.
- Auth error → CLI prints `ERROR: …`, exits non-zero; stop and point to Token refresh.
- the user skips everything / aborts / closes the pane → make no writes.
- Preview pane: only available in Claude Code (not the Desktop app). If unavailable, fall back to the clipboard "Copy decisions" button (he pastes the JSON back) or the pop-up.
- Proposed new label duplicates an existing theme → prefer the existing label.
