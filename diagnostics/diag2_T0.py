"""Read-only T0 grid diagnostics f-h. Run from repo root. Same re-scoring and validation as diag_T0.py."""
import glob, json, os, statistics, sys
from collections import Counter
sys.path.insert(0, os.getcwd())
from score import parse, max_flags

R, NS, TYPES = "results_grid", [1, 4, 16, 64], ["local", "stateful", "contradiction"]
logs = []
for f in glob.glob(f"{R}/scored/*.json"):
    sc = json.load(open(f)); key = os.path.basename(f)[:-5]
    raws = json.load(open(f"{R}/raw/{key}.json"))["raw"]
    truth = json.load(open(f"{R}/logs/T256_N{sc['n']}_s{sc['seed']}.truth.json"))
    ded, seen = [], set()
    for fl in parse(raws[-1]):
        if fl["action"] not in seen: seen.add(fl["action"]); ded.append(fl)
    flagged = {fl["action"] for fl in ded[:max_flags(truth)]}
    for t in TYPES:
        assert sum(e["type"] == t and e["action"] in flagged for e in truth["errors"]) == sc["by_type"][t]["caught"], key
    errs = {e["action"] for e in truth["errors"]}
    fps = flagged - errs
    assert len(fps) == sc["fp"] and sum(a in {x for d in truth["decoys"] for x in d["chain"]} for a in fps) == sc["fp_decoy"], key
    logs.append({"n": sc["n"], "seed": sc["seed"], "rep": sc["rep"], "flagged": flagged, "fps": fps, "truth": truth,
                 "st": [e for e in truth["errors"] if e["type"] == "stateful"]})
assert len(logs) == 400
print(f"validated: {len(logs)} logs; per-type caught, fp and fp_decoy match scored/*.json\n")

# role of every chain action; positions must not overlap
EVENT = {0: "setup", 1: "middle", 2: "cancel"}
def roles(truth):
    r = {}
    for e in truth["errors"]:
        for i, a in enumerate(e["chain"][:-1]):
            assert a not in r; r[a] = (f"{e['type']}-error chain", EVENT.get(i, f"pos{i}") if e["type"] == "stateful" else f"pos{i}", e["action"])
    for kind, key in (("decoy chain", "decoys"), ("noise pair", "noise")):
        for c in truth[key]:
            for a in c["chain"]:
                assert a not in r; r[a] = (kind, None, None)
    return r

print("f) False positives by landing site (deduped, capped flags on actions that are not planted errors)")
cats = ["stateful-error chain", "contradiction-error chain", "local-error chain", "decoy chain", "noise pair", "background"]
print("N  | FP total | " + " | ".join(cats))
detail = {}
for n in NS:
    c, d = Counter(), Counter()
    for lg in (x for x in logs if x["n"] == n):
        r = roles(lg["truth"])
        for a in lg["fps"]:
            kind, ev, err = r.get(a, ("background", None, None))
            c[kind.replace("-error chain", "-error chain")] += 1
            if kind == "stateful-error chain":
                d[(ev, "error missed same call" if err not in lg["flagged"] else "error caught same call")] += 1
    detail[n] = d
    print(f"{n:<2} | {sum(c.values())} | " + " | ".join(str(c[k]) for k in cats))
print("  (1) stateful-error chain FPs by event and by whether that chain's error was flagged in the same call:")
print("  N  | " + " | ".join(f"{ev}: missed / caught" for ev in EVENT.values()))
for n in NS:
    print(f"  {n:<2} | " + " | ".join(f"{detail[n][(ev, 'error missed same call')]} / {detail[n][(ev, 'error caught same call')]}" for ev in EVENT.values()))

print("\ng) EXPLORATORY SENSITIVITY - NOT PRE-REGISTERED. Stateful catch by N if a flag on any action in the error's own chain")
print("   (setup, middle, cancel or the error) counts as a catch. Both reps pooled over seeds. analysis.py unchanged.")
print("N  | primary (error action flagged) | chain rule (any chain action flagged) | caught only via chain rule")
for n in NS:
    es = [(e, lg) for lg in logs if lg["n"] == n for e in lg["st"]]
    p = sum(e["action"] in lg["flagged"] for e, lg in es)
    ch = sum(any(a in lg["flagged"] for a in e["chain"]) for e, lg in es)
    print(f"{n:<2} | {p}/{len(es)} = {p / len(es):.1%} | {ch}/{len(es)} = {ch / len(es):.1%} | {ch - p}")

print("\nh) Stateful catch by N, by tercile of setup-to-error gap (truth 'gap', in actions). Both reps pooled over seeds.")
gap = {}
for lg in logs:
    for e in lg["st"]:
        k = (lg["seed"], e["action"]); assert gap.setdefault(k, e["gap"]) == e["gap"]   # same gap at every N
g = list(gap.values())
c1, c2 = statistics.quantiles(g, n=3, method="inclusive")
bins = [("T1", lambda x: x <= c1), ("T2", lambda x: c1 < x <= c2), ("T3", lambda x: x > c2)]
print(f"   {len(g)} distinct stateful errors (seed, action); cut points {c1:g}, {c2:g} (inclusive quantiles)")
for name, f in bins:
    v = [x for x in g if f(x)]
    print(f"   {name}: gap {min(v)}-{max(v)}, {len(v)} errors")
print("N  | " + " | ".join(name for name, _ in bins))
for n in NS:
    cells = []
    for _, f in bins:
        es = [(e, lg) for lg in logs if lg["n"] == n for e in lg["st"] if f(e["gap"])]
        k = sum(e["action"] in lg["flagged"] for e, lg in es); cells.append(f"{k}/{len(es)} = {k / len(es):.1%}")
    print(f"{n:<2} | " + " | ".join(cells))
