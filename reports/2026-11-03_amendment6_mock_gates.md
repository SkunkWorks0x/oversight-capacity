# Report: Amendment 6 finished; mock gates pass; analysis.py committed as `f80e0fd` (no API calls)

## Status
| Step | Status |
|---|---|
| 0 | PASS. pwd `~/dev/oversight-capacity`, HEAD `95b997a`; the uncommitted Amendment 6 GLMM edit was present. |
| 1 | FAILED (`mv` → `Operation timed out`). You'll move the folder to the Trash in Finder. I haven't touched it since. |
| 2 | **PASS.** Both mock grids regenerated, both gates met, `analysis.py` committed as `f80e0fd`. |
| 3 | This report, copied with pbcopy. Earlier reports are saved in the scratchpad (paths at the end). |

## Step 2: regeneration
- **How:** I ran `analysis_mock_test.py` as committed: positive grid `random.seed(1)`, T0/T1/T2; null grid `random.seed(2)`, T0. Both use 50 seeds × N {1,4,16,64} × 2 reps and `--mock`.
  - Plain `runner.py --mock` can't make the null grid: the null monitor is patched in only by that script.
  - Every run had `ANTHROPIC_API_KEY` unset, so an API call would have failed.
- **The old null grid was contaminated by iCloud:** `results_mock_null_mock/` held 129 conflict copies in `scored/` and 354 in `raw/` (e.g. `T256_N1_s10_T0 3.json`).
  - `load()` globs `scored/*.json`, so those copies would have been read. A cell with an extra copy fails the reps-per-cell guard, so `load()` should exit rather than double count. [med: read the code, didn't run it]
  - I moved the folder aside, not deleted it.
  - The real result folders (`results_cal`, `results_cal2`, `results_pilot`, `results_v2_pilot`, `results_smoke`, `results_tokens_d2h`) have **0** conflict-named files.

## Step 2: results (T0, 10,000 seed-level bootstrap resamples, points per doubling)
| Check | Positive grid | Null grid | Gate |
|---|---|---|---|
| `slope_stateful` | **−10.59 [−11.36, −9.84]** | −0.40 [−1.30, +0.56] | positive < 0 ✅ |
| `contrast_stateful_minus_local` (PRIMARY) | −11.16 [−12.12, −10.21] | **−0.38 [−1.52, +0.78]** | null covers 0 ✅ |
| `sens_contrast_stateful_minus_local` | −11.20 [−12.17, −10.25] | −0.35 [−1.48, +0.79] | null covers 0 ✅ |
| `slope_local` | +0.56 [−0.08, +1.20] | −0.02 [−0.71, +0.67] | covers 0 ✅ |
| Headline (b): X | 68.2 pts | 7.8 pts (stateful) / 9.1 pts (contrast) | — |
| **GLMM** log2(N), log-odds | **−0.508 [−0.535, −0.482]** | **−0.017 [−0.040, +0.007]** | descriptive only |
| GLMM random-intercept SD (seed / log) | 0.141 / 0.384 | 0.183 / 0.191 | — |
| GLMM rows / logs | 2120 / 400 | 2120 / 400 | — |
| Parse (first try) | 98–100% | 100% | — |

- **Mock checks:** all pass; the script printed `ALL MOCK CHECKS PASS`. The positive-grid CIs cover the mock's true slope of −10.95.
- **The GLMM recovers the mock's true slope:** the mock's catch probabilities are 0.85/0.61/0.37/0.20, which give an OLS logit slope of −0.517 per doubling (computed). The GLMM estimate is −0.508.
- **Figures** went to `results_mock_*_mock/catch_vs_N_T0.png` (gitignored). The tracked `reports/mock_grid_catch_vs_N_T0.png` is unchanged.

## For your review (I made no changes)
| # | Observation |
|---|---|
| 1 | **Null replicates:** the contrast CI covered 0 in **92/100** runs, against a nominal 95%. The mean bootstrap SE was 0.584 pts against an empirical SD of 0.634 (about 8% low). With 50 seeds the percentile CI may be slightly too narrow [low–med]. At n=100, 92 is within binomial noise of 95. |
| 2 | **Log random-intercept SD is not near 0** (0.384 positive, 0.191 null), even though the mock has no per-log clustering. Possible causes: the variational Bayes prior, and on the positive grid, misfit from a mock that's linear in probability with a 0.2 floor being absorbed per log [low]. This fits "descriptive only" in Amendment 6. |

## Anomaly closed: snapshot commits
All four "WIP on v3" pairs (14:23:34, 14:31:11, 14:37:13 and 14:54:15, which is `3dda795`/`f69782b`) match, to the second, a prompt submission or session start, logged as `UserPromptSubmit` + `file-history-snapshot`. Each tree equals the working tree, and no refs changed. So they're Claude Code harness snapshots, not file changes [med-high]. I saved this as a project memory so future sessions don't stop on them.

## Repo state
- HEAD is `f80e0fd` (v3). `git status` shows only `?? reports/latest.md`. No API calls were made.
- Moved aside, not deleted: `/private/tmp/claude-501/-Users-imani-dev-oversight-capacity/25348e45-3dae-48e9-ae65-32a29da1bc42/scratchpad/results_mock_null_mock.icloud-old`
- Earlier reports: `/private/tmp/claude-501/-Users-imani-dev-oversight-capacity/25348e45-3dae-48e9-ae65-32a29da1bc42/scratchpad/latest.prev-move-report.md` and `/private/tmp/claude-501/-Users-imani-dev-oversight-capacity/25348e45-3dae-48e9-ae65-32a29da1bc42/scratchpad/latest.step1-stop-report.md`

## Still open
- Move `~/Desktop/Oversight Capacity` to the Trash in Finder (yours).
- Pilot T1/T2 have never run (credits). The Haiku T1/T2 grid cost estimate is still missing.
- Observation #1 is a call for you to make: accept the percentile bootstrap as pre-registered, or amend before any grid data.

Next 60-second action: paste this report into the reviewer chat and decide on observation #1. Then trash the Desktop folder in Finder.
