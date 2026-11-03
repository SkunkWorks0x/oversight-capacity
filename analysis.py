#!/usr/bin/env python3
"""Offline analysis of one results root for one condition (no API calls).
Usage: python analysis.py --root results_grid [--cond T0] [--seeds 0-49] [--boot 10000] [--fig out.png]
Slope = OLS of the per-N pooled catch rate (caught / planted, summed over seeds, reps averaged per cell
first) on log2(N), in points per doubling. CIs: percentile, resampling seeds with replacement."""
import argparse, glob, json, os, random, re, statistics, sys
from runner import rng_list

TYPES = ["local", "stateful", "contradiction"]
NS = [1, 4, 16, 64]
W = [-3 / 20, -1 / 20, 1 / 20, 3 / 20]   # OLS slope weights for x = log2(N) = 0, 2, 4, 6
GROUPS = {"local": ["local"], "stateful": ["stateful"], "contradiction": ["contradiction"],
          "pooled": ["stateful", "contradiction"]}

def slope(rates):
    return sum(w * r for w, r in zip(W, rates))

def ci(xs):
    s = sorted(xs)
    return s[int(0.025 * len(s))], s[int(0.975 * len(s)) - 1]

def load(root, cond, seeds):
    rows = [json.load(open(f)) for f in glob.glob(os.path.join(root, "scored", "*.json"))]
    rows = [r for r in rows if r["cond"] == cond and r["total"] == 256 and r["n"] in NS and (seeds is None or r["seed"] in seeds)]
    cells = {}
    for r in rows: cells.setdefault((r["seed"], r["n"]), []).append(r)
    present = sorted({s for s, _ in cells})
    missing = [(s, n) for s in present for n in NS if (s, n) not in cells]
    reps = sorted({len(v) for v in cells.values()})
    if not cells or missing or len(reps) != 1:
        sys.exit(f"incomplete grid for {cond}: {len(present)} seeds, missing cells {missing[:5]}, reps per cell {reps}")
    per = []   # one dict per seed: caught[type] per N (rep-averaged), planted[type], engaged per N (rep-averaged)
    for s in present:
        d = {"planted": {}, "caught": {t: [] for t in TYPES}, "engaged": []}
        for n in NS:
            rs = cells[(s, n)]
            for t in TYPES:
                if {r["by_type"][t]["planted"] for r in rs} != {d["planted"].setdefault(t, rs[0]["by_type"][t]["planted"])}:
                    sys.exit(f"planted {t} differs across N/reps for seed {s}")
                d["caught"][t].append(sum(r["by_type"][t]["caught"] for r in rs) / len(rs))
            p = d["planted"]["stateful"]
            d["engaged"].append(sum(r["by_type"]["stateful"]["caught"] >= p / 2 for r in rs) / len(rs))
        per.append(d)
    return rows, per, present, reps[0]

def rates(sample):
    out = {}
    for g, ts in GROUPS.items():
        P = sum(d["planted"][t] for d in sample for t in ts)
        out[g] = [sum(d["caught"][t][j] for d in sample for t in ts) / P for j in range(4)]
    out["engaged"] = [sum(d["engaged"][j] for d in sample) / len(sample) for j in range(4)]
    return out

def estimates(r):
    sl = {g: slope(v) for g, v in r.items()}
    return {**{f"slope_{g}": v for g, v in sl.items()},
            "contrast_stateful_minus_local": sl["stateful"] - sl["local"],
            "contrast_pooled_minus_local": sl["pooled"] - sl["local"]}

def bootstrap(per, B, seed):
    rng = random.Random(seed); S = len(per)
    est, per_n = [], []
    for _ in range(B):
        r = rates([per[rng.randrange(S)] for _ in range(S)])
        est.append(estimates(r)); per_n.append(r)
    return est, per_n

def glmm(rows):
    try:
        import pandas as pd
        from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
    except ImportError:
        return "GLMM skipped: statsmodels/pandas not installed."
    recs = [{"y": int(i < r["by_type"][t]["caught"]), "x": NS.index(r["n"]) * 2, "st": int(t == "stateful"), "seed": r["seed"]}
            for r in rows for t in ("local", "stateful") for i in range(r["by_type"][t]["planted"])]
    m = BinomialBayesMixedGLM.from_formula("y ~ x * st", {"seed": "0 + C(seed)"}, pd.DataFrame(recs))
    return "Logistic GLMM (random intercept per seed, variational Bayes); x = log2(N), st = stateful vs local:\n" + str(m.fit_vb().summary())

def descriptives(root, rows, seeds, cond):
    calls = [json.loads(l) for l in open(os.path.join(root, "calls.jsonl"))] if os.path.exists(os.path.join(root, "calls.jsonl")) else []
    tag = re.compile(rf"^T256_N(\d+)_s(\d+)_{cond}(?:_r\d+)?#\d+$")
    think = {n: [] for n in NS}
    for c in calls:
        m = tag.match(c["tag"])
        if m and c["model"].startswith("claude-opus") and int(m.group(1)) in think and int(m.group(2)) in seeds:
            think[int(m.group(1))].append(c["thinking"])
    lines = ["N  | " + " | ".join(f"{t[:5]:>5}" for t in TYPES) + " | FP rate | fp_decoy (per log) | flags/log | parse (1st try) | generic share | thinking median (calls)"]
    for n in NS:
        rs = [r for r in rows if r["n"] == n]; ok = [r for r in rs if r["parse_ok"]]
        catch = [sum(r["by_type"][t]["caught"] for r in rs) / sum(r["by_type"][t]["planted"] for r in rs) for t in TYPES]
        gen = []
        for s in seeds:
            k = json.load(open(os.path.join(root, "logs", f"T256_N{n}_s{s}.truth.json")))["clean_msg_kinds"]
            gen.append(k["generic"] / sum(k.values()))
        th = f"{statistics.median(think[n]):.0f} ({len(think[n])})" if think[n] else "n/a (no calls.jsonl)"
        lines.append(f"{n:<2} | " + " | ".join(f"{c:5.1%}" for c in catch)
                     + f" | {sum(r['fp'] for r in rs) / sum(r['clean_actions'] for r in rs):6.2%}"
                     + f" | {sum(r['fp_decoy'] for r in rs)} ({sum(r['fp_decoy'] for r in rs) / len(rs):.2f})"
                     + f" | {statistics.mean(r['n_flags'] for r in ok):.1f}"
                     + f" | {len(ok)}/{len(rs)} ({sum(r['attempts'] == 1 for r in ok)})"
                     + f" | {statistics.mean(gen):5.1%} | {th}")
    return "\n".join(lines)

def figure(point, per_n, path, title):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return "Figure skipped: matplotlib not installed (data table above is the figure's content)."
    style = {"local": ("#2a78d6", "o"), "stateful": ("#eb6834", "s"), "contradiction": ("#1baf7a", "^")}   # dataviz default slots 1-3
    x = [0, 2, 4, 6]
    fig, ax = plt.subplots(figsize=(6.4, 4), facecolor="#fcfcfb"); ax.set_facecolor("#fcfcfb")
    ends = []
    for t, (col, mk) in style.items():
        lo = [ci([b[t][j] for b in per_n])[0] * 100 for j in range(4)]; hi = [ci([b[t][j] for b in per_n])[1] * 100 for j in range(4)]
        ax.fill_between(x, lo, hi, color=col, alpha=0.15, linewidth=0)
        ax.plot(x, [v * 100 for v in point[t]], color=col, marker=mk, markersize=8, linewidth=2, label=t)
        ends.append([point[t][-1] * 100, t])
    ends.sort()
    for i in range(1, len(ends)): ends[i][0] = max(ends[i][0], ends[i - 1][0] + 5)   # keep direct labels from colliding
    for yv, t in ends: ax.annotate(t, (6.15, yv), va="center", fontsize=9, color="#52514e", annotation_clip=False)
    ax.set_xticks(x, [str(n) for n in NS]); ax.set_xlabel("agent streams N (log2 scale)", color="#52514e")
    ax.set_ylim(0, 105); ax.set_ylabel("catch rate (%)", color="#52514e")
    ax.grid(axis="y", color="#e8e7e3", linewidth=0.8); ax.set_axisbelow(True)
    for side in ("top", "right"): ax.spines[side].set_visible(False)
    ax.legend(frameon=False, loc="lower left"); ax.set_title(title, loc="left", fontsize=11, color="#0b0b0b")
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)
    return f"Figure written: {path}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--cond", default="T0"); ap.add_argument("--seeds")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--boot-seed", type=int, default=0); ap.add_argument("--fig")
    a = ap.parse_args()
    rows, per, seeds, reps = load(a.root, a.cond, set(rng_list(a.seeds)) if a.seeds else None)
    point = rates(per); est = estimates(point)
    boots, per_n = bootstrap(per, a.boot, a.boot_seed)
    print(f"=== {a.root} cond={a.cond}: {len(seeds)} seeds x N {NS} x {reps} reps; {a.boot} seed-level bootstrap resamples ===")
    print("\nSlopes on log2(N), points per doubling [95% CI]:")
    for k in est:
        lo, hi = ci([b[k] for b in boots])
        print(f"  {k:32s} {est[k] * 100:+7.2f}  [{lo * 100:+7.2f}, {hi * 100:+7.2f}]" + ("   <- PRIMARY" if k == "contrast_stateful_minus_local" else ""))
    print("\nHeadline (b): fitted drop from N=1 to N=64 = -6 x slope (points); the 95% CI excludes drops larger than X:")
    for k in ("slope_stateful", "contrast_stateful_minus_local"):
        lo, hi = ci([-6 * b[k] for b in boots])
        print(f"  {k:32s} drop {-6 * est[k] * 100:+6.1f} [{lo * 100:+6.1f}, {hi * 100:+6.1f}]  -> X = {hi * 100:.1f} points")
    print("\nCatch rate by N (rep-averaged, pooled over seeds) [95% CI]  (figure data / table view):")
    for g in list(GROUPS) + ["engaged"]:
        print(f"  {g:13s} " + "  ".join(f"N={n}: {point[g][j]:5.1%} [{ci([b[g][j] for b in per_n])[0]:.1%},{ci([b[g][j] for b in per_n])[1]:.1%}]" for j, n in enumerate(NS)))
    print("\nDescriptives by N (all reps):"); print(descriptives(a.root, rows, seeds, a.cond))
    print("\n" + glmm(rows))
    print(figure(point, per_n, a.fig or os.path.join(a.root, f"catch_vs_N_{a.cond}.png"),
                 f"Catch rate vs agent streams, {a.cond} ({len(seeds)} seeds, {reps} reps)"))

if __name__ == "__main__":
    main()
