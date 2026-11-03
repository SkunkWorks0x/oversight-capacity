#!/usr/bin/env python3
"""Mock-only checks for analysis.py (no API calls).
Usage: python analysis_mock_test.py [scratch_dir]
1. Full mock grid (runner's mock: stateful/contradiction degrade with N, local flat) -> stateful slope < 0.
2. Null mock (no N effect, patched in here only) -> primary contrast CI covers 0.
3. 100 null replicates (B=1000, own bootstrap seed each) -> CI coverage of 0; bootstrap SE vs empirical SD."""
import asyncio, contextlib, glob, io, json, os, random, shutil, statistics, sys
import runner, analysis

def run_grid(root, conds, seed):
    random.seed(seed)
    sys.argv = ["runner.py", "run", "--mock", "--root", root, "--ns", "1,4,16,64", "--seeds", "0-49",
                "--conds", conds, "--reps", "2", "--subtlety", "d2h"]
    with contextlib.redirect_stdout(io.StringIO()):
        asyncio.run(runner.main())
    return root + "_mock"

def null_monitor(truth, n, cond, top_k):
    flags = [{"stream": e["stream"], "action": e["action"], "type": e["type"], "reason": "x"}
             for e in truth["errors"] if random.random() < (0.85 if e["type"] == "local" else 0.6)]
    if random.random() < 0.3: flags.append({"stream": "S01", "action": "A0001", "type": "local", "reason": "x"})
    return json.dumps({"flags": flags})

def contrast_ci(root, B, boot_seed=0):
    _, per, _, _ = analysis.load(root, "T0", None)
    est = analysis.estimates(analysis.rates(per))
    boots, _ = analysis.bootstrap(per, B, boot_seed)
    return est, {k: analysis.ci([b[k] for b in boots]) for k in est}, {k: statistics.stdev(b[k] for b in boots) for k in est}

scratch = sys.argv[1] if len(sys.argv) > 1 else "results_mock_reps"
ok = True

# 1. positive control; synthetic calls.jsonl (thinking = 10*N) exercises the thinking-token path
pos = run_grid("results_mock_grid", "T0,T1,T2", 1)
with open(os.path.join(pos, "calls.jsonl"), "w") as f:
    for p in glob.glob(os.path.join(pos, "scored", "*.json")):
        r = json.load(open(p)); key = os.path.basename(p)[:-5]
        f.write(json.dumps({"tag": f"{key}#0", "model": "claude-opus-5-5", "stop": "end_turn", "in": 1, "out": 1, "thinking": 10 * r["n"]}) + "\n")
est, cis, _ = contrast_ci(pos, 10000)
true_st = analysis.slope([0.85, 0.61, 0.37, 0.2])   # runner.mock_monitor: max(0.2, 0.85 - 0.12*log2 N)
for k in ("slope_stateful", "slope_local", "contrast_stateful_minus_local"):
    print(f"positive {k:30s} {est[k] * 100:+6.2f} [{cis[k][0] * 100:+6.2f}, {cis[k][1] * 100:+6.2f}]")
c1 = cis["slope_stateful"][1] < 0
c2 = cis["contrast_stateful_minus_local"][0] <= true_st <= cis["contrast_stateful_minus_local"][1]
c3 = cis["slope_local"][0] <= 0 <= cis["slope_local"][1]
print(f"  stateful slope negative, CI excludes 0: {c1} | contrast CI covers mock truth {true_st * 100:+.2f}: {c2} | local CI covers 0: {c3}")
ok &= c1 and c2 and c3

# 2. null control
runner.mock_monitor = null_monitor
null = run_grid("results_mock_null", "T0", 2)
est, cis, _ = contrast_ci(null, 10000)
k = "contrast_stateful_minus_local"
c4 = cis[k][0] <= 0 <= cis[k][1]
print(f"null     {k:30s} {est[k] * 100:+6.2f} [{cis[k][0] * 100:+6.2f}, {cis[k][1] * 100:+6.2f}]  covers 0: {c4}")
ok &= c4

# 3. null replicates
cover, ests, ses = 0, [], []
for i in range(100):
    root = run_grid(os.path.join(scratch, f"null{i}"), "T0", 100 + i)
    est, cis, se = contrast_ci(root, 1000, boot_seed=i)
    cover += cis[k][0] <= 0 <= cis[k][1]; ests.append(est[k]); ses.append(se[k])
    shutil.rmtree(root)
print(f"null replicates: contrast CI covers 0 in {cover}/100 (nominal 95%) | empirical SD {statistics.stdev(ests) * 100:.3f} pts"
      f" vs mean bootstrap SE {statistics.mean(ses) * 100:.3f} pts")
print("ALL MOCK CHECKS PASS" if ok else "MOCK CHECK FAILURE")
