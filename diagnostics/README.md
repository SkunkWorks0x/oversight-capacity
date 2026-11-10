# diagnostics/: how each reported number is reproduced

All commands run offline from the repo root with no API key. Inputs are the local result folders, which are **gitignored and not in the repo**: `results_grid/` (13M, 1,202 files), `results_pilot/` (2.4M, 242), `results_cal/` (1.7M, 126), `results_cal2/` (1.1M, 82). Without them, nothing here can be re-run, and regenerating them needs API calls.

## Map: source → report section → output
| Source | Kind | Reported in | Reported output | Re-run output (`out/`) | Re-run result |
|---|---|---|---|---|---|
| `../analysis.py --root results_grid --cond T0 --seeds 0-49` | committed script | T0 grid analysis (2026-11-09) | `analysis_T0_grid.txt` | `analysis_T0_grid.txt`, `grid_catch_vs_N_T0.png` | identical except the "Figure written" path; PNG byte-identical to `reports/grid_catch_vs_N_T0.png` |
| `diag_T0.py` | script | diagnostics a–e | `diag_T0.txt` | `diag_T0.txt` | identical |
| `diag2_T0.py` | script | diagnostics f–h (`reports/2026-11-09_diag_f-h.md`) | `diag2_T0.txt` | `diag2_T0.txt` | identical |
| `pilot_gates.py results_pilot` | script | `reports/pilot.md` T1/T2 rows and Haiku cost table; T1/T2 grid cost estimate | `recovered/pilot_gates_run.transcript_out.txt` (from `== monitor`) | `pilot_gates.txt`, `pilot_gates_run.txt` | identical digits |
| `recovered/gap1_pilot_T0_gates.sh` | **RECOVERED** one-off | `reports/pilot.md` T0 gates, difficulty rule, engagement; Amendment 7 | `recovered/gap1_*.transcript_out.txt` | `gap1_pilot_T0_gates.snapshot.txt` | identical (needs the snapshot, below) |
| `recovered/gap2_T2_scores_and_thinking.sh` | **RECOVERED** one-off | `reports/pilot.md` T2 score means and cutoff, T1/T2 thinking shares; Amendment 7 | `recovered/gap2_*.transcript_out.txt` | `gap2_T2_scores_and_thinking.txt` | identical digits |
| `recovered/gap3_pilot_T0_thinking_share.sh` | **RECOVERED** one-off | `reports/pilot.md` T0 thinking 10/40; Amendment 7 | `recovered/gap3_*.transcript_out.txt` | `gap3_pilot_T0_thinking_share.txt` | identical |
| `recovered/gap4_T0_grid_cost_estimate.sh` | **RECOVERED** one-off | T0 grid pre-run estimate $35.78 / $36.49 (report overwritten) | `recovered/gap4_*.transcript_out.txt` | `gap4_T0_grid_cost_estimate.snapshot.txt` | identical (needs the snapshot, below) |
| `recovered/gap5_T0_grid_integrity.sh` | **RECOVERED** one-off | T0 grid integrity, $35.28 spent (report overwritten) | `recovered/gap5_*.transcript_out.txt` | `gap5_T0_grid_integrity.txt` | identical digits; adds a `?? diagnostics/` git status line. Greps status lines of `results_grid/run_stdout.log` |
| `../runner.py report --root results_pilot` | committed script | cross-check of the gap1 T0 catch, FP and parse numbers | n/a | `runner_report_results_pilot.txt` | 218/218, 167/210, 212/212, 2/9600, 40/40 match; CIs printed to integer %; "effort medium" in the header is the CLI default, not the run's setting |
| `effort_blindness.py` | script (reads `calls.jsonl` and scored rows; scans the session transcripts up to the line holding the request) | `reports/2026-11-10_effort_blindness.md` §1–2 | transcript `713cce0c` line 951 tool result | `effort_blindness.txt` | identical. Not in the script: the report's runner-format-row check, gap5 `%`/catch counts and commit times came from inline commands |
| `grid_exposure.py`; `recovered/sec3_1`…`sec3_4_*.sh` | script + 4 **RECOVERED** one-offs (scan transcript `713cce0c` up to the Amendment 7 commit, 2026-11-10T03:26:06Z) | `reports/2026-11-10_effort_blindness.md` §3 | transcript line 1024 tool result; `recovered/sec3_*.transcript_out.txt` | `grid_exposure.txt`, `sec3_*.txt` | identical. §3 names the scratchpad path (this is a `cmp`-identical copy) and says "three inline scans": there were four, and row 391 comes only from `sec3_2`, row 270 only from `sec3_4`. `sec3_2` stops after its first match past the cutoff (line 1036), so it reproduces while that stays first |
| `design_dossier.py` | script (reads `results_grid/logs` and `results_grid/calls.jsonl` by tag; asserts each log equals `gen.build` output; reads no scored or raw results) | `reports/2026-11-10_design_dossier.md`: all numbers and sample lines | `out/design_dossier.txt` (quoted directly) | `design_dossier.txt` | identical (`cmp`). Not in the script: §1's rendered user message came from an inline offline render (`runner.py:183` applied to `T256_N1_s0.log`) |
| `prompt_flag_check.py` | script (runs `runner.py` at HEAD and at `1840d18` via `git show`, recording mock client, temp root) | `reports/2026-11-10_global_prompt_prep.md` §2 | `out/prompt_flag_check.txt` | `prompt_flag_check.txt` | identical (`cmp`), also after the `--shuffle` / `--cost-cap` additions |
| `global_truth_check.py` | script (`replay.py` unchanged, all 200 `results_grid/logs`, per-stream and global state) | `reports/2026-11-10_global_prompt_prep.md` §3; PREREG Amendment 8 (draft) | `out/global_truth_check.txt` | `global_truth_check.txt` | identical (`cmp`) |
| `power_global.py` | script (reads `results_grid/scored` T0 N=1/64 rows, `results_grid/calls.jsonl` N=64 records, `out/pilot_gates.txt`; numpy, fixed RNG seeds) | `reports/2026-11-10_global_prompt_prep.md` §4, §6; PREREG Amendment 8 (draft): power, false-positive rate, expected cost | `out/power_global.txt` | `power_global.txt` | identical (`cmp`) |
| `cost_global.py` | script (reads `results_grid/calls.jsonl`, `out/pilot_gates.txt`) | `reports/2026-11-10_global_prompt_prep.md` §5 | `out/cost_global.txt` | `cost_global.txt` | identical (`cmp`) |
| `analysis_global.py --a <root A> --b <root B>` | script: PREREG Amendment 8 gates, primary (B − A stateful catch at N=64, paired seed bootstrap) and secondary outputs; reads `results_grid` logs and N=64 scored rows | PREREG Amendment 8 (draft; not yet run on real data) | n/a | n/a | exercised by `a8_mock_test.py` on mock roots only |
| `a8_mock_test.py` | test (offline; temp roots; `runner.py --mock` with `--prompt-file`, `--shuffle`, `--cost-cap`; runs `analysis_global.py`) | Amendment 8 tooling check | stdout only, not saved | n/a | 13/13 checks PASS (2026-11-10) |

- **RECOVERED** files are Bash tool inputs copied verbatim from the session transcript (`~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-….jsonl`), with a header giving source line, tool_use id, original run time and recovery date. Each `*.transcript_out.txt` holds the original output verbatim. No code was rewritten. None of these commands was found in the older transcripts.
- Each `recovered/*.sh` starts with `cd ~/dev/oversight-capacity`, so it runs only at that path.
- `recovered/pilot_gates_run.sh` calls the session-scratchpad copy of `pilot_gates.py` by absolute path, which may no longer exist. `diagnostics/pilot_gates.py` is a byte-identical copy (`cmp`-checked when copied); run that instead.

## Snapshot step (gap1, gap4)
gap1 and gap4 read all of `results_pilot/`. The T1/T2 pilot (2026-11-09 21:22–21:35 EST) later appended 40 scored files and 5,180 call records to that folder. Re-run against the current folder, they print different numbers (`out/*.full_results_pilot.txt`). To reproduce them:
```
bash diagnostics/make_pilot_T0_snapshot.sh    # -> results_pilot_T0_snapshot/ (gitignored)
sed 's|^cd ~/dev/oversight-capacity && |cd ~/dev/oversight-capacity/results_pilot_T0_snapshot \&\& |' diagnostics/recovered/gap1_pilot_T0_gates.sh | zsh
```
Use the same `sed` for gap4. Only the working folder changes. The snapshot script selects files by name and records by tag, then asserts:
- 40 T0 scored files, all with mtime 2026-11-03;
- 40 T0 `calls.jsonl` records, which are exactly lines 1–40.

## `reports/pilot.md` values that are not printed by any command
| Value | Derivation |
|---|---|
| 5,180 T1/T2 calls | 20 + 5,120 + 20 + 20 (n values in `pilot_gates.py` output) |
| 20.5 points | 100 − 79.5 |
| T0 thinking 25% | 10/40 (gap3 prints `10 / 40`) |
| T1 8/20, T2 18/20 | gap2 shares 0.4 and 0.9 × n = 20 (n from `pilot_gates.py`) |
| T2 triage $0.0000916/call | $0.469 / 5,120 by hand; the printed mean is 0.00009. With the total rounded to 3 dp, the true value lies in 0.0000915–0.0000917. |
| Rounded from printed values | thinking 4,213 (4213.35), 79 (79.296…), 286 (285.9), 829 (828.75); $/call 0.0956 (0.09557), 0.1038 (0.10376), 0.1095 (0.10953); "100%" (100.0%) |

## T0 grid parse retries (2 of 400 cells)
- `T256_N16_s2_T0` and `T256_N16_s36_T0_r2`: attempt 0 ended `end_turn` with a JSON flags object. The model then retracted it in prose ("Correction — here is the final…" / "Wait, I must give the corrected…") and wrote a second JSON object.
- `score.parse` matches greedily from the first `{` to the last `}`, so `json.loads` fails with "Extra data". Attempt 1 parsed.
- Evidence: `results_grid/raw/<key>.json` and `results_grid/calls.jsonl`.

## Not reproducible from this repo
- **Calibration extra columns:** fp_decoy, median thinking, calls with thinking > 0 and cost per cell (Desktop-era transcript `c7e59a3e`, 2026-11-03) came from a one-off command that wasn't recovered. Catch, FP and parse per cell, including `d2h_low` stateful 43/54 and the medium-effort 100% ceiling, are reproduced by `runner.py report --root results_cal/<cell>` or `results_cal2/<cell>`, given the local folders.
- **Haiku credit check** (2026-11-09, `served claude-haiku-5-5 … in 18 out 4`): makes an API call; not copied.
- **Mid-run spend check** ($11.04 at 126 calls): progress only, not recovered.
- **Prose of reports overwritten in `reports/latest.md`** (2026-11-09 run report, T0 analysis report, diagnostics a–e): not reconstructed. Their numbers are in `analysis_T0_grid.txt`, `diag_T0.txt` and the recovered outputs above.

## Re-run everything
```
for f in diag_T0 diag2_T0; do .venv/bin/python diagnostics/$f.py > diagnostics/out/$f.txt; done
.venv/bin/python diagnostics/pilot_gates.py results_pilot > diagnostics/out/pilot_gates.txt
.venv/bin/python analysis.py --root results_grid --cond T0 --seeds 0-49 --fig diagnostics/out/grid_catch_vs_N_T0.png > diagnostics/out/analysis_T0_grid.txt
for g in gap2_T2_scores_and_thinking gap3_pilot_T0_thinking_share gap5_T0_grid_integrity; do zsh diagnostics/recovered/$g.sh > diagnostics/out/$g.txt 2>&1; done
.venv/bin/python runner.py report --root results_pilot > diagnostics/out/runner_report_results_pilot.txt
```
For gap1 and gap4, use the snapshot step above.
