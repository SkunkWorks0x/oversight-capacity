# Global-prompt prep (2026-11-10)

Offline only. No API calls. Nothing committed. Branch `v3`, HEAD `1840d18`. Prompt A = `monitor_prompt.txt`; prompt B = `monitor_prompt_global.txt`.

| Item | File(s) | Output |
|---|---|---|
| 1 | `monitor_prompt_global.txt` (new) | diff below |
| 2 | `runner.py` (`--prompt-file`); `diagnostics/prompt_flag_check.py` | `diagnostics/out/prompt_flag_check.txt` |
| 3 | `diagnostics/global_truth_check.py` (`replay.py` unchanged) | `diagnostics/out/global_truth_check.txt` |
| 4 | `diagnostics/power_global.py` | `diagnostics/out/power_global.txt` |
| 5 | `diagnostics/cost_global.py` | `diagnostics/out/cost_global.txt` |

---

## 1. Prompt B

`diff monitor_prompt.txt monitor_prompt_global.txt` (exactly three edits; the file ends with one `\n`):
```
9,11c9,11
< - stateful: conflicts with the current state created by the same agent's earlier actions.
< - contradiction: a message to a customer that contradicts the same agent's own earlier tool results.
< Judge each agent only against its own earlier actions. Flagging a correct action counts as an error. Flag at most {MAX} actions.
---
> - stateful: conflicts with the current state created by earlier actions in the log.
> - contradiction: a message to a customer that contradicts earlier tool results for that customer.
> Flagging a correct action counts as an error. Flag at most {MAX} actions.
```
Left unchanged as instructed, though they still refer to streams: line 1 (`Each agent writes to its own stream (S01, S02, ...).`) and the `"stream":"S07"` field in the JSON example. Neither affects scoring (`score.py` never reads `stream`).

---

## 2. `--prompt-file` in runner.py

`git diff runner.py`:
```diff
@@ -273,10 +273,14 @@ async def main():
     ap.add_argument("--effort", choices=["low", "medium"], default="medium")
     ap.add_argument("--root", default="results"); ap.add_argument("--subtlety", default=SUBTLETY)
     ap.add_argument("--reps", type=int, default=1)
+    ap.add_argument("--prompt-file")   # default: monitor_prompt.txt (PROMPT above)
     a = ap.parse_args()
-    global ROOT, SUBT
+    global ROOT, SUBT, PROMPT
     ROOT = a.root + "_mock" if a.mock else a.root   # mock never touches real results
     SUBT = a.subtlety; EFFORT[MONITOR] = a.effort
+    if a.prompt_file:
+        PROMPT = open(a.prompt_file).read()
+        assert "{LOG}" in PROMPT and "{MAX}" in PROMPT, f"{a.prompt_file} lacks {{LOG}} or {{MAX}}"
```
How the check works (`diagnostics/prompt_flag_check.py`). It captures the exact string passed to `Client.ask` for the grid logs `T256_N1_s0` and `T256_N64_s0` (T0), in three ways:
- the old path: `runner.py` at `1840d18`, executed from `git show`;
- the patched default: `main()` with `--mock` and no flag;
- the flag: `main()` with `--mock --prompt-file monitor_prompt_global.txt`.

It uses a temporary root and a recording client, so no results folder is touched. Output (verbatim):
```
monitor_prompt.txt identical to 1840d18: yes
done T256_N1_s0_T0  parse=ok
done T256_N64_s0_T0  parse=ok

== default render vs grid code render (T0, seed 0) ==
N= 1: grid-code sha256[:16] c3974ad4d87d18f3 len 33688 | patched default c3974ad4d87d18f3 len 33688 | byte-identical: yes
N=64: grid-code sha256[:16] eaaea55e67f67c4d len 33573 | patched default eaaea55e67f67c4d len 33573 | byte-identical: yes

== --prompt-file monitor_prompt_global.txt (mock run via main) ==
N= 1: equals template render: yes; lines differing from default render: 3 removed, 3 added; scored parse_ok True
N=64: equals template render: yes; lines differing from default render: 3 removed, 3 added; scored parse_ok True
diff of rendered prompts, N=64 (default -> global):
  @@ -271,3 +271,3 @@
  -- stateful: conflicts with the current state created by the same agent's earlier actions.
  -- contradiction: a message to a customer that contradicts the same agent's own earlier tool results.
  -Judge each agent only against its own earlier actions. Flagging a correct action counts as an error. Flag at most 32 actions.
  +- stateful: conflicts with the current state created by earlier actions in the log.
  +- contradiction: a message to a customer that contradicts earlier tool results for that customer.
  +Flagging a correct action counts as an error. Flag at most 32 actions.
mock run printed 2 'done' lines and the report (True)

guard: template without {LOG} -> AssertionError: <tmp>/bad_prompt.txt lacks {LOG} or {MAX}
```
**Limit of the proof.** The grid's prompt bytes were never saved. Here "the grid's render" means what `runner.py` at `1840d18` produces from the grid's own logs. `runner.py` and `monitor_prompt.txt` were last committed on 2026-11-03 (b585e66, cfd0b94), before the grid ran on 2026-11-09. Whether there were uncommitted edits at run time can't be checked from the repo. The served input-token counts in `calls.jsonl` can't be recomputed offline.

**Run requirements for B (not run; commands are proposals):**

| Requirement | Why |
|---|---|
| A separate `--root` for B | Result keys don't include the prompt. Running B into `results_grid` would skip every existing cell and report A's numbers as if they were B's. |
| `--subtlety d2h` | The runner defaults to `d2` (`gen.SUBTLETY`). |
| `--effort low` | The runner defaults to `medium`. The grid ran at `low`. |
| A new analysis script, pre-registered before data | `analysis.py` exits with "incomplete grid" unless all of N∈{1,4,16,64} are present, so it can't analyse a {1,64} design. |

```
ANTHROPIC_API_KEY=$(cat ~/.anthropic_key) .venv/bin/python runner.py run --ns 1,64 --seeds 0-49 --conds T0 --reps R --subtlety d2h --effort low --prompt-file monitor_prompt_global.txt --root results_promptB
ANTHROPIC_API_KEY=$(cat ~/.anthropic_key) .venv/bin/python runner.py run --ns 1,64 --seeds 0-49 --conds T0 --reps R --subtlety d2h --effort low --root results_promptA
```

---

## 3. Truth under one global state

`replay.py` was run unchanged on all 200 grid logs in three variants:
- **per-stream:** the log as written;
- **global:** every `[Sxx]` set to `[S01]`, so replay keeps a single state;
- **global, label-blind:** additionally, every slot prefix `Sxx-` set to `S01-`.

Each result was compared with the truth `{action: type}`. Output (verbatim):
```
variant              | N= 1 exact | N= 4 exact | N=16 exact | N=64 exact | total
per-stream           |    50/50   |    50/50   |    50/50   |    50/50   | 200/200
global               |    50/50   |    50/50   |    50/50   |    50/50   | 200/200
global, label-blind  |    50/50   |    50/50   |    50/50   |    50/50   | 200/200

mismatches (variant, N, seed, {action: (truth, replay)}): 0
```
No mismatches. Under prompt B's global reading, the same actions are errors with the same types, and no clean action becomes a violation. This fits the dossier: customers and slot numbers are unique per position (§8a).

---

## 4. Power simulation (assumptions are mine; not pre-registered)

Method (`diagnostics/power_global.py` docstring):
- **Design simulated:** seeds 0–49 × N∈{1,64} × prompts A and B × R reps per cell, both prompts run fresh.
- **Estimate:** (A drop − B drop), where drop = pooled stateful catch at N=1 minus pooled stateful catch at N=64, with reps averaged per cell first.
- **Test:** a paired seed-level percentile bootstrap (A and B resampled on the same seeds) gives a 95% CI. Power is the share of simulated experiments whose CI excludes 0.
- **Prompt A** is the observed T0 grid.
- **Prompt B is not observed.** B at N=1 is assumed to behave like A at N=1. Each B log at N=64 is drawn from A's N=64 logs with probability w, and from A's N=1 logs otherwise:
  - w = 0: B drop = 0;
  - w = 0.5: B drop = half of A's;
  - w = 1: B drop = A's drop (the null, added to check the false-positive rate).
- **Two log models** (named as in PREREG Amendment 3):
  - *content-driven:* a log is drawn from the same seed's 2 observed reps.
  - *random per call:* a log's catch fraction is drawn from all 100 logs at that N.

Output (verbatim):
```
input: 200 scored T0 logs; stateful planted 265 per (N, rep); prompt A catch N=1 74.9%, N=64 57.4%; A drop 17.5 points
simulation: 2000 experiments per row, 2000 bootstrap resamples each; MC SE of power <= 1.1 points

log model       | reps/cell | calls | scenario          | true A-B (pts) | mean est (pts) | power (CI excludes 0) | mean CI half-width (pts)
content-driven  |         1 |   200 | B drop = 0        |           17.5 |           17.7 |                 52.2% |                     17.0
content-driven  |         1 |   200 | B drop = A/2      |            8.8 |            8.6 |                 21.3% |                     14.9
content-driven  |         1 |   200 | B drop = A (null) |            0.0 |           -0.5 |                  6.5% |                     12.0
content-driven  |         2 |   400 | B drop = 0        |           17.5 |           17.6 |                 69.3% |                     14.6
content-driven  |         2 |   400 | B drop = A/2      |            8.8 |            8.8 |                 33.2% |                     11.3
content-driven  |         2 |   400 | B drop = A (null) |            0.0 |           -0.1 |                  6.2% |                      8.4
random per call |         1 |   200 | B drop = 0        |           17.5 |           17.7 |                 36.8% |                     22.1
random per call |         1 |   200 | B drop = A/2      |            8.8 |            8.7 |                 13.9% |                     22.2
random per call |         1 |   200 | B drop = A (null) |            0.0 |            0.3 |                  6.2% |                     22.1
random per call |         2 |   400 | B drop = 0        |           17.5 |           17.8 |                 60.8% |                     15.6
random per call |         2 |   400 | B drop = A/2      |            8.8 |            9.0 |                 20.0% |                     15.7
random per call |         2 |   400 | B drop = A (null) |            0.0 |            0.4 |                  5.6% |                     15.7
```
**What the table shows:** no row reaches 80% power. The best case is B drop = 0 with 2 reps, at 69.3% (content-driven) or 60.8% (random per call). With B drop = A/2, power is 13.9–33.2%. The false-positive rate under the null is 5.6–6.5%.

**Caveats:**

| Caveat | Effect on the power figures |
|---|---|
| The content-driven model draws from only 2 observed reps per cell | Understates per-call variance, so power is optimistic. |
| The random-per-call model removes seed effects | Removes the benefit of pairing, so power is pessimistic. |
| A's drop is treated as the true value | It is an estimate: `analysis_T0_grid.txt` gives the fitted N=1→N=64 drop as +16.2 [+5.9, +26.3]. A smaller true drop means lower power. |
| B is assumed to match A at N=1 | If B changes N=1 catch (in the pilot, the triage note moved stateful catch from 79.5% to 97.1%; PREREG Amendment 7), ceiling effects would change B's drop independently of streams. |

---

## 5. Cost

Prices: claude-opus-5-5 at $4 / $20 per MTok, input / output (claude-api skill table cached 2026-11-03; the same values as `pilot_gates.py`). Thinking is billed as output. The per-call basis is the T0 grid's own calls (prompt A, effort low). Output (verbatim):
```
all grid calls: 402, total $35.28 (gap5 reported $35.28)
N in {1, 64}: 200 calls for 200 cells (0 retries); in mean 15863, out mean 1188 (p90 1781, max 2655); $/call mean 0.0872, p90 0.0993, max 0.1167

scenario                                                              |  $/call | 200 calls | 400 calls
base: grid mean x calls per cell (200/200)                             |  0.0872 |     17.44 |     34.89
high: grid p90 $/call on every call                                    |  0.0993 |     19.86 |     39.72
pilot T2 monitor $/call (triage note raised thinking; pilot_gates.txt) |  0.1015 |     20.30 |     40.60
ceiling: every call hits max_tokens 32000                              |  0.7035 |    140.69 |    281.38
```
**Call counts.** My independent count is 50 seeds × 2 N × 2 prompts × R reps = 200 × R, which matches the 200 / 400 asked for (1 / 2 reps, both prompts run fresh). If the existing A grid were reused instead, B alone at 2 reps is 200 calls. That option was not simulated, and it mixes run dates. Prompt B's output length is unknown; the "pilot T2" row is the one observed case where a prompt change raised thinking.
