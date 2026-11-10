"""Read-only: pilot T1/T2 triage gates, Haiku cost per call, T1/T2 grid cost estimate. Run from repo root."""
import glob, json, math, os, re, statistics as st, sys
from collections import defaultdict
sys.path.insert(0, os.getcwd())
from runner import T1_PROMPT, T2_PROMPT, CRITERION, PROMPT, TRIAGE_NOTE, LINE, split_log

PRICE = {"claude-haiku-5-5": (0.10e-6, 0.50e-6), "claude-opus-5-5": (4e-6, 20e-6)}  # $/token, skill table cached 2026-11-03
CHANCE = 24 / 256

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h

def cost(r): pi, po = PRICE[r["model"]]; return r["in"] * pi + r["out"] * po

P = sys.argv[1] if len(sys.argv) > 1 else "results_pilot"
rows = [json.load(open(f)) for f in glob.glob(f"{P}/scored/*.json")]
print("== monitor + triage recall, pilot N=1 seeds 100-119 ==")
for c in ["T1", "T2"]:
    rs = [r for r in rows if r["cond"] == c]
    print(f"{c}: logs={len(rs)} parse_ok={sum(r['parse_ok'] for r in rs)} first_try={sum(r['parse_ok'] and r['attempts']==1 for r in rs)}"
          f" FP={sum(r['fp'] for r in rs)}/{sum(r['clean_actions'] for r in rs)}")
    for t in ["local", "stateful", "contradiction"]:
        pl = sum(r["by_type"][t]["planted"] for r in rs)
        hk = sum(r["triage_hits"][t] for r in rs); p, lo, hi = wilson(hk, pl)
        mk = sum(r["by_type"][t]["caught"] for r in rs); mp, mlo, mhi = wilson(mk, pl)
        print(f"  {t:13s} triage recall {hk}/{pl}={p:.1%} [{lo:.1%},{hi:.1%}] chance-in-CI={lo <= CHANCE <= hi}"
              f" | monitor catch {mk}/{pl}={mp:.1%} [{mlo:.1%},{mhi:.1%}]")
    tri = [json.load(open(f)) for f in glob.glob(f"{P}/triage/{c}/*.json")]
    print(f"  triage coverage: scored {sum(t['n_scored'] for t in tri)}/{sum(t['n_actions'] for t in tri)} actions over {len(tri)} logs")

calls = [json.loads(l) for l in open(f"{P}/calls.jsonl")]
hk = [r for r in calls if r["model"].startswith("claude-haiku")]
groups = {"T1": [r for r in hk if r["in"] > 5000], "T2": [r for r in hk if r["in"] <= 5000]}
for c in ["T1", "T2"]:
    groups[c + "_mon"] = [r for r in calls if r["model"].startswith("claude-opus") and f"_{c}#" in r["tag"]]
print("\n== per-call tokens and cost from calls.jsonl ==")
for g, rs in groups.items():
    if not rs: print(g, "none"); continue
    stops = defaultdict(int)
    for r in rs: stops[r["stop"]] += 1
    th = [r["thinking"] for r in rs if r["thinking"] is not None]
    print(f"{g:7s} n={len(rs)} in={st.mean(r['in'] for r in rs):.0f} out={st.mean(r['out'] for r in rs):.0f}"
          f" thinking={st.mean(th) if th else 'NA'} $/call mean={st.mean(map(cost, rs)):.5f} max={max(map(cost, rs)):.5f}"
          f" total=${sum(map(cost, rs)):.3f} stops={dict(stops)}")

# ---- grid estimate: 50 seeds x N{1,4,16,64}; triage once per log (200 logs), monitor 2 reps (400 calls) per condition
t1 = groups["T1"]; t2 = groups["T2"]
def t1_prompts(path):
    h, lines = split_log(open(path).read()); s = defaultdict(list)
    for l in lines: s[LINE.match(l).group(1)].append(l)
    return [T1_PROMPT.format(criterion=CRITERION, header=h, lines="\n".join(ls)) for ls in s.values()]
pilot_chars = sum(len(p) for f in glob.glob(f"{P}/logs/*.log") for p in t1_prompts(f))
tpc = sum(r["in"] for r in t1) / pilot_chars   # tokens per char, calibrated on pilot T1 prompts
t1_out = st.mean(r["out"] for r in t1)
print(f"\n== grid estimate (Haiku in-tokens/char from pilot T1 = {tpc:.4f}) ==")
mon = {c: sum(map(cost, groups[c + "_mon"])) / 20 for c in ["T1", "T2"]}  # $/cell incl. parse retries (pilot: 20 cells, reps 1)
tot = {"T1": [0, 0, 0], "T2": [0, 0, 0]}
for n in [1, 4, 16, 64]:
    fs = glob.glob(f"results_grid/logs/T256_N{n}_s*.log"); assert len(fs) == 50, (n, len(fs))
    ins = sum(len(p) for f in fs for p in t1_prompts(f)) * tpc
    calls_n = 50 * n
    lo = ins * PRICE["claude-haiku-5-5"][0] + 50 * t1_out * PRICE["claude-haiku-5-5"][1]       # output scales with actions
    hi = ins * PRICE["claude-haiku-5-5"][0] + calls_n * t1_out * PRICE["claude-haiku-5-5"][1]  # output fixed per call
    t2c = 50 * 256 * st.mean(map(cost, t2))
    print(f"N={n:2d}: T1 Haiku calls={calls_n:5d} in~{ins/1e6:.2f}M tok ${lo:.2f}-{hi:.2f} | T2 Haiku calls={50*256} ${t2c:.2f}")
    tot["T1"][0] += lo; tot["T1"][1] += hi; tot["T2"][0] += t2c; tot["T2"][1] += t2c
for c in ["T1", "T2"]:
    m = 400 * mon[c]   # 200 logs x 2 reps
    print(f"{c}: Haiku ${tot[c][0]:.2f}-{tot[c][1]:.2f} + Opus monitor ${m:.2f} (400 calls at pilot {c} $/call incl. retries)"
          f" = ${tot[c][0]+m:.2f}-{tot[c][1]+m:.2f}")
