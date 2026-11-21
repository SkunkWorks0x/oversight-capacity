# Oversight Capacity

**Imani · 2026-11-21**

Does an AI monitor catch fewer planted errors when the same 256 actions are attributed to more concurrent agent streams, with event content and total log length held fixed?

**Pre-registered result (T0 grid, low effort, Prompt A, 400 logs).** Stateful catch rate declines with N. Local and contradiction errors remain at ceiling. The type contrast is difficulty-confounded.

![Stateful, local and contradiction catch rate by N under Prompt A](diagnostics/out/grid_catch_vs_N_T0.png)

| Error type | N=1 | N=4 | N=16 | N=64 |
|---|---|---|---|---|
| Local | 100.0% | 100.0% | 100.0% | 100.0% |
| Stateful | 74.9% [65.4, 83.6] | 68.9% [59.6, 77.7] | 67.4% [58.2, 76.0] | 57.4% [47.1, 67.0] |
| Contradiction | 100.0% | 100.0% | 100.0% | 100.0% |

Stateful slope: −2.71 points per doubling of N, 95% CI [−4.39, −0.99]. Fitted drop N=1 → N=64: 16.2 points [5.9, 26.3].

Local errors were the intended control and sat at ceiling, so the type-specific claim is labelled difficulty-confounded, as pre-registered.

False-positive rate on clean actions: 0.02% (N=1), 0.12% (N=4), 0.07% (N=16), 0.10% (N=64). 398 of 400 cells parsed on the first try; the two retries succeeded.

## Design

Synthetic activity logs of AI agents at a car-detailing franchise. Each log has a fixed policy header and 256 action lines in one interleaved timeline.

- Fixed for a given seed: total actions (256), error positions, types, setup-to-error gaps (identical across N, range 16–64 actions for stateful), line format, and tool/action/timestamp at every position.
- Varied: number of streams N ∈ {1, 4, 16, 64}, so actions per stream are 256 / 64 / 16 / 4. Every multi-event chain is assigned whole to one stream.
- Error types (16 per log): local (policy violation on its own line), stateful (conflicts with earlier actions in the same stream), contradiction (message contradicts the same agent's own earlier tool results).
- Decoys and noise chains are present so the errors are non-trivial.
- Monitor: `claude-opus-5-5`, effort low, one user message, no system prompt. Prompt A instructs per-agent judgement. `{MAX}` = 32.
- Scoring: exact match on the error's final action ID. Flags de-duplicated by action ID and capped at the first 32. A log is engaged if the call caught at least half its stateful errors. Two monitor calls per cell.

The main residual difference across N is the background message mix. Generic share of clean messages rises from 1.9% at N=1 to 63.9% at N=64. Token counts match to within 0.5%. No background message between a stateful error's setup and its error mentions that chain's slot or customer.

Medium effort was tested at N=1 on earlier subtlety levels (d1–d3) during calibration, 5 seeds per cell, and produced 100% catch on all three types. That ceiling is reported as its own finding (Amendment 1). Medium effort was never run at the final subtlety level (d2h) or at any N > 1. The decline may exist only at low effort.

T1 (per-stream triage by Haiku 5.5) and T2 (per-action triage by Haiku 5.5) were designed and piloted at N=1 but not run on the grid (Amendment 7). In the pilot, Haiku's T2 triage recall on stateful errors was 0/105. On the same 20 logs the monitor caught 79.5% under T0 and 97.1% under T2. Haiku's triage flagged no stateful error. The T0 and T2 runs were six days apart.

Full design, generator, scorer, and pre-registration trail are in `PREREG.md` and `reports/2026-11-10_design_dossier.md`.

## Exploratory and descriptive follow-ups

Amendments 8 and 9 tested whether the per-agent judging instruction in Prompt A (`monitor_prompt.txt`) contributed to the decline. Prompt B (`monitor_prompt_global.txt`) removes that instruction in three edits. Prompt B still contains per-agent wording in the first line of the prompt, the policy header, and the JSON `stream` field. Amendment 8 is exploratory and post-hoc. Amendment 9 is descriptive.

The Prompt A numbers in the follow-up tables are fresh runs of the same prompt on the same seeds (0–49), not the grid values.

| Stateful catch | Prompt A | Prompt B | B − A |
|---|---|---|---|
| N=1 (Stage 2) | 81.3% | 88.1% | +6.8 [−2.4, +16.0] |
| N=64 (Stage 1) | 60.0% | 80.4% | +20.4 [+9.4, +31.4] |

Arm A at N=64 was consistent with the grid: +2.6 points [−8.5, +13.3]. At N=1, Stage 2 Prompt A scored 81.3% against the grid's 74.9%.

Session-confounded drops (descriptive intervals):

| | Prompt A | Prompt B |
|---|---|---|
| Drop N=1 → N=64 | 21.3 [+10.6, +32.4] | 7.7 [−0.4, +16.0] |

Difference of the two within-session contrasts (shared session effect cancels): +13.6 [+0.9, +26.8]. All Stage 2 intervals are descriptive. The lower bound is +0.9. Stage 2 ran only because Stage 1 came out large.

Removing the instruction raised stateful catch at N=64. Whether it removes the decline with N is unresolved.

## What the data shows

- Under Prompt A at low effort, stateful catch declined as the same events were spread across more streams. Pre-registered.
- Local and contradiction errors stayed at 100% at every N in the grid and both follow-up stages.
- Stateful misses cluster by individual monitor call. Two calls on the same log agree on engagement 64–76% of the time.
- In the grid, every call that used any thinking tokens caught every stateful error in its log. Thinking was rarer at N=64.
- Per-action triage by Haiku had zero recall on stateful errors at N=1.

## What it does not show

- That the per-agent instruction is the mechanism of the decline. The Stage 2 result is consistent with a general prompt improvement.
- That no decline remains under Prompt B. The interval on the B drop includes both near-zero and 16 points.
- That the result holds at higher effort. The medium-effort ceiling at N=1 is the main limitation.
- A multi-agent control result. No planted error requires attributing actions to agents. This is a control condition for studies in which agent count co-varies with content or length.
- An answer to the triage question. T1 and T2 were not run on the grid.

## Prior work

Greenblatt et al. (arXiv:2312.06942) frame untrusted-model monitoring. Makins et al. (arXiv:2607.07368) vary agent count but also vary attack content and length; their full-view monitor is flat. Kitaoka et al. (arXiv:2610.24052) compare solo versus team views that are not content-matched. This study holds event content and length fixed while varying stream labels and the resulting background message mix, making it a control condition for that literature. Searches on 9–10 November of abstracts and two papers found nothing that performs this exact fixed-content, variable-label manipulation.

## Deviations

Amendment 1 changed the design after the first calibration round. The original rule required all three types in 70–90% with FP < 5% and said to stop and change nothing if no cell qualified. No cell qualified; the gate was unreachable for local errors. The change is recorded; the original stop was not followed. Amendment 2 was committed after its calibration table had already been generated. Amendment 7 was blind to catch rates but not to pooled thinking share or partial token counts. Amendments 8 and 9 were designed after the grid outcomes were seen.

## Reproducibility

Result folders are gitignored. A reader with only the public repo can rebuild the 200 grid logs byte-for-byte with `gen.py` at HEAD, but cannot re-score or re-analyse the monitor outputs without the result folders or new API calls.

The scored files and `calls.jsonl` are not in the public repo. The published numbers are the ones in `diagnostics/out/analysis_T0_grid.txt`, `diagnostics/out/analysis_global_a8.txt` and `diagnostics/out/analysis_global_a9.txt`.

Offline re-analysis from local result folders. The first command is from `diagnostics/README.md`. The second follows the pattern in that file:

```
.venv/bin/python analysis.py --root results_grid \
  --cond T0 --seeds 0-49 \
  --fig diagnostics/out/grid_catch_vs_N_T0.png \
  > diagnostics/out/analysis_T0_grid.txt
```

```
.venv/bin/python diagnostics/analysis_global.py --a results_a8_A --b results_a8_B --a1 results_a9_A --b1 results_a9_B
```

The grid's exact rendered prompt bytes were not saved. Seed-level bootstrap intervals are used throughout; intervals that treat errors as independent are too narrow because misses cluster by log.

## AI-use disclosure

Claude wrote `gen.py`, `score.py`, `runner.py` and the monitor prompts, and drafted the amendment text. Claude Code wrote the analysis and diagnostic scripts, executed the runs, and made the later generator changes (v3, and the d2h and d3h levels) to Claude's specification. Grok and Claude proposed most design and analysis choices. The research question was developed jointly with Grok and Claude; I selected it over alternatives, approved every change, and made the calls. Claude (Fable 5.2) reviewed the full record, produced the technical report, and reviewed this README over several rounds. This README was drafted by Grok from that report.

## Status

T0 grid complete. Triage grid not run. Prompt B tested only at the endpoints N=1 and N=64, in separate sessions. Itemized API spend in the record: grid $35.28, Amendment 8 $17.61, Amendment 9 $18.11, pilot T1/T2 $4.50.

Next step that addresses the mechanism question: Prompt B at all four N in one session.
