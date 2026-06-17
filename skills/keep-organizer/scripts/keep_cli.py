#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["gkeepapi>=0.16.0"]
# ///
"""keep — minimal Google Keep CLI for the keep-organizer skill (gkeepapi)."""
import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_EMAIL = os.environ.get("GKEEP_EMAIL", "")
SNIPPET = 200          # max chars of note text included in briefs/exemplars
MAX_EXEMPLARS = 12     # cap exemplars per label in `profiles`


def resolve_creds():
    email = os.environ.get("GOOGLE_EMAIL")
    token = os.environ.get("GOOGLE_MASTER_TOKEN")
    cfg = Path.home() / ".config" / "keep-cli" / "token"
    if not token and cfg.exists():
        token = cfg.read_text().strip()
    if not token:
        try:
            data = json.loads((Path.home() / ".claude.json").read_text())
            env = data.get("mcpServers", {}).get("keep-mcp", {}).get("env", {})
            token = token or env.get("GOOGLE_MASTER_TOKEN")
            email = email or env.get("GOOGLE_EMAIL")
        except (OSError, json.JSONDecodeError):
            pass
    email = email or DEFAULT_EMAIL
    if not token:
        sys.exit("ERROR: no master token ($GOOGLE_MASTER_TOKEN, ~/.config/keep-cli/token, "
                 "or keep-mcp env in ~/.claude.json)")
    return email, token


def connect():
    import gkeepapi
    email, token = resolve_creds()
    keep = gkeepapi.Keep()
    try:
        keep.authenticate(email, token)
    except Exception as exc:  # noqa: BLE001 - surface any auth failure cleanly
        sys.exit(f"ERROR: Keep authentication failed: {exc}\n"
                 "Refresh the master token — see ~/.claude/skills/keep-organizer/SKILL.md.")
    return keep


def note_brief(n, full_text=False):
    text = n.text or ""
    return {
        "id": n.id,
        "title": n.title or "",
        "text": text if full_text else text[:SNIPPET],
        "pinned": n.pinned,
        "archived": n.archived,
        "labels": [{"id": l.id, "name": l.name} for l in n.labels.all()],
    }


def out(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def cmd_inbox(keep, args):
    notes = [n for n in keep.all() if not n.pinned and not n.archived and not n.trashed]
    out([note_brief(n) for n in notes])


def cmd_labels(keep, args):
    out([{"id": l.id, "name": l.name} for l in keep.labels()])


def cmd_profiles(keep, args):
    prof = {}
    for n in keep.all():
        if n.trashed:
            continue
        for l in n.labels.all():
            entry = prof.setdefault(l.name, {"id": l.id, "exemplars": []})
            if len(entry["exemplars"]) < MAX_EXEMPLARS:
                entry["exemplars"].append({"title": n.title or "", "snippet": (n.text or "")[:SNIPPET]})
    out(prof)


def _require_note(keep, note_id):
    note = keep.get(note_id)
    if not note:
        sys.exit(f"ERROR: note {note_id} not found")
    return note


def cmd_add_label(keep, args):
    note = _require_note(keep, args.note_id)
    label = keep.getLabel(args.label_id)
    if not label:
        sys.exit(f"ERROR: label {args.label_id} not found")
    note.labels.add(label)
    keep.sync()
    out(note_brief(note))


def cmd_create_label(keep, args):
    label = keep.createLabel(args.name)
    keep.sync()
    out({"id": label.id, "name": label.name})


def cmd_archive(keep, args):
    for nid in args.note_ids:
        _require_note(keep, nid).archived = True
    keep.sync()
    out({"archived": args.note_ids})


def cmd_trash(keep, args):
    for nid in args.note_ids:
        _require_note(keep, nid).trash()
    keep.sync()
    out({"trashed": args.note_ids})


def cmd_get(keep, args):
    out(note_brief(_require_note(keep, args.note_id), full_text=True))


def cmd_find(keep, args):
    label = None
    if args.label:
        for l in keep.labels():
            if l.name.lower() == args.label.lower():
                label = l
                break
        if not label:
            sys.exit(f"ERROR: label '{args.label}' not found")
    results = []
    for n in keep.all():
        if n.trashed:
            continue
        if args.archived and not n.archived:
            continue
        if label and label not in n.labels.all():
            continue
        results.append(note_brief(n, full_text=args.full))
    out(results)


def cmd_remove_label(keep, args):
    note = _require_note(keep, args.note_id)
    label = keep.getLabel(args.label_id)
    if not label:
        sys.exit(f"ERROR: label {args.label_id} not found")
    note.labels.remove(label)
    keep.sync()
    out(note_brief(note))


HANDLERS = {
    "inbox": cmd_inbox, "labels": cmd_labels, "profiles": cmd_profiles,
    "add-label": cmd_add_label, "remove-label": cmd_remove_label,
    "create-label": cmd_create_label, "archive": cmd_archive,
    "trash": cmd_trash, "get": cmd_get, "find": cmd_find,
}


def build_parser():
    p = argparse.ArgumentParser(prog="keep", description="Minimal Google Keep CLI (keep-organizer)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inbox", help="Notes NOT pinned AND NOT archived (the work queue)")
    sub.add_parser("labels", help="All labels (id + name)")
    sub.add_parser("profiles", help="Per-label exemplars for classification")
    a = sub.add_parser("add-label", help="Add a label to a note")
    a.add_argument("note_id"); a.add_argument("label_id")
    rl = sub.add_parser("remove-label", help="Remove a label from a note")
    rl.add_argument("note_id"); rl.add_argument("label_id")
    c = sub.add_parser("create-label", help="Create a label (returns id)")
    c.add_argument("name")
    ar = sub.add_parser("archive", help="Archive note(s)")
    ar.add_argument("note_ids", nargs="+")
    tr = sub.add_parser("trash", help="Trash note(s) (recoverable)")
    tr.add_argument("note_ids", nargs="+")
    g = sub.add_parser("get", help="Full note by id")
    g.add_argument("note_id")
    f = sub.add_parser("find", help="Find notes by label (optionally archived only)")
    f.add_argument("--label", help="Filter by label name")
    f.add_argument("--archived", action="store_true", help="Only archived notes")
    f.add_argument("--full", action="store_true", help="Include full text")
    return p


def main():
    args = build_parser().parse_args()
    HANDLERS[args.cmd](connect(), args)


if __name__ == "__main__":
    main()
