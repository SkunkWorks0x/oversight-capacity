"""Offline: does replay.py (unchanged) reproduce truth on all 200 results_grid logs when state is global?
Variants: per-stream (as written); global = every [Sxx] field set to [S01] so replay keeps one state;
global, label-blind = also every slot prefix Sxx- set to S01-. Compared with truth errors {action: type}."""
import json, os, re, sys
sys.path.insert(0, os.getcwd())
from replay import violations

NS, SEEDS = [1, 4, 16, 64], range(50)
FIELD, PREFIX = re.compile(r"\[S\d{2}\]"), re.compile(r"\bS\d{2}-")
VARIANTS = {"per-stream": lambda t: t, "global": lambda t: FIELD.sub("[S01]", t),
            "global, label-blind": lambda t: PREFIX.sub("S01-", FIELD.sub("[S01]", t))}
mism = []
print("variant              | " + " | ".join(f"N={n:2d} exact" for n in NS) + " | total")
for name, f in VARIANTS.items():
    ok = {}
    for n in NS:
        ok[n] = 0
        for s in SEEDS:
            base = f"results_grid/logs/T256_N{n}_s{s}"
            truth = {e["action"]: e["type"] for e in json.load(open(base + ".truth.json"))["errors"]}
            got = violations(f(open(base + ".log").read()))
            if got == truth: ok[n] += 1
            else: mism.append((name, n, s, {a: (truth.get(a), got.get(a)) for a in set(truth) | set(got) if truth.get(a) != got.get(a)}))
    print(f"{name:20s} | " + " | ".join(f"{ok[n]:5d}/50  " for n in NS) + f" | {sum(ok.values())}/200")
print(f"\nmismatches (variant, N, seed, {{action: (truth, replay)}}): {len(mism)}")
for m in mism: print(" ", m)
