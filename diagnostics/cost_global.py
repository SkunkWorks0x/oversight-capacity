"""Offline cost estimate for 200 and 400 Opus monitor calls (no API calls). Run from repo root.
Prices: claude-opus-5-5 $4 / $20 per MTok input / output (claude-api skill model table, cached 2026-11-03; same as
PRICE in diagnostics/pilot_gates.py). Thinking is billed as output; calls.jsonl 'out' is usage.output_tokens.
Per-call basis: results_grid/calls.jsonl (T0 grid, prompt A, effort low), records tagged T256_N{1,64}_s*_T0*."""
import json, re
import numpy as np

PIN, POUT, MAXTOK = 4e-6, 20e-6, 32000
TAG = re.compile(r"^T256_N(\d+)_s(\d+)_T0(?:_r2)?#(\d)$")
recs = [r for r in map(json.loads, open("results_grid/calls.jsonl"))]
cost = lambda r: r["in"] * PIN + r["out"] * POUT
assert all(TAG.match(r["tag"]) and r["model"] == "claude-opus-5-5" for r in recs)
print(f"all grid calls: {len(recs)}, total ${sum(map(cost, recs)):.2f} (gap5 reported $35.28)")

sub = [r for r in recs if int(TAG.match(r["tag"]).group(1)) in (1, 64)]
cells = sum(TAG.match(r["tag"]).group(3) == "0" for r in sub); retries = len(sub) - cells
c = np.array([cost(r) for r in sub]); i = np.array([r["in"] for r in sub]); o = np.array([r["out"] for r in sub])
print(f"N in {{1, 64}}: {len(sub)} calls for {cells} cells ({retries} retries); in mean {i.mean():.0f}, out mean {o.mean():.0f} "
      f"(p90 {np.percentile(o, 90):.0f}, max {o.max()}); $/call mean {c.mean():.4f}, p90 {np.percentile(c, 90):.4f}, max {c.max():.4f}")
t2 = float(re.search(r"T2_mon .*?\$/call mean=([\d.]+)", open("diagnostics/out/pilot_gates.txt").read()).group(1))
per = {f"base: grid mean x calls per cell ({len(sub)}/{cells})": c.mean() * len(sub) / cells,
       "high: grid p90 $/call on every call": np.percentile(c, 90),
       "pilot T2 monitor $/call (triage note raised thinking; pilot_gates.txt)": t2,
       "ceiling: every call hits max_tokens 32000": i.mean() * PIN + MAXTOK * POUT}
print("\nscenario                                                              |  $/call | 200 calls | 400 calls")
for k, v in per.items(): print(f"{k:70s} | {v:7.4f} | {200 * v:9.2f} | {400 * v:9.2f}")
