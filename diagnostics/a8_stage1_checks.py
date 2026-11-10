"""Amendment 8 Stage 1 provenance and a descriptive split. Offline; no API calls. Run from repo root.
1. Input tokens (served 'in', calls.jsonl) per seed and rep: arm B minus arm A; arm A minus the grid's N=64 call for the
   same seed and rep. Whether any saved file under results_a8_A / results_a8_B records which prompt a cell used.
2. Stateful catch per arm, cells split by thinking tokens > 0 vs 0 (thinking from each cell's calls.jsonl record)."""
import json, os
from collections import Counter

SEEDS, REPS = range(50), ("", "_r2")
ROOTS = {"A": "results_a8_A", "B": "results_a8_B", "grid": "results_grid"}

def calls(root):
    out = {}
    for r in map(json.loads, open(f"{root}/calls.jsonl")):
        assert r["tag"] not in out, r["tag"]; out[r["tag"]] = r
    return out
C = {k: calls(v) for k, v in ROOTS.items()}
tags = [f"T256_N64_s{s}_T0{x}#0" for s in SEEDS for x in REPS]
assert all(t in C[k] for t in tags for k in C) and len(C["A"]) == len(C["B"]) == 100

print("== 1a. input tokens, arm B minus arm A, per seed and rep (100 cells) ==")
d = [C["B"][t]["in"] - C["A"][t]["in"] for t in tags]
print(f"min {min(d)}, max {max(d)}, distinct values {dict(Counter(d))}")
print("\n== 1b. input tokens, arm A minus the grid's N=64 call, same seed and rep (100 cells) ==")
g = [C["A"][t]["in"] - C["grid"][t]["in"] for t in tags]
print(f"min {min(g)}, max {max(g)}, distinct values {dict(Counter(g))}")
print(f"(within arm A, rep 2 minus rep 1: distinct values {dict(Counter(C['A'][f'T256_N64_s{s}_T0_r2#0']['in'] - C['A'][f'T256_N64_s{s}_T0#0']['in'] for s in SEEDS))})")

print("\n== 1c. does any saved file record which prompt a cell used? ==")
keys = {"scored": set(), "raw": set(), "calls.jsonl": set()}
hits = Counter()
needles = {"monitor_prompt": "monitor_prompt", "A-only text": "Judge each agent only against its own earlier actions",
           "B-only text": "contradicts earlier tool results for that customer"}
for arm in ("A", "B"):
    root = ROOTS[arm]
    for f in os.listdir(f"{root}/scored"): keys["scored"] |= set(json.load(open(f"{root}/scored/{f}")))
    for f in os.listdir(f"{root}/raw"): keys["raw"] |= set(json.load(open(f"{root}/raw/{f}")))
    keys["calls.jsonl"] |= {k for r in C[arm].values() for k in r}
    for dirpath, _, files in os.walk(root):
        if os.path.basename(dirpath) == "logs": continue
        for f in files:
            text = open(os.path.join(dirpath, f), errors="replace").read()
            for name, s in needles.items(): hits[(arm, name)] += s in text
for k, v in keys.items(): print(f"{k} fields: {sorted(v)}")
print("files (outside logs/) containing each string: " + ", ".join(f"arm {a} {n}: {hits[(a, n)]}" for a in "AB" for n in needles))

print("\n== 2. stateful catch per arm, cells split by thinking tokens > 0 vs 0 ==")
for arm in ("A", "B"):
    split = {True: [0, 0, 0], False: [0, 0, 0]}   # cells, caught, planted
    for s in SEEDS:
        for x in REPS:
            r = json.load(open(f"{ROOTS[arm]}/scored/T256_N64_s{s}_T0{x}.json")); assert r["attempts"] == 1
            k = (C[arm][f"T256_N64_s{s}_T0{x}#0"]["thinking"] or 0) > 0
            st = r["by_type"]["stateful"]; split[k][0] += 1; split[k][1] += st["caught"]; split[k][2] += st["planted"]
    print(f"arm {arm}: " + "; ".join(f"thinking {'> 0' if k else '= 0'}: {c} cells, stateful {cau}/{pl} = {cau / pl:.1%}" if pl else f"thinking {'> 0' if k else '= 0'}: 0 cells"
                                for k, (c, cau, pl) in ((True, split[True]), (False, split[False]))))
