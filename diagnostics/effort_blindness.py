"""Read-only: (1) effort recorded in calls.jsonl / scored rows, runner commands from transcripts;
(2) first appearance of grid catch figures in this session's transcript. Run from repo root."""
import glob, json, os, re
from collections import Counter

HOME = os.path.expanduser("~/.claude/projects")
CUR = f"{HOME}/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl"
DESK = f"{HOME}/-Users-imani-Desktop-Oversight-Capacity/c7e59a3e-63ed-488e-90d6-8756b641fecc.jsonl"

print("== 1a. keys present in calls.jsonl records")
for root in ("results_grid", "results_pilot"):
    recs = [json.loads(l) for l in open(f"{root}/calls.jsonl")]
    keys = Counter(k for r in recs for k in r)
    print(f"{root}: {len(recs)} records; keys {dict(keys)}; by model {dict(Counter(r['model'] for r in recs))}")
print("== 1b. 'effort' field in scored rows (one row per cell; the runner writes its configured EFFORT[MONITOR])")
for root in ("results_grid", "results_pilot"):
    rows = [json.load(open(f)) for f in glob.glob(f"{root}/scored/*.json")]
    print(f"{root}: " + ", ".join(f"{c} effort={e}: {k}" for (c, e), k in sorted(Counter((r['cond'], r.get('effort')) for r in rows).items())))

def blocks(path, stop_marker=None):
    for i, line in enumerate(open(path), 1):
        if stop_marker and stop_marker in line: return
        o = json.loads(line); c = (o.get("message") or {}).get("content")
        if isinstance(c, str): yield i, o, "user-text" if o.get("type") == "user" else "text", c; continue
        for b in c if isinstance(c, list) else []:
            t = b.get("type")
            if t == "text": yield i, o, f"{o.get('type')}-text", b["text"]
            elif t == "tool_use": yield i, o, "tool_use", json.dumps(b.get("input"))
            elif t == "tool_result":
                x = b.get("content"); yield i, o, "tool_result", x if isinstance(x, str) else "".join(y.get("text", "") for y in x or [] if isinstance(y, dict))

print("== 1c. runner.py run commands (non-mock) writing results_grid or results_pilot")
for path in (DESK, CUR):
    for i, o, kind, s in blocks(path, "2026-11-10_effort_blindness"):
        if kind != "tool_use": continue
        cmd = json.loads(s).get("command", "")
        if "runner.py run" in cmd and "--mock" not in cmd and re.search(r"--root results_(grid|pilot)\b", cmd):
            for m in re.finditer(r"runner\.py run[^>;]*", cmd):
                print(f"{os.path.basename(path)[:8]} line {i} {o.get('timestamp')} | {m.group(0).strip()}")

print("== 2. this session: '=== GRID' and real grid catch figures, before this request")
FIG = re.compile(r"74\.9%|68\.9%|67\.4%|57\.4%|slope_stateful\s+-2\.71|N=64: 57\.4")
first_fig = None
for i, o, kind, s in blocks(CUR, "2026-11-10_effort_blindness"):
    if "=== GRID" in s:
        k = s.find("=== GRID"); ctx = s[k:k + 160].replace("\\n", "\n").split("\n")
        rows_after = [l for l in ctx[1:4] if l.strip()]
        print(f"GRID   line {i} {o.get('timestamp')} {kind}: {ctx[0][:70]!r} | next lines: {rows_after[:2]!r}")
    m = FIG.search(s)
    if m and first_fig is None:
        first_fig = (i, o.get("timestamp"), kind, s[max(0, m.start() - 120):m.end() + 60])
print("FIRST grid catch figure:", first_fig)
