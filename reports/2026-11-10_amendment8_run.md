# Amendment 8 run, Stage 1 (2026-11-10)

Exploratory, post hoc (PREREG Amendment 8). Prompt A = `monitor_prompt.txt`, prompt B = `monitor_prompt_global.txt`. N=64, seeds 0–49, 2 reps, d2h, effort low, T0.

| Item | Value | Source |
|---|---|---|
| Run commit | `3178876` (PREREG Amendment 8), committed 2026-11-10T09:31:05−05:00; tooling `cf11f81`, `1e4a375`; `git status` clean before the run | `git log` |
| Start | 2026-11-10T14:31:22Z (block 1 start) | `results_a8_A/block_times.txt` |
| End | 2026-11-10T14:36:33Z (block 4 end) | same |
| Calls | 200 (100 per arm), all served by claude-opus-5-5, 200/200 `end_turn` | `analysis_global.py` gates |
| Retries | 0 (100/100 first-try parse in each arm) | same |
| Spend | $17.61 (A $8.65, B $8.97); the $25 cap was not reached | `analysis_global.py` secondary |

## Protocol as run

Blocks, in the committed ABBA order (times verbatim from `results_a8_A/block_times.txt`):
```
block1 A rep1 start 2026-11-10T14:31:22Z
block1 A rep1 end 2026-11-10T14:32:26Z
block2 B rep1 start 2026-11-10T14:32:41Z
block2 B rep1 end 2026-11-10T14:33:53Z
block3 B rep2 start 2026-11-10T14:34:02Z
block3 B rep2 end 2026-11-10T14:35:16Z
block4 A rep2 start 2026-11-10T14:35:26Z
block4 A rep2 end 2026-11-10T14:36:33Z
```

| After block | A cells | B cells | COST CAP / JOB ERROR lines | Exit code |
|---|---|---|---|---|
| 1 (A rep 1) | 50 | none yet (`results_a8_B/scored` did not exist) | 0 | 0 |
| 2 (B rep 1) | 50 | 50 | 0 / 0 | 0 |
| 3 (B rep 2) | 50 | 100 | 0 / 0 | 0 |
| 4 (A rep 2) | 100 | 100 | 0 / 0 | 0 |

**Blinding.**
- Runner output went to `run_stdout.log` with `>>`. Neither log was opened, and no outcome was read before all four blocks finished.
- `analysis_global.py --gates-only` ran first: ALL PASS in both arms. Only then did the full analysis run.

**Additions to the committed commands.** None changes the design:
- Each block command was wrapped in `date -u` lines that write to `results_a8_A/block_times.txt`.
- Each block ran in the background, with its exit code echoed.
- Before block 1, one unauthenticated request to `https://api.anthropic.com/v1/models` (no key sent) returned HTTP 401, confirming the host was reachable.

## Analysis output (`diagnostics/out/analysis_global_a8.txt`, verbatim)
```
=== Amendment 8 (exploratory, post hoc): A = results_a8_A, B = results_a8_B; N=64, seeds 0-49, reps 1-2 ===

Gates, arm A:
  PASS  complete: 100 scored cells, nothing else in scored/, T0 / 256 / N=64 / effort low  (100 cells, 100 files)
  PASS  logs byte-identical to the grid's  (50 seeds, .log and .truth.json)
  PASS  parse success on the first try >= 98%  (100/100 first try; 0 retried; 0 failed after retry)
  PASS  every call served by claude-opus-5-5  (100 design calls of 100 records)
  PASS  stop end_turn on >= 98% of calls  (100/100)
  PASS  FP rate < 5% of clean actions  (11/24000)
  PASS  local catch >= 90%  (534/534)
  PASS  contradiction catch >= 90%  (536/536)

Gates, arm B:
  PASS  complete: 100 scored cells, nothing else in scored/, T0 / 256 / N=64 / effort low  (100 cells, 100 files)
  PASS  logs byte-identical to the grid's  (50 seeds, .log and .truth.json)
  PASS  parse success on the first try >= 98%  (100/100 first try; 0 retried; 0 failed after retry)
  PASS  every call served by claude-opus-5-5  (100 design calls of 100 records)
  PASS  stop end_turn on >= 98% of calls  (100/100)
  PASS  FP rate < 5% of clean actions  (9/24000)
  PASS  local catch >= 90%  (534/534)
  PASS  contradiction catch >= 90%  (536/536)

PRIMARY: pooled stateful catch at N=64, reps averaged per cell; 10000 seed-level paired bootstrap resamples (seed 0)
  A 60.0%   B 80.4%   B - A +20.4 points  95% CI [+9.4, +31.4]
  grid A drop N=1 -> N=64 (pooled stateful catch, reps averaged, unrounded): +17.5472 points
  reading 1: CI entirely above 0 (B catches more stateful errors at N=64): yes
  reading 2: CI upper bound below the grid A drop (the instruction does not explain the whole drop): no
  reading 3: CI entirely below 0 (B hurts): no
  Amendment 8 rule: CI above 0. Stage 2 only with a separate OK; descriptive only.

SECONDARY (descriptive):
  arm A: local 100.0% [99.3%,100.0%]; stateful 60.0% [55.8%,64.1%]; contradiction 100.0% [99.3%,100.0%]
         FP 11/24000; fp_decoy 4; parse first try 100/100; flags/log 14.0; engaged logs 64.0%; thinking median 0, >0 in 3/100 calls; spend $8.65
  arm B: local 100.0% [99.3%,100.0%]; stateful 80.4% [76.8%,83.5%]; contradiction 100.0% [99.3%,100.0%]
         FP 9/24000; fp_decoy 7; parse first try 100/100; flags/log 15.1; engaged logs 82.0%; thinking median 0, >0 in 17/100 calls; spend $8.97
  engaged-log share B - A: +18.0 points  95% CI [+6.0, +30.0]
  arm A minus grid A at N=64 (replication): +2.6 points  95% CI [-8.5, +13.3]
  total spend, both arms: $17.61
```

## What the pre-registered rule says

- **Reading 1 (yes):** B catches more stateful errors at N=64 than A: +20.4 points, 95% CI [+9.4, +31.4].
- **Reading 2 (no):** the CI's upper bound (+31.4) is not below the grid's A drop (+17.5472), so the data do not show that the instruction explains only part of the drop.
- **Reading 3 (no):** B does not hurt.
- **Rule:** Stage 2 (A and B at N=1) runs only with a separate OK, and only as descriptive.

## Limits on interpretation (all stated in Amendment 8 or read from the outputs above)

- **Status.** Exploratory and post hoc. The simulated false-positive rate for this design is 6.3–7.1% (Amendment 8).
- **What Stage 1 can't show.** It can't tell a stream-specific lift from B being a better prompt at every N. There are two descriptive signs that a general prompt effect is possible, and both compare across separate runs, so neither is a test:
  - B's N=64 stateful catch (80.4%) is above the grid's A rate at N=1 (74.9%, `diagnostics/out/analysis_T0_grid.txt`).
  - B produced thinking in 17/100 calls, against 3/100 for A.
- **Replication.** Arm A matches the grid's A at N=64: +2.6 points, CI [−8.5, +13.3].
- **Remaining per-agent wording.** B still contains per-agent wording in prompt line 1, in the policy header and in the JSON `stream` field (Amendment 8 limitation).
