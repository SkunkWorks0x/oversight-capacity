"""Amendment 8 analysis (exploratory, post hoc): prompt A vs prompt B at N=64; with --a1/--b1, Amendment 9 (Stage 2,
descriptive) adds A and B at N=1. Offline; no API calls. Run from repo root.
Stage 1: python diagnostics/analysis_global.py --a results_a8_A --b results_a8_B [--gates-only] [--grid results_grid] [--boot 10000] [--boot-seed 0]
Stage 2: add --a1 results_a9_A --b1 results_a9_B
Stage 1 primary: B - A pooled stateful catch at N=64 (sum caught / sum planted over seeds, reps averaged per cell),
seed-level paired percentile bootstrap (A and B resampled on the same seeds), 95% CI. Gates per arm come first
(--gates-only stops there); a gate failure means the estimate is printed and the three readings are not. Readings:
(1) CI above 0; (2) CI upper bound below the grid's A drop N=1 -> N=64 (unrounded); (3) CI below 0.
Stage 2 outputs (descriptive; all four cells of a seed resampled together): B - A at N=1; B drop = B N=1 - B N=64;
A drop = A N=1 - A N=64; A drop - B drop. Reading on the B drop interval; prediction B drop point estimate < +10 points;
ceiling flag if either arm is >= 95% at N=1. Secondary outputs are descriptive."""
import argparse, json, os, random, re, statistics, sys
sys.path.insert(0, os.getcwd())
from analysis import ci
from runner import MONITOR, PRICE, wilson

SEEDS, REPS, TYPES = range(50), (1, 2), ["local", "stateful", "contradiction"]
tag_re = lambda n: re.compile(rf"^T256_N{n}_s(\d+)_T0(?:_r2)?#\d$")
key = lambda s, rep, n=64: f"T256_N{n}_s{s}_T0" + ("_r2" if rep == 2 else "")
same = lambda p, q: os.path.exists(p) and open(p, "rb").read() == open(q, "rb").read()
avg = lambda rows, f: [statistics.mean(f(rows[(s, r)]) for r in REPS) for s in SEEDS]
stateful = lambda r: r["by_type"]["stateful"]["caught"]
engaged_f = lambda r: r["by_type"]["stateful"]["caught"] >= r["by_type"]["stateful"]["planted"] / 2

def load(root, grid, n=64):
    for s in SEEDS:
        for ext in (".log", ".truth.json"):
            f = f"logs/T256_N{n}_s{s}{ext}"
            if not same(os.path.join(root, f), os.path.join(grid, f)):
                sys.exit(f"ABORT: {root}/{f} is missing or not byte-identical to {grid}/{f}")
    files = sorted(os.listdir(os.path.join(root, "scored")))
    rows = {(s, r): json.load(open(os.path.join(root, "scored", key(s, r, n) + ".json")))
            for s in SEEDS for r in REPS if key(s, r, n) + ".json" in files}
    p = os.path.join(root, "calls.jsonl")
    calls = [json.loads(l) for l in open(p)] if os.path.exists(p) else []
    return files, rows, calls

def rate(rows, t): return sum(r["by_type"][t]["caught"] for r in rows), sum(r["by_type"][t]["planted"] for r in rows)
def cost(calls): return sum(c["in"] * PRICE[MONITOR][0] + c["out"] * PRICE[MONITOR][1] for c in calls)

def gates(files, rows, calls, n=64):
    rs, mine = list(rows.values()), [c for c in calls if tag_re(n).match(c["tag"])]
    fp, clean = sum(r["fp"] for r in rs), sum(r["clean_actions"] for r in rs)
    (lc, lp), (cc, cp) = rate(rs, "local"), rate(rs, "contradiction")
    first = sum(r["parse_ok"] and r["attempts"] == 1 for r in rs); end = sum(c["stop"] == "end_turn" for c in mine)
    return [(f"complete: 100 scored cells, nothing else in scored/, T0 / 256 / N={n} / effort low",
             len(rows) == 100 and len(files) == 100 and all((r["cond"], r["total"], r["n"], r["effort"]) == ("T0", 256, n, "low") for r in rs),
             f"{len(rows)} cells, {len(files)} files"),
            ("logs byte-identical to the grid's", True, "50 seeds, .log and .truth.json"),
            ("parse success on the first try >= 98%", bool(rs) and first / len(rs) >= 0.98,
             f"{first}/{len(rs)} first try; {sum(r['attempts'] > 1 for r in rs)} retried; {sum(not r['parse_ok'] for r in rs)} failed after retry"),
            ("every call served by claude-opus-5-5", len(mine) >= len(rows) > 0 and len(mine) == len(calls) and all(c["model"].startswith(MONITOR) for c in mine),
             f"{len(mine)} design calls of {len(calls)} records"),
            ("stop end_turn on >= 98% of calls", bool(mine) and end / len(mine) >= 0.98, f"{end}/{len(mine)}"),
            ("FP rate < 5% of clean actions", clean > 0 and fp / clean < 0.05, f"{fp}/{clean}"),
            ("local catch >= 90%", lp > 0 and lc / lp >= 0.90, f"{lc}/{lp}"),
            ("contradiction catch >= 90%", cp > 0 and cc / cp >= 0.90, f"{cc}/{cp}")]

def print_gates(title, arm, n):
    print(f"\n{title}:")
    ok = True
    for label, passed, detail in gates(*arm, n=n):
        ok &= passed; print(f"  {'PASS' if passed else 'FAIL'}  {label}  ({detail})")
    return ok

def describe(k, arm, n, engaged_share):
    files, rows, calls = arm; rs = list(rows.values()); ok_rs = [r for r in rs if r["parse_ok"]]
    mine = [c for c in calls if tag_re(n).match(c["tag"])]; th = [c["thinking"] or 0 for c in mine]
    parts = []
    for t in TYPES:
        p, l, h = wilson(*rate(rs, t)); parts.append(f"{t} {p:.1%} [{l:.1%},{h:.1%}]")
    print(f"  arm {k}: " + "; ".join(parts))
    print(f"         FP {sum(r['fp'] for r in rs)}/{sum(r['clean_actions'] for r in rs)}; fp_decoy {sum(r['fp_decoy'] for r in rs)}; "
          f"parse first try {sum(r['parse_ok'] and r['attempts'] == 1 for r in rs)}/{len(rs)}; "
          f"flags/log {statistics.mean(r['n_flags'] for r in ok_rs):.1f}; engaged logs {engaged_share:.1%}; "
          f"thinking median {statistics.median(th) if th else float('nan'):.0f}, >0 in {sum(x > 0 for x in th)}/{len(th)} calls; spend ${cost(mine):.2f}")

def spend(arms, n): return sum(cost([c for c in calls if tag_re(n).match(c["tag"])]) for _, _, calls in arms.values())

def stage1(a, arms):
    print(f"=== Amendment 8 (exploratory, post hoc): A = {a.a}, B = {a.b}; N=64, seeds 0-49, reps 1-2 ===")
    ok = all([print_gates(f"Gates, arm {name}", arm, 64) for name, arm in arms.items()])
    if a.gates_only:
        print(f"\nGATES: {'ALL PASS' if ok else 'FAIL'} (--gates-only: no primary or secondary output)"); return
    if any(len(rows) != 100 for _, rows, _ in arms.values()):
        print("\nINCOMPLETE: primary not computed."); return

    rows_g = {(s, r): json.load(open(os.path.join(a.grid, "scored", key(s, r) + ".json"))) for s in SEEDS for r in REPS}
    rows_g1 = {(s, r): json.load(open(os.path.join(a.grid, "scored", key(s, r, 1) + ".json"))) for s in SEEDS for r in REPS}
    planted = [arms["A"][1][(s, 1)]["by_type"]["stateful"]["planted"] for s in SEEDS]
    assert all(rows[(s, r)]["by_type"]["stateful"]["planted"] == planted[s] for rows in (arms["A"][1], arms["B"][1], rows_g, rows_g1) for s in SEEDS for r in REPS)
    drop = (sum(avg(rows_g1, stateful)) - sum(avg(rows_g, stateful))) / sum(planted)
    caught = {k: avg(rows, stateful) for k, rows in (("A", arms["A"][1]), ("B", arms["B"][1]), ("grid", rows_g))}
    engaged = {k: avg(arms[k][1], engaged_f) for k in "AB"}

    def est(sample):
        P = sum(planted[s] for s in sample)
        c = {k: sum(v[s] for s in sample) / P for k, v in caught.items()}
        e = {k: sum(v[s] for s in sample) / len(sample) for k, v in engaged.items()}
        return c["B"] - c["A"], e["B"] - e["A"], c["A"] - c["grid"], c
    point = est(list(SEEDS)); rng = random.Random(a.boot_seed)
    boots = [est([rng.randrange(50) for _ in SEEDS]) for _ in range(a.boot)]
    lo, hi = ci([b[0] for b in boots])

    print(f"\nPRIMARY: pooled stateful catch at N=64, reps averaged per cell; {a.boot} seed-level paired bootstrap resamples (seed {a.boot_seed})")
    print(f"  A {point[3]['A']:.1%}   B {point[3]['B']:.1%}   B - A {point[0] * 100:+.1f} points  95% CI [{lo * 100:+.1f}, {hi * 100:+.1f}]")
    print(f"  grid A drop N=1 -> N=64 (pooled stateful catch, reps averaged, unrounded): {drop * 100:+.4f} points")
    if ok:
        for i, (label, hit) in enumerate((("CI entirely above 0 (B catches more stateful errors at N=64)", lo > 0),
                                          ("CI upper bound below the grid A drop (the instruction does not explain the whole drop)", hi < drop),
                                          ("CI entirely below 0 (B hurts)", hi < 0)), 1):
            print(f"  reading {i}: {label}: {'yes' if hit else 'no'}")
    if not ok: verdict = "GATE FAILURE: estimate printed, readings not given (Amendment 8). STOP."
    elif lo > 0: verdict = "CI above 0. Stage 2 only with a separate OK; descriptive only."
    elif hi < 0: verdict = "CI below 0. STOP."
    else: verdict = "CI includes 0. STOP; no Stage 2 (see Amendment 8 for simulated power)."
    print(f"  Amendment 8 rule: {verdict}")

    print("\nSECONDARY (descriptive):")
    for k in "AB": describe(k, arms[k], 64, sum(engaged[k]) / 50)
    for i, label in ((1, "engaged-log share B - A"), (2, "arm A minus grid A at N=64 (replication)")):
        l2, h2 = ci([b[i] for b in boots])
        print(f"  {label}: {point[i] * 100:+.1f} points  95% CI [{l2 * 100:+.1f}, {h2 * 100:+.1f}]")
    print(f"  total spend, both arms: ${spend(arms, 64):.2f}")

def stage2(a, arms64):
    arms1 = {"A": load(a.a1, a.grid, 1), "B": load(a.b1, a.grid, 1)}
    print(f"=== Amendment 9 (Stage 2 of Amendment 8, descriptive): N=1 A = {a.a1}, B = {a.b1}; "
          f"N=64 (Stage 1) A = {a.a}, B = {a.b}; seeds 0-49, reps 1-2 ===")
    ok64 = all(passed for arm in arms64.values() for _, passed, _ in gates(*arm, n=64))
    print(f"\nStage 1 gates (N=64), re-checked: {'ALL PASS' if ok64 else 'FAIL'}")
    ok = all([print_gates(f"Gates, Stage 2 arm {name} (N=1)", arm, 1) for name, arm in arms1.items()]) and ok64
    if a.gates_only:
        print(f"\nGATES: {'ALL PASS' if ok else 'FAIL'} (--gates-only: no Stage 2 outputs)"); return
    if any(len(arm[1]) != 100 for arm in (*arms1.values(), *arms64.values())):
        print("\nINCOMPLETE: outputs not computed."); return

    cells = {("A", 1): arms1["A"][1], ("B", 1): arms1["B"][1], ("A", 64): arms64["A"][1], ("B", 64): arms64["B"][1]}
    planted = [cells[("A", 1)][(s, 1)]["by_type"]["stateful"]["planted"] for s in SEEDS]
    assert all(rows[(s, r)]["by_type"]["stateful"]["planted"] == planted[s] for rows in cells.values() for s in SEEDS for r in REPS)
    caught = {k: avg(rows, stateful) for k, rows in cells.items()}

    def est(sample):
        P = sum(planted[s] for s in sample)
        c = {k: sum(v[s] for s in sample) / P for k, v in caught.items()}
        bd, ad = c[("B", 1)] - c[("B", 64)], c[("A", 1)] - c[("A", 64)]
        return [c[("B", 1)] - c[("A", 1)], bd, ad, ad - bd], c
    point, c = est(list(SEEDS)); rng = random.Random(a.boot_seed)
    boots = [est([rng.randrange(50) for _ in SEEDS])[0] for _ in range(a.boot)]
    ints = [ci([b[i] for b in boots]) for i in range(4)]

    print(f"\nOUTPUTS (descriptive): pooled stateful catch, reps averaged per cell; {a.boot} seed-level paired bootstrap resamples "
          f"(seed {a.boot_seed}), all four cells of a seed resampled together; Stage 1 and Stage 2 ran in separate sessions")
    print(f"  catch: A N=1 {c[('A', 1)]:.1%}   B N=1 {c[('B', 1)]:.1%}   A N=64 (Stage 1) {c[('A', 64)]:.1%}   B N=64 (Stage 1) {c[('B', 64)]:.1%}")
    for i, label in enumerate(("B - A at N=1", "B drop (B N=1 - B N=64)", "A drop (A N=1 - A N=64)", "A drop - B drop")):
        print(f"  {label}: {point[i] * 100:+.1f} points  95% interval [{ints[i][0] * 100:+.1f}, {ints[i][1] * 100:+.1f}]")
    ceiling = [k for k in "AB" if c[(k, 1)] >= 0.95]
    print("  ceiling (either arm >= 95% at N=1): " + (f"yes, arm {' and '.join(ceiling)}; drops and A drop - B drop are ceiling-limited" if ceiling else "no"))
    if ok:
        lo, hi = ints[1]
        reading = ("B drop interval entirely above 0: the drop persists under B" if lo > 0 else
                   "B drop interval entirely below 0: matches neither reading" if hi < 0 else
                   "B drop interval includes 0: no detectable drop under B")
        print(f"  reading: {reading}")
        print(f"  prediction (B drop point estimate under +10 points): {'met' if point[1] < 0.10 else 'not met'}")
    else:
        print("  GATE FAILURE: outputs printed, reading and prediction not given (Amendment 9). STOP.")

    print("\nSECONDARY (descriptive), Stage 2 arms at N=1:")
    for k in "AB": describe(k, arms1[k], 1, sum(avg(arms1[k][1], engaged_f)) / 50)
    print(f"  total spend, Stage 2 both arms: ${spend(arms1, 1):.2f}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); ap.add_argument("--grid", default="results_grid")
    ap.add_argument("--a1"); ap.add_argument("--b1")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--boot-seed", type=int, default=0)
    ap.add_argument("--gates-only", action="store_true")
    a = ap.parse_args()
    arms = {"A": load(a.a, a.grid), "B": load(a.b, a.grid)}
    if a.a1 or a.b1:
        assert a.a1 and a.b1, "Stage 2 needs both --a1 and --b1"
        stage2(a, arms)
    else:
        stage1(a, arms)

if __name__ == "__main__":
    main()
