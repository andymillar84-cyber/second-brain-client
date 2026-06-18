#!/usr/bin/env python3
"""keep-autolabel — label new Google Keep notes automatically (no archiving).

Polls the Keep inbox, classifies any note that has no topic label yet against the
existing label vocabulary (via `claude -p`, using Andrew's subscription), and applies
the chosen topic + routing labels. It NEVER archives and NEVER creates new labels, so
the downstream keep-organizer / keep-router flow is untouched — it just finds notes
already labelled and ready to route.

If a run fails (e.g. an expired Keep master token or Claude login) it posts a macOS
notification ONCE, so a silent stall surfaces instead of only landing in the log; it
goes quiet while the failure persists and pings again once it recovers.

Run by launchd hourly; also runnable by hand:
    python3 autolabel.py            # live
    python3 autolabel.py --dry-run  # classify + log, apply nothing
"""
import fcntl
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HOME = Path.home()
KEEP = str(HOME / ".local" / "bin" / "keep")
CLAUDE = str(HOME / ".local" / "bin" / "claude")
LEARNINGS = HOME / ".claude" / "skills" / "keep-organizer" / "learnings.md"
STATE_DIR = HOME / ".config" / "keep-autolabel"
PROCESSED = STATE_DIR / "processed.json"
LOG = STATE_DIR / "log.jsonl"
FAIL_FLAG = STATE_DIR / ".failing"  # present while the job is in a failed state (dedupes notifications)

ROUTING_LABELS = {
    "notion task", "today", "tomorrow", "next 3 days",
    "notion new project idea", "notion add to project",
}
# Labels that are neither topic labels nor routing labels — never auto-applied as a topic.
NON_TOPIC = ROUTING_LABELS | {"keep-mcp"}

CLASSIFY_PROMPT = """You are classifying Google Keep notes so they can be filed later. \
For EACH note return one JSON object with these exact fields:
  "id": the note id (copy it back exactly),
  "suggested": the single best-fit EXISTING topic label name from the TOPIC LABELS list, \
or "none" if nothing fits well. NEVER invent a label — only use names from the list or "none".
  "alts": array of up to 2 alternate existing topic label names (or []),
  "uncertain": true/false,
  "routing_suggested": one of "notion task","today","tomorrow","next 3 days",\
"notion new project idea","notion add to project", or null.

Rules:
- Topic labels are the "[NN] Name" style labels. Match each note to the label whose existing \
notes (see PROFILES exemplars) its content most resembles. Prefer an existing label; if none \
fits well, use "none" — a human will label it later.
- Suggest a routing label ONLY when the note contains an actionable task or project idea. \
For a task with a clear time window prefer "today"/"tomorrow"/"next 3 days"; use "notion task" \
for an actionable task with no fixed window; "notion new project idea" / "notion add to project" \
for project-level ideas. Otherwise routing_suggested is null.
- Honour the corrections in LEARNINGS.

Return ONLY a JSON array of these objects — no other text, no markdown fences.

TOPIC LABELS:
{topic_labels}

PROFILES (exemplars per label):
{profiles}

LEARNINGS:
{learnings}

NOTES TO CLASSIFY:
{notes}
"""


def now():
    return datetime.now()


def env_with_path():
    env = dict(os.environ)
    extra = [str(HOME / ".local" / "bin"), "/opt/homebrew/bin", "/usr/local/bin",
             "/usr/bin", "/bin", "/usr/sbin", "/sbin"]
    cur = env.get("PATH", "")
    env["PATH"] = ":".join(extra + ([cur] if cur else []))
    env.setdefault("HOME", str(HOME))
    return env


def run_keep(*args):
    r = subprocess.run([KEEP, *args], capture_output=True, text=True, env=env_with_path())
    if r.returncode != 0:
        raise RuntimeError("keep {} failed: {}".format(" ".join(args), r.stderr.strip()))
    return json.loads(r.stdout) if r.stdout.strip() else None


def extract_json_array(s):
    # Strip markdown fences the model sometimes adds, then decode the first JSON
    # array with a string-aware decoder (label names contain literal [ ] chars,
    # so naive bracket-matching breaks).
    s = re.sub(r"```(?:json)?", "", s)
    start = s.find("[")
    if start == -1:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(s[start:])
        return value if isinstance(value, list) else None
    except json.JSONDecodeError:
        return None


def classify(notes, topic_labels, profiles, learnings):
    prompt = CLASSIFY_PROMPT.format(
        topic_labels="\n".join(topic_labels),
        profiles=json.dumps(profiles, ensure_ascii=False),
        learnings=learnings or "(none)",
        notes=json.dumps(notes, ensure_ascii=False),
    )
    r = subprocess.run(
        [CLAUDE, "-p", "--model", "haiku"],
        input=prompt, capture_output=True, text=True,
        timeout=300, cwd=str(STATE_DIR), env=env_with_path(),
    )
    if r.returncode != 0:
        raise RuntimeError("claude -p failed (rc={}): {}".format(r.returncode, r.stderr.strip()[:500]))
    arr = extract_json_array(r.stdout)
    if arr is None:
        raise RuntimeError("could not parse JSON from claude output: {}".format(r.stdout.strip()[:500]))
    return {c["id"]: c for c in arr if isinstance(c, dict) and "id" in c}


def log_line(record):
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def daily_log(line):
    p = STATE_DIR / ("daily-%s.log" % now().strftime("%Y-%m-%d"))
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def notify(title, message):
    """Best-effort macOS notification. This is a LaunchAgent so it runs in the user's
    GUI session and Notification Center is reachable. Never let a notification failure
    crash the actual labelling run."""
    try:
        subprocess.run(
            ["/usr/bin/osascript", "-e", "display notification {} with title {}".format(
                json.dumps(message, ensure_ascii=False), json.dumps(title, ensure_ascii=False))],
            capture_output=True, env=env_with_path(), timeout=10,
        )
    except Exception:
        pass


def mark_failing(stage, detail):
    """Ping the user ONCE when a run goes healthy→failing (e.g. an expired Keep or Claude
    token), then stay quiet while it keeps failing so it doesn't nag every hour."""
    if not FAIL_FLAG.exists():
        notify("Keep auto-labeller stopped",
               "{} error — new notes won't auto-label until it's fixed.".format(stage))
    FAIL_FLAG.write_text("{}: {}".format(stage, detail)[:500], encoding="utf-8")


def mark_ok():
    """On a healthy run, clear the failure flag and ping once if it had been failing."""
    if FAIL_FLAG.exists():
        FAIL_FLAG.unlink()
        notify("Keep auto-labeller recovered", "Auto-labelling is working again.")


def main():
    dry = "--dry-run" in sys.argv
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    ts = now().isoformat(timespec="seconds")

    # Run lock — prevent overlapping launchd runs racing on processed.json.
    lock_f = open(STATE_DIR / "run.lock", "w")
    try:
        fcntl.flock(lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another keep-autolabel run is in progress; exiting")
        return 0

    processed = set()
    if PROCESSED.exists():
        try:
            data = json.loads(PROCESSED.read_text())
            if not isinstance(data, list):
                raise ValueError("processed.json is not a JSON list")
            processed = set(data)
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as e:
            # Don't silently reset to empty — that would re-mutate every note.
            log_line({"ts": ts, "event": "error", "stage": "state", "detail": str(e)})
            print("ERROR: processed.json is unreadable — refusing to run (would reset history):", e)
            mark_failing("state", str(e))
            return 1

    try:
        inbox = run_keep("inbox") or []
        labels = run_keep("labels") or []
    except RuntimeError as e:
        log_line({"ts": ts, "event": "error", "stage": "keep", "detail": str(e)})
        print("ERROR (keep):", e)
        mark_failing("Keep", str(e))
        return 1

    name_to_id = {l["name"]: l["id"] for l in labels}
    topic_labels = sorted(
        n for n in name_to_id
        if n not in NON_TOPIC and not n.lower().startswith("calendar")
    )
    topic_set = set(topic_labels)

    def has_topic(note):
        return any(l["name"] in topic_set for l in note.get("labels", []))

    candidates = [n for n in inbox if n["id"] not in processed and not has_topic(n)]

    if not candidates:
        log_line({"ts": ts, "event": "poll", "new": 0})
        print("[{}] no new notes to label".format(ts))
        mark_ok()  # Keep was reachable → the job is healthy
        return 0

    try:
        profiles = run_keep("profiles") or {}
    except RuntimeError as e:
        log_line({"ts": ts, "event": "error", "stage": "profiles", "detail": str(e)})
        print("ERROR (profiles):", e)
        mark_failing("Keep", str(e))
        return 1
    learnings = LEARNINGS.read_text(encoding="utf-8") if LEARNINGS.exists() else ""

    notes_payload = [
        {"id": n["id"], "title": n.get("title", ""), "text": n.get("text", ""),
         "current_labels": [l["name"] for l in n.get("labels", [])]}
        for n in candidates
    ]

    try:
        results = classify(notes_payload, topic_labels, profiles, learnings)
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        log_line({"ts": ts, "event": "error", "stage": "classify", "detail": str(e)})
        print("ERROR (classify):", e)
        mark_failing("Claude", str(e))
        return 1  # leave candidates unprocessed → retried next poll

    applied = 0
    for n in candidates:
        c = results.get(n["id"])
        if not c:
            continue  # model omitted it — retry next poll
        title = n.get("title") or (n.get("text", "")[:40].replace("\n", " "))

        suggested = (c.get("suggested") or "").strip()
        topic = suggested if (suggested and suggested != "none" and suggested in topic_set) else None
        routing = c.get("routing_suggested")
        routing = routing if (routing in ROUTING_LABELS and routing in name_to_id) else None

        if not dry:
            try:
                # Apply routing first, topic LAST: the candidate filter retries any
                # note that still lacks a topic label, so making topic the final write
                # means a partial failure here is safely retried next run (add-label
                # is idempotent, so re-applying routing does no harm).
                if routing:
                    run_keep("add-label", n["id"], name_to_id[routing])
                if topic:
                    run_keep("add-label", n["id"], name_to_id[topic])
            except RuntimeError as e:
                log_line({"ts": ts, "event": "error", "stage": "apply",
                          "note_id": n["id"], "detail": str(e)})
                continue  # don't mark processed → retry next poll

        processed.add(n["id"])
        applied += 1
        rec = {"ts": ts, "event": "labelled", "note_id": n["id"], "title": title,
               "topic": topic, "routing": routing, "uncertain": bool(c.get("uncertain")),
               "dry": dry}
        log_line(rec)
        daily_log("[{}]{} {} → topic: {} | routing: {}".format(
            now().strftime("%H:%M"), " [DRY]" if dry else "",
            title, topic or "NONE (needs review)", routing or "none"))

    if not dry:
        tmp = PROCESSED.with_name(PROCESSED.name + ".tmp")
        tmp.write_text(json.dumps(sorted(processed), ensure_ascii=False))
        os.replace(tmp, PROCESSED)  # atomic — no mid-write corruption

    print("[{}]{} labelled {}/{} new note(s)".format(
        ts, " [DRY]" if dry else "", applied, len(candidates)))
    mark_ok()  # a full classify+apply cycle ran → the job is healthy
    return 0


if __name__ == "__main__":
    sys.exit(main())
