---
name: notion-project-skill
description: >-
  Use when Andrew describes a real multi-step PROJECT he wants to track in Notion — something
  that takes more than one sitting and needs breaking into tasks (not a single to-do). Triggers on
  "I've got this project I need to do", "I need to build/set up/launch X", "help me break this down",
  "add a project for…", or any voice-dump where the end state is a tracked project with tasks. This
  skill interviews him to pin down the project, then creates the project page in his "My Projects"
  database and fills it with bite-sized, prioritised tasks in his exact house style
  (outcome-as-comment, circle-icon task rows linked back to the project, Importance/Urgency/State set,
  filed under a life bucket). Prefer this over hand-rolling Notion pages — it encodes the precise
  database IDs, template, and property formats so the result matches his system every time. Do NOT
  use for single one-off tasks, for editing the calendar/timetable database, or for non-project
  Notion edits.
---

# Notion Project Skill

Andrew runs his life out of one Notion hub, **"Freshie"**. When he has a *project* (a thing too big for one task — could take a few hours or a few weeks), he wants it captured the same way every time: a project page in **My Projects**, broken into small tasks he can tick off and allocate his own time to. This skill does that, faithfully matching the house style he's refined.

The single most important idea: **tasks are not checkboxes typed into the project page body.** They are rows in his master **My Task List** database, linked back to the project via a relation. The project page shows them through a pre-filtered linked view called "Project Tasks". Get this wrong and the tasks won't appear on the project. The recipe below gets it right.

## Resolve the target workspace FIRST (config-aware)

Before using **any** ID in this skill, check for `~/.config/freshie/config.json`:

- **If it exists** (a cloned / client machine): use its values — they **override every hardcoded ID below**. Map: `proj_ds` → My Projects data source · `task_ds` → My Task List data source · `bucket_ds` → My Life Buckets data source · `project_template_id` → New Project template · `hub_page_id` → org hub. The IDs in the System Map are **fallback defaults only**.
- **If it's absent** (Andrew's own machine): use the System Map defaults as-is — behaviour is unchanged.

> ⛔ **If `config.json` exists you MUST route every create / search / query to its IDs.** Writing to a hardcoded default while a client config is present creates the client's project *inside Andrew's Notion* — the exact isolation failure this guards against. If unsure, print the IDs you're about to use and confirm they match `config.json` before writing.

Quick read: `python3 -c 'import json,os;p=os.path.expanduser("~/.config/freshie/config.json");print(json.load(open(p)) if os.path.exists(p) else "no config — using Andrew defaults")'`

## Workflow

### 1. First, ask: quick capture or detailed?

Andrew arrives in one of two modes, and they need opposite handling — so **before anything else, ask him which this is.** One line is enough:

> "Quick capture — you've already got the tasks? Or detailed — we work them out together?"

- **Quick capture** → he already knows the tasks (he's reading them off, or they're obvious in his dump). **Skip the interview and the path-mapping entirely** (steps 2–3). Jump to step 4, show one compact proposed list, and build on his yes. Don't make him answer questions he doesn't need — that interview *is* the friction he's trying to avoid here.
- **Detailed / exploratory** → he has the goal but not the full path. Run steps 2–3 to surface and map the tasks, then propose.

Always ask — don't guess the mode. Guessing wrong is precisely the cost Andrew wants gone: a long interview when he just wanted to dump three tasks, or a thin list when he actually needed help thinking it through. The build steps (5–8) are identical for both modes; only the discovery up front differs.

**The detailed pass has a budget: ~10 minutes of total elapsed time to create the project.** Creation is for *capturing and scaffolding*, not researching — deep research is the work Andrew does later in his allocated project time, not now. This skill is the middle hop of his Keep → Notion → Calendar funnel; if creating a project is slow, he won't do it. The cap shapes steps 2–3: keep the interview light and **defer unknowns to research tasks rather than resolving them now** (see step 3).

**Thorough-planning opt-out:** the cap comes off only when Andrew *explicitly* asks to properly plan a project out. Don't offer or ask about this — just honour it when he says so, and then interview and research as deeply as the project warrants.

### 2. *(Detailed only)* Interview to surface the project — invoke `process-interviewer`

Andrew will usually arrive mid-thought ("Hey Claude, I've got this project…") and voice-dump. Don't start writing to Notion yet. **Invoke the `process-interviewer` skill** to extract a complete, unambiguous picture before building. You're trying to surface:

- **The outcome** — short, usually a sentence or two: what's true when this project is done? E.g. for the YouTube project: *"Andrew records a video and it automatically uploads to his YouTube channel."* (This becomes the project's comment.)
- **Scope & size** — hours or weeks? This calibrates how granular the task breakdown should be.
- **Known vs. unknown** — for each piece, does Andrew already know *how* to do it, or only that it needs doing? This is the single most important thing to draw out, because it's what decides what becomes a real task vs. a research task in step 3. **Explicitly tell `process-interviewer` to probe this** — it's a separate skill and won't know to ask otherwise. ("Which parts of this do you already know how to do, and which are you still figuring out?")
- **The tasks** — the concrete steps. If he mentions he already has tasks in mind, lean on `process-interviewer` to draw out the ones he knows but forgot to say. Push for bite-sized pieces, each ideally one sitting.
- **Ordering / dependencies** — what must happen before what. Andrew cares about this a lot ("first I need to make the YouTube channel before I can connect it to Claude"). There's no dependency field in Notion, so you encode order through Urgency (see below) — but you need to *know* the order to do that.
- **The bucket** — don't interrogate him for it; *assume* the likely life area (almost always **Business**; occasionally MAMA Clinic, Personl Brand, etc.) and state your assumption when you propose the project so he can correct it.

Don't re-ask things he already said in his dump. Interview to fill gaps, not to make him repeat himself. Scale the interview to the project — a few-hours project needs a lighter touch than a multi-week one. Under the default ~10-min cap, keep it brief — surface enough to scaffold, not to fully plan. Go deep only if Andrew invoked the thorough-planning opt-out.

Use `process-interviewer` purely to *extract* the project picture. Once it's complete, come back to this skill and run steps 3–8 to map the path and build it — don't let the interview end without the project getting created.

### 3. *(Detailed only)* Map the path: known steps now, unknowns become research tasks

Exploratory projects have a clear goal but unknown steps. Under the ~10-min cap, **your job is to scaffold, not to resolve the unknowns** — split the work two ways:

- **Known steps** → real tasks now (e.g. "he needs a passport" → `⏰ Urgent` / `⚠️ Important`).
- **Unknowns** → research tasks. A *structural* unknown (its answer changes *what the other tasks are*) becomes the first `⏰ Urgent` "figure out X" task, with a note that the list may reshape once it's answered (the YouTube `Spike:` tasks — "can we download the mp4?", "are uploads private-locked?" — are exactly this). A *detail* unknown (only changes *how* one task is done) is just a normal research task. Either way: **write it down, don't go research it now.**

Research-now is justified only for a genuine ~30-second lookup that tells you what the tasks even are; anything longer is execution work and gets deferred, because elapsed time counts against the cap.

So for a larger project, a rough framework — outcome + the handful of known tasks + the structural unknowns captured as research tasks — **is the correct 10-minute output, not a compromise.** A project that's *entirely* "figure out X / Y / Z" tasks for now is a complete, valid first pass; the doing-tasks get added later once research resolves them.

(This step relaxes only under the thorough-planning opt-out — then it's fine to actually research now and resolve unknowns before proposing.)

### 4. Propose the breakdown, get a yes

Before touching Notion, show him the proposed project + task list with your suggested Importance / Urgency / State for each, and the do-first ordering. Let him correct it — he'd rather fix it on paper than in Notion. **In quick-capture mode this is a single compact list** (his tasks, your suggested labels + ordering) — one round, then build on his yes; don't reopen it into an interview. In detailed mode it's the fuller proposal coming out of steps 2–3. Once he approves, build it.

Pressure-test the tasks — don't just transcribe them. Whether a task came from Andrew or from you, and whether the project is exploratory or well-understood, sanity-check that it genuinely needs doing. It's easy to add steps that *sound* right but aren't actually necessary; catching those here keeps the list honest and short.

**Task notes (tasks are pages).** Most tasks are just a title — "Create the YouTube channel" needs nothing more. But some carry detail worth keeping: a spec, a link, an idea, a gotcha to remember. Once the list is outlined, check whether any task needs notes and capture them (in detailed mode, `process-interviewer` is good for drawing these out — "anything you want jotted inside any of these?"). These are one-off, per-task. Reference notes go in the task's page **body** when you create it (step 7); use a task **comment** instead if it's more of a question or something to discuss than fixed reference info.

**What counts as one task?** Something Andrew can sit down and finish in one go — a single coherent deliverable. His rule of thumb: for a course project, "make the Google Slides for module 1" is one task. "Make the course" is too big (that's the project, or a phase). "Open Google Slides" is too small (a sub-step, not worth its own row). Aim for a list he can tick through — often 5–15 tasks, but let the project set the count: a big build legitimately has more, a small one fewer. Don't pad to hit a number, and don't over-split into trivial micro-steps.

**Habit & routine projects — design around the Atomic Habits 4 Laws.** If the project is to build or implement a *habit or routine* (a start/end-of-day SOP, a recurring practice, a daily rep), don't just list the steps — suggest shaping it around James Clear's 4 Laws of Behavior Change: **Make it Obvious · Make it Attractive · Make it Easy · Make it Satisfying** (full reference: `active/operating-system/atomic-habits-laws.md`). Concretely: bias the design toward "easy to start, easy to end" with a reward at the end of the cycle, and add an explicit *Atomic-Habits check* task that runs the routine past all four laws. Andrew builds all his routines this way.

### 5. Create the project page

**First, check it doesn't already exist.** Search My Projects for the name — `notion-search` with `query: "<name>"` and `data_source_url: "collection://a2050211-b922-830a-8cf0-876a231ef27a"`. If a same-or-similar project turns up, stop and ask Andrew whether to add tasks to that one or make a new one — don't silently duplicate, because the API can't hard-delete pages and a stray project then has to be archived by hand.

Create one page in the **My Projects** data source, applying the **New Project template** — the template is what auto-builds the inline "Project Tasks" linked view and wires its filter to this new page. Without the template you get a bare page and the tasks won't render.

> **⛔ The template can ONLY be applied via the MCP `notion-create-pages` tool with `template_id`.** The Notion public REST API — and therefore `notion-pp-cli`, `norg`, and any Bash-driven sub-agent — **rejects `template_id` with `HTTP 400: body.template_id should be not present`**. Create the project with the MCP tool **from the main agent** (sub-agents shelling to the CLI hit the 400 wall). **Never "fall back" to a plain page if the MCP call seems to fail — stop and tell Andrew.** Silently creating a templateless plain page is exactly the bug that produced 5 malformed projects on 2026-05-24. (`norg project create` is deliberately hard-disabled and will refuse with a STOP banner.) Full context: `LESSONS.md` → "Notion project template can ONLY be applied via the MCP create-pages tool".

```
notion-create-pages
  parent: { type: "data_source_id", data_source_id: "<proj_ds from config.json, else a2050211-b922-830a-8cf0-876a231ef27a>" }
  pages: [{
    properties: {
      "Name": "<project name>",
      "My Life Buckets": "[\"<bucket page url>\"]"
    },
    template_id: "<project_template_id from config.json, else c0650211-b922-8379-ae4c-01fddbadb514>"
  }]
```

Notes:
- **Status** — leave it **blank by default** (omit the property). New projects sit under "No Status" until Andrew decides; don't auto-assign one. His meanings: **Fav** = a project he's *actively focused on right now* (keeping that list short is the whole point — never auto-Fav); **Ongoing** = ongoing client work; (`Deadline`, `Completed`, `Moved the Needle`, `Archived` also exist). Set a status only if Andrew clearly indicates one; otherwise leave it blank and let him pick.
- **My Life Buckets** is a relation; its value is a JSON-array *string* of the bucket page URL. Resolve the bucket at runtime (see "Buckets" below) rather than trusting a stale ID. **Gotcha:** applying `template_id` can *drop* a relation set in the same call — the bucket silently comes back empty. After creating, **re-set the bucket in a separate `notion-update-page` call** and confirm it stuck (see step 8). The task `Project`/`Bucket` relations are not affected (tasks use no template).
- **Deadline** (a date property on the project) — leave blank unless Andrew gives a real target date. If he does, set `date:Deadline:start`; the OVERDUE/Deadline project views key off it.
- Don't pass `content` — the template supplies the page body.
- Keep the returned **project page id/url** — every task links to it.

### 6. Add the outcome as a comment

Andrew puts the project's outcome in the comment thread, not the body.

```
notion-create-comment
  page_id: "<project page id>"
  markdown: "Outcome: <the short outcome — a sentence or two>"
```

### 7. Create the tasks

Each task is a row in the **My Task List** data source, linked to the project. Create them in one `notion-create-pages` call (the parent is the task data source, so they share a parent):

```
notion-create-pages
  parent: { type: "data_source_id", data_source_id: "<task_ds from config.json, else c0050211-b922-82c1-9bc6-076a4be40378>" }
  pages: [
    {
      icon: "icons/circle-alternate_gray",
      properties: {
        "Task": "<task name>",
        "Project": "[\"<project page url>\"]",
        "Bucket": "[\"<same bucket page url as the project>\"]",
        "Importance": "<see options>",
        "Urgency": "<see options>",
        "State": "<see options>"
      }
    },
    … one object per task …
  ]
```

Per-task rules:
- **icon** must be `icons/circle-alternate_gray` — the grey circle. Andrew specifically likes this over the default page icon. Set it on every task.
- **Project** is a relation → JSON-array string of the project page URL. This is what makes the task appear in the project's "Project Tasks" view. Miss it and the task floats free.
- **Bucket** — set each task's `Bucket` relation to the *same* bucket as the project (same JSON-array-string format), so the Project Tasks table's Bucket column is filled in rather than empty.
- **Date** — leave blank. Andrew allocates his own time on the calendar; only set a date if he explicitly asks.
- **Notes** — if a task has notes from step 4, pass them as the page `content` (Notion markdown) on that task object; tasks are pages, so the notes live in the body. Tasks with no notes simply omit `content`.
- The tick-off checkbox is a property literally named `" "` (a single space). New tasks default to unchecked, so you don't set it.

### 8. Verify thoroughly, fix, *then* report

Andrew does not want to open Notion later and discover mistakes, so treat this as a real QA pass, not a glance. Fetch the project page and fetch the tasks back, check every item below, and **fix anything that's off before you report** — if a write didn't take, redo it and re-verify.

Project checks:
- **Verify via the data-source query, NOT `pages retrieve-a`.** `retrieve-a` returns a stale cache right after creation (shows `buckets=0` / `icon=null` even when they're set). The live truth is in `data-sources query data-source a2050211-… --no-cache`. Always confirm project state there.
- `Status` matches what was agreed — by default that's **blank / No Status**, which is correct; only expect Fav or Ongoing if Andrew explicitly chose it.
- The bucket relation actually attached — `My Life Buckets` populated, not empty. **This is the one most likely to have silently dropped** (template expansion eats it); if empty, re-set it with `notion-update-page` and re-check.
- The outcome **comment** is present.
- The inline "Project Tasks" view exists — the page body should contain the template's `child_database` linked-view blocks (currently 3; the exact count matters less than that there are **some**). That's the template's signature; a templateless plain page has **none**, which is the failure to catch.

Per-task checks — verify *every* task, not just the first:
- **Linked to the project** — `Project` relation contains the project URL. This is what makes a task appear on the page; a missing link is the most common silent failure, and the task will vanish from view.
- **Icon** is the grey circle (`/icons/circle-alternate_gray`).
- **Importance, Urgency, and State are all set** — no blanks. A half-labelled task is exactly the kind of thing Andrew would otherwise have to fix by hand.
- Any **notes** captured in step 4 actually landed in the task body.

Only once everything checks out, report: the project link, the task list with how you sequenced it (what's `⏰ Urgent` / do-first and *why*), the bucket you assumed, and a one-line flag of anything you couldn't set — so there are no surprises.

## Choosing Importance / Urgency / State

These three selects are how Andrew triages and how the "do-first" ordering gets expressed. Think about *why* each exists:

- **Importance** — does this move the needle? Options: `⚠️ Important`, `Not Important`, `Moved the needle`. Use `⚠️ Important` for the genuinely high-value, project-critical tasks; `Not Important` for small/admin steps (even necessary ones). (`Moved the needle` is mostly a retrospective tag — prefer the first two when creating.)
- **Urgency** — should this be done soon / does it unblock other work? Options: `⏰ Urgent`, `Not Urgent`, `Habit`. **This is your ordering lever.** Since Notion has no dependency field, mark the *prerequisites that unblock everything else* as `⏰ Urgent` — even if they're not "important" in themselves. Example: "Create the YouTube channel" is quick and low-importance, but nothing else can happen until it's done, so it's `⏰ Urgent`. Build tasks that come later are usually `Not Urgent` + `⚠️ Important`. (`Habit` is for recurring tasks — rarely relevant to project breakdowns.)
- **State** — what *kind* of work session is this, so he can batch by energy? Options: `Flow` (deep focused build work), `Quick` (fast admin / setup), `Easy` (light, low-effort), `Personal`. Pick the one that matches the task's texture.

The combination tells Andrew, at a glance, what to grab first: scan for `⏰ Urgent` to find the unblockers, then work the `⚠️ Important` build tasks.

## Buckets

Projects are filed under a life area via the **My Life Buckets** relation on the project. The common one is **Business** (most of Andrew's projects). Resolve the bucket's page URL at runtime instead of trusting a hardcoded id — search the buckets data source by name:

```
notion-search  query: "Business"  data_source_url: "collection://c8550211-b922-8371-84e7-87ce15587470"
```

Freshie's buckets: **Business** (the default for work projects), 🏥 MAMA Clinic, 🎥 Personl Brand *(Andrew's spelling — keep it)*, ⚙️ Systems and Energy, 🚀 Moonshots, Life Admin, 🌱 Real Humans. Business's page id is `f1d50211-b922-829d-af5a-015773f50f80` — fine as a fast path, but verify if a write fails.

## System Map (the concrete IDs)

> **These are fallback defaults (Andrew's workspace).** On a client machine they are **overridden by `~/.config/freshie/config.json`** — see "Resolve the target workspace FIRST" at the top. The matching `config.json` key is noted per row.

| Thing | ID / value | config.json key |
|---|---|---|
| My Projects data source | `a2050211-b922-830a-8cf0-876a231ef27a` | `proj_ds` |
| New Project template | `c0650211-b922-8379-ae4c-01fddbadb514` | `project_template_id` |
| My Task List data source | `c0050211-b922-82c1-9bc6-076a4be40378` | `task_ds` |
| My Life Buckets data source | `c8550211-b922-8371-84e7-87ce15587470` | `bucket_ds` |
| Business bucket page | `f1d50211-b922-829d-af5a-015773f50f80` | *(resolved by name)* |
| Task circle icon | `icons/circle-alternate_gray` | *(constant)* |
| Org hub page (Freshie) | `30e50211-b922-833e-82ae-8173e7cc0e16` | `hub_page_id` |

**Project (My Projects) properties:** `Name` (title), `Status` (select), `Deadline` (date), `My Life Buckets` (relation → buckets).

**Task (My Task List) properties:** `Task` (title), `" "` (checkbox, the tick-off — single-space name), `Date` (date), `Importance` (select), `Urgency` (select), `State` (select), `Project` (relation → My Projects), `Bucket` (relation → buckets), `Time`/`Minutes`/`Hours` (leave alone).

**Relation values** are JSON-array strings of page URLs, e.g. `"[\"https://www.notion.so/<id>\"]"`. **Select values** are the exact option string including any emoji (e.g. `"⏰ Urgent"`).

## Tools

This skill uses the connected **Notion MCP** tools: `notion-create-pages`, `notion-update-page`, `notion-create-comment`, `notion-fetch`, `notion-search`. (In the tool list they carry the Notion connector's server-id prefix.) The calendar/timetable is a *separate* database and out of scope — don't touch it here.

## Out of scope / guardrails

- A single one-off task → just add one row to My Task List; don't spin up a project.
- **Project vs. actually building a connection — if unsure, ask.** "Connect X and Y" / "make our tools talk to each other" can mean *track building that integration as a Notion project* (this skill) **or** *go build the integration now* (the `connection-builder` skill). When it's genuinely ambiguous which Andrew wants, double-check with him before creating anything.
- The Notion MCP has **no hard-delete** for pages. If a project needs removing, set its `Status` to `Archived` and tell Andrew it can't be permanently deleted via API.
- Don't invent dates or assign a bucket other than what fits; when genuinely unsure on bucket or status, ask rather than guess.
- **No native sub-projects.** My Projects has no parent/child relation — Notion doesn't nest projects here. For an unusually large project, split it into separate projects, or express phases through task ordering; don't try to fake a hierarchy. (Confirmed 2026-05-22.)

## Parked — revisit ~2026-06-22

Not built yet. Add after roughly a month of real use (≈ **2026-06-22**, one month from this skill's creation on 2026-05-22):

- **Per-task time estimates.** When creating tasks, ask Andrew for a rough estimate (hours or minutes) per task and write it to the task's `Minutes` field (a number — it feeds the existing `Hours` formula). Deliberately left out for now to keep task creation fast. Reaching this date also flags that Andrew's had a month with the skill — a good moment to check in on how it's working and what else to add.
