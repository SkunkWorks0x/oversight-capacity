"""Read-only numbers for reports/2026-11-10_design_dossier.md. Run from repo root. No API calls.
Inputs: results_grid/logs/T256_N{1,4,16,64}_s{0..49} and results_grid/calls.jsonl records tagged T256_N*_s*_T0#0 / _T0_r2#0."""
import json, os, re, statistics, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.getcwd())
from gen import build

R, NS, SEEDS = "results_grid", [1, 4, 16, 64], range(50)
LINE = re.compile(r"^\[t=(\d+)\] \[(S\d+)\] \[A(\d+)\] tool=(\w+) ")
LABEL = re.compile(r"S\d{2}(?=[\]-])")   # stream label: the [Sxx] field and the Sxx- slot prefix
ROLES = {"stateful": ["setup", "middle", "cancel", "final"], "contradiction": ["refund", "appeal", "message"],
         "cancel": ["book", "cancel"], "appeal": ["refund", "appeal"], "local": ["final"]}

def load(n, s):
    base = f"{R}/logs/T256_N{n}_s{s}"
    text, truth = open(base + ".log").read(), json.load(open(base + ".truth.json"))
    t2, tr2 = build(n, s, 256, n_err=16, subtlety="d2h")
    assert text == t2 and truth == json.loads(json.dumps(tr2)), base
    header, body = text.split("\n\n", 1)
    return header, body.splitlines(), truth

def labels(truth):
    lab = {}
    for kind, rows in (("error", truth["errors"]), ("decoy", truth["decoys"]), ("noise", truth["noise"])):
        for e in rows:
            for i, a in enumerate(e["chain"]):
                role = ROLES[e["type"]][i]
                if kind == "error" and a == e["action"]:
                    lab[a] = f"ERROR {e['type']}" + (f" ({e['flavor']})" if e["type"] == "local" else "")
                else:
                    lab[a] = f"clean ({kind} chain {e['type']}{' ' + e['flavor'] if e['flavor'] and kind != 'error' else ''}: {role})"
    return lab

def group(truth, a):
    for kind, rows in (("error", truth["errors"]), ("decoy", truth["decoys"]), ("noise", truth["noise"])):
        for e in rows:
            if a in e["chain"]: return "local error" if e["type"] == "local" else f"{kind} chain"
    return "background"

def msg_kind(line):
    for k, p in (("reminder", "Reminder:"), ("confirm", "refund is on its way"), ("decline", "could not be approved"), ("generic", "Thanks for reaching out")):
        if p in line: return k

L = {(n, s): load(n, s) for n in NS for s in SEEDS}
print(f"integrity: {len(L)} logs in {R}/logs equal gen.build(n, seed, 256, n_err=16, subtlety='d2h') byte for byte (log and truth)")
assert all(L[(n, s)][0] == L[(1, 0)][0] for n in NS for s in SEEDS)
print("header identical in all 200 logs")

# ---- section 2: seed 0 excerpts
_, l1, t1 = L[(1, 0)]
for n in NS:
    assert [(e["chain"], e["type"], e["flavor"]) for e in L[(n, 0)][2]["errors"]] == [(e["chain"], e["type"], e["flavor"]) for e in t1["errors"]]
pick = [("stateful error chain", next(e for e in t1["errors"] if e["type"] == "stateful")),
        ("decoy chain (first stateful decoy)", next(e for e in t1["decoys"] if e["type"] == "stateful")),
        ("contradiction error chain", next(e for e in t1["errors"] if e["type"] == "contradiction")),
        ("local error", next(e for e in t1["errors"] if e["type"] == "local"))]
print("\n== S2 seed 0 header ==")
print(L[(1, 0)][0])
for n in (1, 64):
    _, ls, tr = L[(n, 0)]; lab = labels(tr)
    print(f"\n== S2 seed 0 N={n}: lines 1-12 ==")
    for l in ls[:12]: print(f"{l}   <- {lab.get('A' + LINE.match(l).group(3), 'clean (background)')}")
    for name, e in pick:
        print(f"\n== S2 seed 0 N={n}: {name} {e['chain']} ==")
        for a in e["chain"]: print(f"{ls[int(a[1:]) - 1]}   <- {lab[a]}")

# ---- section 3 support: timeline order and chain/stream sharing
print("\n== S3 timeline: per log, action ids 1..256 in order and t non-decreasing; stream switches between adjacent lines ==")
for n in NS:
    sw, per = [], set()
    for s in SEEDS:
        m = [LINE.match(l).groups() for l in L[(n, s)][1]]
        assert [int(x[2]) for x in m] == list(range(1, 257)) and all(int(a[0]) <= int(b[0]) for a, b in zip(m, m[1:]))
        sw.append(sum(a[1] != b[1] for a, b in zip(m, m[1:]))); per |= set(Counter(x[1] for x in m).values())
    print(f"N={n:2d}: ordered by action id in 50/50 logs; actions per stream {sorted(per)}; adjacent-line stream switches mean {statistics.mean(sw):.1f} (of 255)")
print("\n== S3 chains: all events of a chain on one stream (errors non-local, decoys, noise) ==")
for n in NS:
    c = Counter()
    for s in SEEDS:
        _, ls, tr = L[(n, s)]
        for kind in ("errors", "decoys", "noise"):
            for e in tr[kind]:
                if len(e["chain"]) > 1: c[(kind, len({LINE.match(ls[int(a[1:]) - 1]).group(2) for a in e["chain"]}) == 1)] += 1
    print(f"N={n:2d}: " + "  ".join(f"{k}: one stream {c[(k, True)]}, split {c[(k, False)]}" for k in ("errors", "decoys", "noise")))

# ---- section 4: line diff N=1 vs N=64, generic share, tokens
print("\n== S4 line diff N=1 vs N=64, 50 seeds x 256 positions ==")
by_tool, by_group, cross = defaultdict(Counter), defaultdict(Counter), Counter()
for s in SEEDS:
    _, a1, tr = L[(1, s)]; _, a64, _ = L[(64, s)]
    for x, y in zip(a1, a64):
        mx, my = LINE.match(x), LINE.match(y)
        assert mx.group(4) == my.group(4) and mx.group(3) == my.group(3) and mx.group(1) == my.group(1)
        cls = "identical" if x == y else "label-only" if LABEL.sub("S##", x) == LABEL.sub("S##", y) else "content"
        g = group(tr, "A" + mx.group(3))
        by_tool[mx.group(4)][cls] += 1; by_group[g][cls] += 1
        if g == "background" and mx.group(4) == "send_message": cross[(msg_kind(x), msg_kind(y))] += 1
print("tool and position id and t identical at every position: yes (asserted)")
for title, d in (("by tool", by_tool), ("by line origin", by_group)):
    print(f"{title:15s} | identical | label-only | content | total")
    for k in sorted(d): print(f"{k:15s} | {d[k]['identical']:9d} | {d[k]['label-only']:10d} | {d[k]['content']:7d} | {sum(d[k].values())}")
    tot = Counter(); [tot.update(v) for v in d.values()]
    print(f"{'ALL':15s} | {tot['identical']:9d} | {tot['label-only']:10d} | {tot['content']:7d} | {sum(tot.values())}\n")
print("background send_message kind, N=1 (rows) -> N=64 (cols), positions pooled over 50 seeds")
K = ["reminder", "confirm", "decline", "generic"]
print("N=1 \\ N=64 | " + " | ".join(f"{k:8s}" for k in K))
for a in K: print(f"{a:10s} | " + " | ".join(f"{cross[(a, b)]:8d}" for b in K))

print("\n== S4 generic share of background messages (truth clean_msg_kinds; analysis.py definition) and log size ==")
calls = {}
for r in map(json.loads, open(f"{R}/calls.jsonl")):
    calls[r["tag"]] = r["in"]
base_tok = {s: calls[f"T256_N1_s{s}_T0#0"] for s in SEEDS}
for n in NS:
    g = [L[(n, s)][2]["clean_msg_kinds"]["generic"] / sum(L[(n, s)][2]["clean_msg_kinds"].values()) for s in SEEDS]
    k = Counter(); [k.update(L[(n, s)][2]["clean_msg_kinds"]) for s in SEEDS]
    tok = [calls[f"T256_N{n}_s{s}_T0#0"] for s in SEEDS]
    assert tok == [calls[f"T256_N{n}_s{s}_T0_r2#0"] for s in SEEDS]
    ch = [L[(n, s)][2]["chars"] for s in SEEDS]
    dv = [(calls[f"T256_N{n}_s{s}_T0#0"] / base_tok[s] - 1) * 100 for s in SEEDS]
    print(f"N={n:2d}: generic share mean {statistics.mean(g):.1%} (SD {statistics.stdev(g):.1%}, {min(g):.1%}-{max(g):.1%}); pooled kinds {dict(k)}"
          f" | monitor input tokens mean {statistics.mean(tok):.0f} ({min(tok)}-{max(tok)}), vs N=1 same seed {statistics.mean(dv):+.2f}% ({min(dv):+.2f}..{max(dv):+.2f})"
          f" | log chars mean {statistics.mean(ch):.0f}")
print("input tokens: served 'in' of attempt #0, reps 1 and 2 equal in all 200 (seed, N) pairs (asserted)")

# ---- section 5: stateful errors, setup/cancel/error stream membership
print("\n== S5 stateful errors: streams of setup (chain[0]), cancel (chain[2]), error (chain[3]) ==")
for n in (4, 16, 64):
    one = split = mid = 0
    for s in SEEDS:
        _, ls, tr = L[(n, s)]
        for e in tr["errors"]:
            if e["type"] != "stateful": continue
            st = [LINE.match(ls[int(a[1:]) - 1]).group(2) for a in e["chain"]]
            if len({st[0], st[2], st[3]}) == 1: one += 1
            else: split += 1
            mid += st[1] == st[0]
    print(f"N={n:2d}: {one + split} stateful errors; setup+cancel+error in one stream {one} ({one / (one + split):.0%}), split {split}; middle on same stream {mid}")
