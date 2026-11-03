# Pre-registration

Framing: event content and positions are identical across N; only stream labels and the background message mix change. No planted error requires attributing actions to agents. The study tests whether distributing identical events across more agent labels degrades monitoring, with local errors as the control. The message-mix shift is the main alternative explanation for any N effect and is reported by N.

## Calibration (recorded 2026-11-03, before any calibration run; generator commit aa41b19)

Design: N=1, T0, 256 actions, seeds 120-124; 6 cells = knob d1,d2,d3 x effort low,medium; separate roots results_cal/<knob>_<effort>.

Pre-registered rule: pick the cell where all three types are 70-90% and FP < 5%; ties -> medium effort, then lower knob. If no cell qualifies, STOP; do not run the pilot, do not change anything.

Prediction: medium effort >= 95% on all types at all knobs; low effort may drop stateful/contradiction below 90%.

AMENDMENT 1 (recorded before running). Reason: the original matrix never varied local difficulty, so the 70-90% gate was unreachable for local; contradiction is unaffected by the decoy knob.
- Effort fixed at LOW (cheap-monitor operating point). The medium-effort ceiling (100% on all types at all knobs) is reported as its own finding.
- Local uses over_cap 5 and price_off 5; contradiction uses implicit wording. Stateful knob d2 and d3.
- 2 cells x 10 new seeds (125-134), N=1, T0.
- Rule: choose the cell with stateful in 60-90% and FP <5%; tie -> the cell with local closest to stateful. Local and contradiction are reported; any type above 90% is a ceiling type, and claims involving it are labelled difficulty-confounded.
- If no cell has stateful in 60-90%: use the cell with the lowest stateful catch.
- STOPPING RULE: no further calibration. The pilot (seeds 100-119) runs at the chosen cell.
- Primary contrast unchanged. Stateful-vs-local is named as the cleanest label-effect test, since contradiction is exposed to the message-mix shift.

AMENDMENT 2 (decided before the Amendment 1 calibration table was seen).
- Primary contrast: seed-level bootstrap of (stateful slope - local slope) on log2(N). Contradiction and the pooled (stateful+contradiction) contrast are secondary, because contradiction is exposed to the message-mix shift, which is nearly collinear with N.
- Difficulty-match rule: the type-specific claim is supported only if pilot N=1 T0 catch rates (seeds 100-119) of stateful and local differ by <=15 points. Otherwise the contrast is labelled difficulty-confounded, the separate slopes are reported, and a differential drop is not interpreted as state-tracking cost.
- Grid seeds: 0-49 (power ~86% for a 15-point differential drop, simulated).
- Covariate adjustment for generic-message share is NOT used for inference (collinear with N); share is reported by N.

AMENDMENT 3 (recorded before the pilot). Calibration showed stateful misses are all-or-nothing per log at low effort.
- Correction to Amendment 2 timing: Amendment 2 was decided in the reviewer chat before the Amendment 1 table existed, but committed after it was generated (09:51); the repo cannot verify the timing.
- Correction to Amendment 2 power: the ~86% figure assumed independent errors within a log and is withdrawn. Re-simulated with whole-log engagement (50 seeds, 15-point drop, local at ceiling): 1 call per cell gives 45% if skips are random per call, 95% if content-driven; 2 calls per cell give 72% if random.
- Primary outcome unchanged: per-error catch rate. Secondary: per-log stateful engagement (log catches >= half its stateful errors), seed-level bootstrap on its slope.
- Grid design: 2 monitor calls per cell in every condition (T0, T1, T2), averaged per cell before the seed-level contrast. Fixed, not conditional on pilot data. The pilot's repeat agreement on engagement is reported descriptively.
- Pilot gates: stateful 60-90% (pooled over repeats), FP < 5%, parse >= 98%, T2 triage recall on local >= 80% and near chance on stateful. The <=15-point difficulty rule is computed on the pilot and reported. If a gate fails: report and STOP; no retuning on pilot seeds.
- Headline templates: (a) 'At fixed log length with identical events, low-effort monitor catch rate on stateful errors declines as the same actions are spread across more agent streams; local and contradiction errors stay at ceiling, so the contrast is difficulty-confounded.' (b) 'At fixed log length with identical events, spreading actions across up to 64 agent streams produced no detectable decline in low-effort stateful catch rate; the 95% CI excludes drops larger than X points.'

AMENDMENT 4 (budget; recorded before any grid data). Run order: (1) T0 grid, seeds 0-49, N in {1,4,16,64}, --reps 2, d2h, effort low; (2) pilot T1/T2 gates, then T1 grid; (3) T2 grid. Triage gates govern only the T1/T2 conditions; T0 does not depend on them. Any condition not run for budget reasons is reported as not run. Seeds and reps are not reduced.
