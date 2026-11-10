"""Read-only: every transcript block before the Amendment 7 commit (2026-11-10T03:26:06Z) that carries
results_grid-derived content: tool calls whose input reads results_grid (or pilot_gates.py, which reads
results_grid/logs) with their results; monitor events; assistant text mentioning the grid."""
import json, os, re

P = os.path.expanduser("~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl")
CUT = "2026-11-10T03:26:06"
uses, results, events, texts = {}, {}, [], []
for i, line in enumerate(open(P), 1):
    o = json.loads(line); ts = o.get("timestamp")
    if ts is None: continue                      # duplicate request-blob records carry no timestamp
    if ts >= CUT: break
    c = (o.get("message") or {}).get("content")
    if isinstance(c, str):
        if "<task-notification>" in c and ("T0 grid" in c or "results_grid" in c): events.append((i, ts, c))
        continue
    for b in c if isinstance(c, list) else []:
        t = b.get("type")
        if t == "tool_use":
            s = json.dumps(b.get("input"))
            if "results_grid" in s or "pilot_gates.py" in s: uses[b["id"]] = (i, ts, b["name"], (b.get("input") or {}).get("description", ""))
        elif t == "tool_result" and b.get("tool_use_id") in uses:
            x = b.get("content"); results[b["tool_use_id"]] = (i, ts, x if isinstance(x, str) else "".join(y.get("text", "") for y in x or [] if isinstance(y, dict)))
        elif t == "text" and o.get("type") == "user" and "<task-notification>" in b.get("text", "") and "grid" in b.get("text", ""):
            events.append((i, ts, b["text"]))
        elif t == "text" and o.get("type") == "assistant" and re.search(r"grid", b.get("text", ""), re.I) and re.search(r"\d", b.get("text", "")):
            texts.append((i, ts, b["text"]))
print(f"cutoff {CUT}Z; {len(uses)} tool calls reading results_grid or pilot_gates.py")
for tid, (i, ts, name, desc) in uses.items():
    r = results.get(tid)
    print(f"\n### tool_use line {i} {ts} {name}: {desc}")
    print(f"--- result line {r[0]} {r[1]}:\n{r[2][:1800]}" if r else "--- no result before cutoff")
print("\n### monitor events")
for i, ts, s in events:
    m = re.findall(r"<event>(.*?)</event>|<summary>(.*?)</summary>", s, re.S)
    print(f"line {i} {ts}: " + " | ".join(a or b for a, b in m))
print("\n### assistant text mentioning grid with digits (first 300 chars)")
for i, ts, s in texts: print(f"line {i} {ts}: {s[:300]!r}")
