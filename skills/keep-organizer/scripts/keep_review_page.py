#!/usr/bin/env python3
"""Render the keep-organizer review page from a JSON spec.

Usage:  keep_review_page.py <input.json> [output.html]

input.json:
  {
    "labels": ["[01] Example Topic", ...],       # all label names (for the Other dropdown)
    "projects": ["Project A", "Project B", ...], # Notion project names (for the notion-task project picker), optional
    "notes": [
      {"id": "...", "title": "...", "text": "full note text",
       "current": ["[99] ..."],                  # labels already on the note (optional)
       "suggested": "[01] Example Topic",        # best-fit topic label (pre-ticked)
       "alts": ["[02] Another Topic"],           # other plausible topic labels shown as checkboxes
       "uncertain": false,                       # ⚠️ flag
       "routing_suggested": "notion task"}       # one of the 6 routing labels, or null/omit for none
    ]
  }

Default output: ../review/index.html (served by the `keep-review` preview server).
Read selections back with: preview_eval(window.getReview())
  -> { decisions: [{id,title,suggested,action,labels,instruction,why,routing_label,route_notes,route_project}], batch }
     action ∈ "label" | "trash" | "instruct" | "skip"
     routing_label = one of the 6 routing label names, or null
     why = optional reason the user typed when he overrode the suggested label (self-improve loop)
     route_notes = free-text detail the user voice-dumped for a Notion-bound note (any "notion …" route), else null
                   → flows to the task/project body in keep-router (Notion MCP) at execution
     route_project = Notion project name the user assigned (only for "notion task" route), else null
                   → flows to the task's Project relation in keep-router (Notion MCP) at execution

Styling: dark-mode design system — accent hues only.
"""
import json
import sys
from pathlib import Path

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Keep Organizer — review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
/* Dark-mode design system — accent hues only */
:root {
  --parchment:#F4F3EE; --floral-white:#FBFBF2; --carbon-black:#222222;
  --boxy-copper:#D66853; --copper-700:#B8512F; --copper-300:#E28F78;
  --teal-blue:#0471A6; --teal-300:#3A92BE;
  --font-serif:'Libre Caslon Text','Iowan Old Style',Georgia,serif;
  --font-sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace;
  /* dark semantic roles */
  --bg:#1b1b19; --bg-elevated:#262623; --bg-footer:#161614;
  --fg:var(--floral-white); --fg-muted:rgba(244,243,238,.60); --fg-subtle:rgba(244,243,238,.40);
  --border:rgba(244,243,238,.12); --border-strong:rgba(244,243,238,.22);
  --accent:var(--teal-300);            /* checkbox + button accent */
  --del:var(--boxy-copper);            /* delete / destructive */
  --inst:var(--teal-blue);             /* free-text instruct */
  --warn:#E2B778;
  --radius-md:6px; --radius-lg:12px;
}
* { box-sizing:border-box; }
body { margin:0; font-family:var(--font-sans); font-size:15px; line-height:1.55; background:var(--bg); color:var(--fg);
       -webkit-font-smoothing:antialiased; font-feature-settings:'ss01','cv11'; }
header { position:sticky; top:0; z-index:5; background:var(--bg); padding:18px 22px 12px; border-bottom:1px solid var(--border); }
h1 { font-family:var(--font-serif); font-weight:400; letter-spacing:-.02em; font-size:24px; margin:0 0 2px; }
header p { margin:0; color:var(--fg-muted); font-size:13px; }
main { padding:18px 22px 240px; max-width:780px; }
.card { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px 18px; margin:0 0 14px; }
.card.del { outline:2px solid var(--del); opacity:.72; }
.card.inst { outline:2px solid var(--inst); }
.top { display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; }
.tag { font-family:var(--font-mono); font-size:11px; font-weight:500; color:var(--carbon-black); background:var(--boxy-copper); border-radius:var(--radius-md); padding:2px 8px; white-space:nowrap; }
.title { font-weight:600; }
.untitled { color:var(--fg-subtle); font-style:italic; }
.warn { color:var(--warn); font-size:12px; font-weight:600; }
.text { color:var(--parchment); font-size:13.5px; margin:9px 0 8px; white-space:pre-wrap; opacity:.9; }
.cur { color:var(--fg-muted); font-size:12px; margin-bottom:2px; }
.sug { color:var(--fg-muted); font-size:12px; margin-bottom:7px; }
.sug b { color:var(--teal-300); font-weight:600; }
.labels { display:flex; flex-wrap:wrap; gap:7px 16px; }
label.chk { display:inline-flex; align-items:center; gap:6px; font-size:13.5px; cursor:pointer; user-select:none; }
label.chk input { width:16px; height:16px; accent-color:var(--accent); }
.row2 { display:flex; gap:18px; align-items:center; margin-top:11px; flex-wrap:wrap; }
select, input.instruct, input.why, textarea { background:#141413; color:var(--fg); border:1px solid var(--border-strong); border-radius:var(--radius-md); padding:7px 9px; font-size:13px; font-family:inherit; }
select:focus, input:focus, textarea:focus { outline:2px solid var(--teal-blue); outline-offset:1px; }
.del-lbl { color:var(--del); }
.del-lbl input { accent-color:var(--del); }
.instruct { display:none; width:100%; margin-top:10px; border-color:var(--inst); }
.instruct.show { display:block; }
.why { display:none; width:100%; margin-top:8px; border-color:var(--warn); }
.why.show { display:block; }
footer { position:fixed; bottom:0; left:0; right:0; background:var(--bg-footer); border-top:1px solid var(--border); padding:11px 22px; }
footer .bar { display:flex; align-items:center; gap:14px; max-width:780px; }
#copy { background:var(--boxy-copper); color:var(--floral-white); border:0; border-radius:2px; padding:9px 16px; font-weight:600; font-family:var(--font-sans); cursor:pointer; }
#copy:hover { background:var(--copper-700); }
#status { color:var(--fg-muted); font-size:12px; }
.batchwrap { max-width:780px; margin-top:8px; }
.batchwrap label { font-size:12px; color:var(--fg-muted); }
#batch { width:100%; height:36px; margin-top:4px; }
pre { margin:8px 0 0; max-height:60px; overflow:auto; background:#121211; border:1px solid var(--border); border-radius:var(--radius-md); padding:8px; font-size:11px; color:var(--fg-muted); max-width:780px; font-family:var(--font-mono); }
.routing { margin-top:10px; border-top:1px solid var(--border); padding-top:10px; }
.routing-label { font-size:12px; color:var(--fg-muted); margin-bottom:5px; }
.routing-label b { color:#9fc; font-weight:600; }
.routing select { min-width:220px; }
.route-notes { display:none; width:100%; margin-top:10px; border-color:#9fc; }
.route-notes.show { display:block; }
.route-project-wrap { display:none; margin-top:10px; align-items:center; gap:6px; font-size:13px; color:var(--fg-muted); }
.route-project-wrap.show { display:flex; }
.route-project-wrap select { min-width:220px; }
</style>
</head>
<body>
<header>
  <h1>Keep Organizer — review</h1>
  <p>One scrollable page. Tick label(s), pick "Other…", choose "➕ New label / tell Claude…" to type a free instruction, or 🗑 to delete. If you change my suggestion, a quick "why?" box appears. Then tell Claude "done".</p>
</header>
<main id="notes"></main>
<footer>
  <div class="bar">
    <button id="copy">Copy decisions</button>
    <span id="status">…</span>
  </div>
  <div class="batchwrap">
    <label for="batch">Instructions for Claude (whole batch, optional)</label>
    <textarea id="batch" placeholder="Voice-dump any edge cases for the whole batch here."></textarea>
  </div>
  <pre id="out"></pre>
</footer>
<script>
const DATA = __DATA__;
const ALL_LABELS = DATA.labels || [];
const PROJECTS = DATA.projects || [];
const NOTES = DATA.notes || [];
const INSTRUCT = "__instruct__";
const ROUTING_OPTIONS = [
  "calendar today",
  "calendar three days",
  "calendar next week",
  "notion task",
  "notion new project idea",
  "notion add to project"
];
// Routes that send the note into Notion — reveal the voice-dump detail field for these.
const NOTION_ROUTES = ["notion task", "notion new project idea", "notion add to project"];
function esc(s){ return (s==null?"":String(s)).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function escAttr(s){ return esc(s).replace(/"/g,"&quot;"); }

const main = document.getElementById("notes");
NOTES.forEach((n, i) => {
  const chips = [...new Set([n.suggested, ...(n.alts||[])].filter(Boolean))];
  const cur = (n.current||[]).length ? `<div class="cur">currently: ${esc((n.current||[]).join(", "))}</div>` : "";
  const warn = n.uncertain ? ` <span class="warn">⚠️ unsure</span>` : "";
  const routingSug = n.routing_suggested || null;
  const card = document.createElement("section");
  card.className = "card";
  card.innerHTML = `
    <div class="top"><span class="tag">Note ${i+1}</span>
      <span class="title ${n.title?"":"untitled"}">${esc(n.title) || "(untitled)"}</span>${warn}</div>
    <div class="text">${esc(n.text)}</div>
    ${cur}
    <div class="sug">suggested: <b>${esc(n.suggested||"—")}</b></div>
    <div class="labels">
      ${chips.map(c => `<label class="chk"><input type="checkbox" class="lbl" value="${escAttr(c)}" ${c===n.suggested?"checked":""}>${esc(c)}${c===n.suggested?" ✓":""}</label>`).join("")}
    </div>
    <div class="row2">
      <label>Other…
        <select class="other"><option value="">—</option>
          ${ALL_LABELS.map(l => `<option value="${escAttr(l)}">${esc(l)}</option>`).join("")}
          <option value="${INSTRUCT}">➕ New label / tell Claude…</option>
        </select></label>
      <label class="chk del-lbl"><input type="checkbox" class="del">🗑 Delete (trash)</label>
    </div>
    <input class="instruct" placeholder="Tell Claude what to do, e.g. 'create label [10] Health and file here'">
    <input class="why" placeholder="Why was my suggestion off? (optional — helps me improve)">
    <div class="routing">
      <div class="routing-label">route as: <b>${esc(routingSug || "none")}</b></div>
      <label>Route:
        <select class="routing-sel">
          <option value="" ${!routingSug?"selected":""}>none (skip routing)</option>
          ${ROUTING_OPTIONS.map(r => `<option value="${escAttr(r)}" ${r===routingSug?"selected":""}>${esc(r)}</option>`).join("")}
        </select>
      </label>
      <label class="route-project-wrap">Project:
        <select class="route-project">
          <option value="">— (no project)</option>
          ${PROJECTS.map(p => `<option value="${escAttr(p)}">${esc(p)}</option>`).join("")}
        </select>
      </label>
      <textarea class="route-notes" placeholder="Extra detail for this Notion task/project (voice-dump) — appended to the note body."></textarea>
    </div>`;
  main.appendChild(card);
});

function readCard(card, n) {
  const del = card.querySelector(".del").checked;
  const labels = new Set();
  card.querySelectorAll(".lbl:checked").forEach(c => labels.add(c.value));
  const otherSel = card.querySelector(".other").value;
  const instructInput = card.querySelector(".instruct");
  const wantInstruct = otherSel === INSTRUCT;
  instructInput.classList.toggle("show", wantInstruct);
  if (otherSel && !wantInstruct) labels.add(otherSel);
  const instruction = wantInstruct ? instructInput.value.trim() : "";
  let action = "skip";
  if (del) action = "trash";
  else if (instruction) action = "instruct";
  else if (labels.size) action = "label";
  // self-improve: reveal "why?" only when the suggestion was overridden (not picked, not deleted)
  const overridden = !del && n.suggested && !labels.has(n.suggested);
  const whyInput = card.querySelector(".why");
  whyInput.classList.toggle("show", overridden);
  const why = overridden ? whyInput.value.trim() : "";
  card.classList.toggle("del", del);
  card.classList.toggle("inst", !del && !!instruction);
  const routing_label = del ? null : (card.querySelector(".routing-sel").value || null);
  // Notion-bound routes reveal a voice-dump detail field; "notion task" also reveals a project picker.
  const isNotion = NOTION_ROUTES.includes(routing_label);
  const isTask = routing_label === "notion task";
  const notesEl = card.querySelector(".route-notes");
  const projWrap = card.querySelector(".route-project-wrap");
  const projEl = card.querySelector(".route-project");
  notesEl.classList.toggle("show", isNotion);
  projWrap.classList.toggle("show", isTask);
  const route_notes = isNotion ? (notesEl.value.trim() || null) : null;
  const route_project = isTask ? (projEl.value || null) : null;
  return { id:n.id, title:n.title, suggested:n.suggested||null, action, labels:[...labels], instruction, why, routing_label, route_notes, route_project };
}

window.getReview = function () {
  const decisions = NOTES.map((n,i) => readCard(main.children[i], n));
  return { decisions, batch: document.getElementById("batch").value.trim() };
};
window.getDecisions = () => window.getReview().decisions;

function refresh() {
  const r = window.getReview();
  document.getElementById("out").textContent = JSON.stringify(r, null, 1);
  const acted = r.decisions.filter(x => x.action!=="skip").length;
  document.getElementById("status").textContent = `${acted}/${r.decisions.length} notes have an action`;
}
main.addEventListener("change", refresh);
main.addEventListener("input", refresh);
document.getElementById("batch").addEventListener("input", refresh);
document.getElementById("copy").addEventListener("click", () => {
  navigator.clipboard.writeText(JSON.stringify(window.getReview())).then(()=>{
    document.getElementById("status").textContent = "copied to clipboard ✓";
  });
});
refresh();
</script>
</body>
</html>
'''


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: keep_review_page.py <input.json> [output.html]")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = (Path(sys.argv[2]) if len(sys.argv) > 2
           else Path(__file__).resolve().parent.parent / "review" / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.replace("__DATA__", blob), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
