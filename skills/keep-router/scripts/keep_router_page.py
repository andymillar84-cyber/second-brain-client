#!/usr/bin/env python3
"""Render the keep-router review page from a JSON spec.

Usage:  keep_router_page.py <input.json> [output.html]

input.json:
  {
    "proposals": [
      {"note_id": "...", "note_title": "...", "note_text": "full text",
       "routing_label": "notion task",       # notion task | notion new project idea
                                              # | notion add to project | today | tomorrow | next 3 days
       "proposed_title": "...",
       "proposed_project": "Project X",       # notion add to project only
       "uncertain": false}
    ],
    "projects": ["Project A", "Project B", ...]
  }

A timing label (today / tomorrow / next 3 days) becomes a Notion task staged in that window
(Notion "When?" = Today / Tomorrow / Next 3 Days). Everything routes to Notion — no calendar.

Default output: ../review/index.html (served by the `keep-router-review` preview server).
Read selections back with: preview_eval(window.getReview())
  -> { decisions: [{note_id, action, title, destination, project, when}] }
     action ∈ "confirm" | "skip";  when ∈ "today" | "tomorrow" | "next-3" | null
"""
import json
import sys
from pathlib import Path

TEMPLATE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Keep Router — review</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Libre+Caslon+Text:wght@400;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --parchment:#F4F3EE; --floral-white:#FBFBF2; --carbon-black:#222222;
  --boxy-copper:#D66853; --copper-700:#B8512F; --copper-300:#E28F78;
  --teal-blue:#0471A6; --teal-300:#3A92BE;
  --font-serif:'Libre Caslon Text','Iowan Old Style',Georgia,serif;
  --font-sans:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
  --font-mono:'JetBrains Mono',ui-monospace,'SF Mono',Menlo,monospace;
  --bg:#1b1b19; --bg-elevated:#262623; --bg-footer:#161614;
  --fg:var(--floral-white); --fg-muted:rgba(244,243,238,.60); --fg-subtle:rgba(244,243,238,.40);
  --border:rgba(244,243,238,.12); --border-strong:rgba(244,243,238,.22);
  --accent:var(--teal-300);
  --del:var(--boxy-copper);
  --warn:#E2B778;
  --green:#7cba6a;
  --radius-md:6px; --radius-lg:12px;
}
* { box-sizing:border-box; }
body { margin:0; font-family:var(--font-sans); font-size:15px; line-height:1.55; background:var(--bg); color:var(--fg);
       -webkit-font-smoothing:antialiased; }
header { position:sticky; top:0; z-index:5; background:var(--bg); padding:18px 22px 12px; border-bottom:1px solid var(--border); }
h1 { font-family:var(--font-serif); font-weight:400; letter-spacing:-.02em; font-size:24px; margin:0 0 2px; }
header p { margin:0; color:var(--fg-muted); font-size:13px; }
main { padding:18px 22px 240px; max-width:820px; }
.card { background:var(--bg-elevated); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px 18px; margin:0 0 14px; }
.card.skipped { opacity:.5; }
.top { display:flex; gap:8px; align-items:baseline; flex-wrap:wrap; }
.tag { font-family:var(--font-mono); font-size:11px; font-weight:500; color:var(--carbon-black); background:var(--green); border-radius:var(--radius-md); padding:2px 8px; white-space:nowrap; }
.tag.when { background:var(--teal-300); }
.title { font-weight:600; }
.warn { color:var(--warn); font-size:12px; font-weight:600; }
.text { color:var(--parchment); font-size:13.5px; margin:9px 0 8px; white-space:pre-wrap; opacity:.85; max-height:80px; overflow:hidden; }
.text:hover { max-height:none; }
.route-lbl { font-size:12px; color:var(--fg-muted); margin-bottom:8px; }
.route-lbl b { color:var(--green); font-weight:600; }
.fields { display:grid; grid-template-columns:1fr 1fr; gap:10px 16px; margin-top:10px; }
.fields label { font-size:12px; color:var(--fg-muted); display:flex; flex-direction:column; gap:4px; }
.fields input, .fields select { background:#141413; color:var(--fg); border:1px solid var(--border-strong); border-radius:var(--radius-md); padding:7px 9px; font-size:13px; font-family:inherit; }
.fields input:focus, .fields select:focus { outline:2px solid var(--teal-blue); outline-offset:1px; }
.row-actions { display:flex; gap:14px; align-items:center; margin-top:12px; }
label.chk { display:inline-flex; align-items:center; gap:6px; font-size:13px; cursor:pointer; user-select:none; }
label.chk input { width:16px; height:16px; accent-color:var(--accent); }
footer { position:fixed; bottom:0; left:0; right:0; background:var(--bg-footer); border-top:1px solid var(--border); padding:11px 22px; }
footer .bar { display:flex; align-items:center; gap:14px; max-width:820px; }
#copy { background:var(--boxy-copper); color:var(--floral-white); border:0; border-radius:2px; padding:9px 16px; font-weight:600; font-family:var(--font-sans); cursor:pointer; }
#copy:hover { background:var(--copper-700); }
#status { color:var(--fg-muted); font-size:12px; }
pre { margin:8px 0 0; max-height:60px; overflow:auto; background:#121211; border:1px solid var(--border); border-radius:var(--radius-md); padding:8px; font-size:11px; color:var(--fg-muted); max-width:820px; font-family:var(--font-mono); }
</style>
</head>
<body>
<header>
  <h1>Keep Router — Notion placements</h1>
  <p>Review proposed Notion destinations. Adjust titles or projects. Timing labels (today / tomorrow / next 3 days) stage the task in that window. Skip items you don't want routed.</p>
</header>
<main id="proposals"></main>
<footer>
  <div class="bar">
    <button id="copy">Copy decisions</button>
    <span id="status">…</span>
  </div>
  <pre id="out"></pre>
</footer>
<script>
const DATA = __DATA__;
const PROPOSALS = DATA.proposals || [];
const PROJECTS = DATA.projects || [];

const WHEN_LABEL = {"today":"Today","tomorrow":"Tomorrow","next 3 days":"Next 3 Days"};
const WHEN_VALUE = {"today":"today","tomorrow":"tomorrow","next 3 days":"next-3"};
function destOf(label){
  if (label==="notion new project idea") return "New Project";
  if (label==="notion add to project") return "Add to Project";
  return "My Task List";  // notion task + timing labels
}

function esc(s){ return (s==null?"":String(s)).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function escAttr(s){ return esc(s).replace(/"/g,"&quot;"); }

const main = document.getElementById("proposals");
PROPOSALS.forEach((p, i) => {
  const warn = p.uncertain ? ` <span class="warn">⚠️ unsure</span>` : "";
  const when = WHEN_LABEL[p.routing_label] || null;
  const dest = destOf(p.routing_label);
  const card = document.createElement("section");
  card.className = "card";

  const projOpts = PROJECTS.map(pr => `<option value="${escAttr(pr)}" ${pr===p.proposed_project?"selected":""}>${esc(pr)}</option>`).join("");
  const fieldsHTML = `
      <div class="fields">
        <label>Title <input type="text" class="f-title" value="${escAttr(p.proposed_title||"")}"></label>
        <label>Destination <input type="text" class="f-dest" value="${escAttr(dest)}" readonly></label>
        ${when?`<label>When? <input type="text" class="f-when" value="${escAttr(when)}" readonly></label>`:""}
        ${p.routing_label==="notion add to project"?`<label>Project <select class="f-project"><option value="">— pick —</option>${projOpts}</select></label>`:""}
      </div>
      <div class="row-actions">
        <label class="chk"><input type="checkbox" class="f-skip">Skip (don't route)</label>
      </div>`;

  const whenTag = when ? ` <span class="tag when">${esc(when)}</span>` : "";
  card.innerHTML = `
    <div class="top"><span class="tag">${esc(p.routing_label)}</span>${whenTag}
      <span class="title">${esc(p.note_title||"(untitled)")}</span>${warn}</div>
    <div class="text">${esc(p.note_text)}</div>
    <div class="route-lbl">routing: <b>${esc(p.routing_label)}</b></div>
    ${fieldsHTML}`;
  main.appendChild(card);
});

function readCard(card, p) {
  const skip = card.querySelector(".f-skip")?.checked || false;
  if (skip) {
    card.classList.add("skipped");
    return { note_id:p.note_id, action:"skip" };
  }
  card.classList.remove("skipped");
  const title = card.querySelector(".f-title")?.value.trim() || p.proposed_title || p.note_title;
  const project = card.querySelector(".f-project")?.value || null;
  const when = WHEN_VALUE[p.routing_label] || null;
  return { note_id:p.note_id, action:"confirm", title, destination:destOf(p.routing_label), project, when };
}

window.getReview = function () {
  return { decisions: PROPOSALS.map((p,i) => readCard(main.children[i], p)) };
};

function refresh() {
  const r = window.getReview();
  document.getElementById("out").textContent = JSON.stringify(r, null, 1);
  const confirmed = r.decisions.filter(x => x.action==="confirm").length;
  const skipped = r.decisions.filter(x => x.action==="skip").length;
  document.getElementById("status").textContent = `${confirmed} confirmed, ${skipped} skipped / ${r.decisions.length} total`;
}
main.addEventListener("change", refresh);
main.addEventListener("input", refresh);
document.getElementById("copy").addEventListener("click", () => {
  navigator.clipboard.writeText(JSON.stringify(window.getReview())).then(()=>{
    document.getElementById("status").textContent = "copied to clipboard ✓";
  });
});
refresh();
</script>
</body>
</html>
''';


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: keep_router_page.py <input.json> [output.html]")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = (Path(sys.argv[2]) if len(sys.argv) > 2
           else Path(__file__).resolve().parent.parent / "review" / "index.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out.write_text(TEMPLATE.replace("__DATA__", blob), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
