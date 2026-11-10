"""Read-only T0 grid diagnostics a-e. Run from repo root. Re-scores the final raw response per log with
score.py rules (dedupe by action, cap at max_flags) and asserts agreement with scored/*.json."""
import glob, json, os, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.getcwd())
from score import parse, max_flags

R, NS, TYPES = "results_grid", [1, 4, 16, 64], ["local", "stateful", "contradiction"]
calls = [json.loads(l) for l in open(f"{R}/calls.jsonl")]
by_tag = {c["tag"]: c for c in calls}
logs = []
for f in glob.glob(f"{R}/scored/*.json"):
    sc = json.load(open(f)); key = os.path.basename(f)[:-5]
    assert sc["cond"] == "T0" and sc["parse_ok"], key
    raws = json.load(open(f"{R}/raw/{key}.json"))["raw"]
    truth = json.load(open(f"{R}/logs/T256_N{sc['n']}_s{sc['seed']}.truth.json"))
    ded, seen = [], set()
    for fl in parse(raws[-1]):
        if fl["action"] not in seen: seen.add(fl["action"]); ded.append(fl)
    ded = ded[:max_flags(truth)]
    flagged = {fl["action"] for fl in ded}
    for t in TYPES:
        assert sum(e["type"] == t and e["action"] in flagged for e in truth["errors"]) == sc["by_type"][t]["caught"], key
    assert len(ded) == sc["n_flags"] and len(raws) == sc["attempts"], key
    st = [e for e in truth["errors"] if e["type"] == "stateful"]
    logs.append({"n": sc["n"], "seed": sc["seed"], "rep": sc["rep"], "ded": ded, "flagged": flagged, "truth": truth, "st": st,
                 "caught": sum(e["action"] in flagged for e in st), "think": by_tag[f"{key}#{len(raws) - 1}"]["thinking"],
                 "engaged": sum(e["action"] in flagged for e in st) >= len(st) / 2})
assert len(logs) == 400
L = {(d["seed"], d["n"], d["rep"]): d for d in logs}
seeds = sorted({d["seed"] for d in logs})
pct = lambda k, n: f"{k}/{n} = {k / n:.1%}" if n else "0/0"
print(f"validated: {len(logs)} logs re-scored; per-type caught and n_flags match scored/*.json\n")

print("a) Thinking by N. Calls = every monitor call in calls.jsonl incl. parse retries; split uses the scored attempt's thinking.")
print("N  | calls | calls thinking>0 | mean thinking tokens | stateful catch, thinking>0 (logs) | stateful catch, thinking=0 (logs)")
for n in NS:
    cs = [c for c in calls if c["tag"].startswith(f"T256_N{n}_s")]
    k = sum(c["thinking"] > 0 for c in cs)
    parts = []
    for cond in (lambda d: d["think"] > 0, lambda d: d["think"] == 0):
        ds = [d for d in logs if d["n"] == n and cond(d)]
        parts.append(f"{pct(sum(d['caught'] for d in ds), sum(len(d['st']) for d in ds))} ({len(ds)})")
    print(f"{n:<2} | {len(cs)} | {pct(k, len(cs))} | {sum(c['thinking'] for c in cs) / len(cs):.1f} | {parts[0]} | {parts[1]}")

print("\nb) Engagement transitions, (seed, rep) pairs, rep r at N=1 paired with rep r at N=64; engaged = caught >= planted/2")
tr = Counter((L[(s, 1, r)]["engaged"], L[(s, 64, r)]["engaged"]) for s in seeds for r in (1, 2))
lab = {True: "engaged", False: "disengaged"}
for a in (True, False):
    for b in (True, False): print(f"  N=1 {lab[a]:10s} -> N=64 {lab[b]:10s}: {tr[(a, b)]}")
print(f"  total pairs: {sum(tr.values())}")
pairs_all = sum(all(not L[(s, n, r)]["engaged"] for n in NS) for s in seeds for r in (1, 2))
seeds_all = sum(all(not L[(s, n, r)]["engaged"] for n in NS for r in (1, 2)) for s in seeds)
print(f"  (seed, rep) pairs disengaged at all 4 N: {pairs_all}/100")
print(f"  seeds disengaged in all 8 logs (4 N x 2 reps): {seeds_all}/50")

print("\nc) Rep agreement on engagement by N (50 seeds)")
print("N  | both engaged | both disengaged | split | agreement")
for n in NS:
    c = Counter((L[(s, n, 1)]["engaged"], L[(s, n, 2)]["engaged"]) for s in seeds)
    split = c[(True, False)] + c[(False, True)]
    print(f"{n:<2} | {c[(True, True)]} | {c[(False, False)]} | {split} | {pct(c[(True, True)] + c[(False, False)], 50)}")

print("\nd) Stateful catch by N, both reps pooled over seeds")
print("by error quartile (truth 'quartile'):")
print("N  | " + " | ".join(f"Q{q}" for q in range(4)))
for n in NS:
    cells = []
    for q in range(4):
        es = [(e, d) for d in logs if d["n"] == n for e in d["st"] if e["quartile"] == q]
        cells.append(pct(sum(e["action"] in d["flagged"] for e, d in es), len(es)))
    print(f"{n:<2} | " + " | ".join(cells))
fl = Counter(e["flavor"] for d in logs for e in d["st"])
print(f"by chain flavor (truth 'flavor'): levels present on stateful errors = {dict(fl)}")
for n in NS:
    for v in sorted(fl):
        es = [(e, d) for d in logs if d["n"] == n for e in d["st"] if e["flavor"] == v]
        print(f"  N={n:<2} flavor={v}: {pct(sum(e['action'] in d['flagged'] for e, d in es), len(es))}")

print("\ne) Flags per log by N (deduped, capped; mean over 100 logs)")
lbls = ["local", "stateful", "contradiction", "other/missing"]
print("by monitor-assigned 'type' label:")
print("N  | " + " | ".join(lbls) + " | total")
for n in NS:
    ds = [d for d in logs if d["n"] == n]
    c = Counter((fl.get("type") if fl.get("type") in TYPES else "other/missing") for d in ds for fl in d["ded"])
    print(f"{n:<2} | " + " | ".join(f"{c[x] / len(ds):.2f}" for x in lbls) + f" | {sum(c.values()) / len(ds):.2f}")
print("by ground-truth category of the flagged action:")
cats = ["local", "stateful", "contradiction", "clean (FP)"]
print("N  | " + " | ".join(cats) + " | total")
for n in NS:
    ds = [d for d in logs if d["n"] == n]
    c = Counter()
    for d in ds:
        et = {e["action"]: e["type"] for e in d["truth"]["errors"]}
        for fl in d["ded"]: c[et.get(fl["action"], "clean (FP)")] += 1
    print(f"{n:<2} | " + " | ".join(f"{c[x] / len(ds):.2f}" for x in cats) + f" | {sum(c.values()) / len(ds):.2f}")
other = Counter(str(fl.get("type")) for d in logs for fl in d["ded"] if fl.get("type") not in TYPES)
print(f"other/missing label values (all N): {dict(other)}")
