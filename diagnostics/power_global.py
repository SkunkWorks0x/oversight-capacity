"""Offline power simulation for prompt A (monitor_prompt.txt) vs prompt B (monitor_prompt_global.txt). No API calls.
Input: results_grid/scored T0 rows (prompt A, effort low), seeds 0-49, N in {1, 64}, reps 1-2; stateful catch only.
Simulated design: seeds 0-49 x N {1, 64} x prompts A, B x R reps per cell (R = 1, 2), both prompts run fresh.
Estimate: A drop - B drop, drop = pooled catch(N=1) - pooled catch(N=64), reps averaged per cell first;
paired seed-level percentile bootstrap (A and B resampled on the same seeds), 95% CI. Power = share of simulated
experiments whose CI excludes 0. CI half-width = mean of (hi - lo) / 2.
B is not observed. Assumptions: B at N=1 behaves like A at N=1; each B log at N=64 comes from A's N=64 logs with
probability w, else from A's N=1 logs (w = 0: B drop 0; w = 0.5: B drop half of A's; w = 1: B drop = A's, the null).
Log models (PREREG Amendment 3 terms): content-driven = a log is drawn from the same seed's two observed reps at
that N (seed effects shared by A and B); random per call = a log's catch fraction is drawn from all 100 logs at that N."""
import json
import numpy as np

SEEDS, NSIM, NBOOT = range(50), 2000, 2000
rows = {}
for s in SEEDS:
    for n in (1, 64):
        for suf in ("", "_r2"):
            r = json.load(open(f"results_grid/scored/T256_N{n}_s{s}_T0{suf}.json"))
            assert (r["cond"], r["total"], r["effort"], r["rep"]) == ("T0", 256, "low", 2 if suf else 1)
            rows[(s, n, r["rep"])] = r["by_type"]["stateful"]
planted = np.array([rows[(s, 1, 1)]["planted"] for s in SEEDS], float)
assert all(rows[(s, n, k)]["planted"] == planted[s] for s in SEEDS for n in (1, 64) for k in (1, 2))
obs = {n: np.array([[rows[(s, n, k)]["caught"] for k in (1, 2)] for s in SEEDS], float) for n in (1, 64)}
frac = {n: (obs[n] / planted[:, None]).ravel() for n in (1, 64)}
drop_A = (obs[1].mean(1).sum() - obs[64].mean(1).sum()) / planted.sum()
print(f"input: {len(rows)} scored T0 logs; stateful planted {planted.sum():.0f} per (N, rep); prompt A catch N=1 "
      f"{obs[1].mean(1).sum() / planted.sum():.1%}, N=64 {obs[64].mean(1).sum() / planted.sum():.1%}; A drop {drop_A * 100:.1f} points")
print(f"simulation: {NSIM} experiments per row, {NBOOT} bootstrap resamples each; MC SE of power <= 1.1 points\n")

rng = np.random.default_rng(20261110)
S = np.arange(50)[None, :, None]

def logs(model, n, R):
    if model == "content-driven": return obs[n][S, rng.integers(0, 2, (NSIM, 50, R))]
    return frac[n][rng.integers(0, 100, (NSIM, 50, R))] * planted[None, :, None]

def sim(model, R, w):
    A1, A64, B1 = (logs(model, n, R).mean(2) for n in (1, 64, 1))
    B64 = np.where(rng.random((NSIM, 50, R)) < w, logs(model, 64, R), logs(model, 1, R)).mean(2)
    dA, dB = A1 - A64, B1 - B64
    est, half, sig = (dA - dB).sum(1) / planted.sum(), np.empty(NSIM), np.empty(NSIM, bool)
    for i in range(NSIM):
        bi = rng.integers(0, 50, (NBOOT, 50))
        d = np.sort((dA[i][bi] - dB[i][bi]).sum(1) / planted[bi].sum(1))
        lo, hi = d[int(0.025 * NBOOT)], d[int(0.975 * NBOOT) - 1]
        half[i], sig[i] = (hi - lo) / 2, lo > 0 or hi < 0
    return est.mean(), sig.mean(), half.mean()

print("log model       | reps/cell | calls | scenario          | true A-B (pts) | mean est (pts) | power (CI excludes 0) | mean CI half-width (pts)")
for model in ("content-driven", "random per call"):
    for R in (1, 2):
        for w, name in ((0.0, "B drop = 0"), (0.5, "B drop = A/2"), (1.0, "B drop = A (null)")):
            m, p, h = sim(model, R, w)
            print(f"{model:15s} | {R:9d} | {200 * R:5d} | {name:17s} | {(1 - w) * drop_A * 100:14.1f} | {m * 100:14.1f} | {p:21.1%} | {h * 100:24.1f}")
