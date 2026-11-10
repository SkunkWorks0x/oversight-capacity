# Pilot report (level d2h, effort low, N=1, seeds 100-119, root results_pilot)

Gate definition (decided before T1/T2 ran; T0 complete, T1/T2 not yet run): "near chance" for T2 stateful recall
= the 95% Wilson CI of T2 stateful recall contains 9.4% (24/256).

## Results (T1/T2 run 2026-11-09 at HEAD f80e0fd; computed from results_pilot/scored, triage, calls.jsonl)

Runs: T0 = 20 seeds x 2 reps (40 logs, earlier); T1, T2 = 20 seeds x 1 rep (20 logs each). Same logs (gen v3, d2h) in all three.
Monitor claude-opus-5-5 effort low; triage claude-haiku-5-5 (no effort set, server default). All 5,180 T1/T2 calls end_turn, served model = requested.

### Gates (Amendment 3; 95% Wilson CIs)
| Gate | Value | Rule | Result |
|---|---|---|---|
| T0 stateful catch (pooled over reps) | 167/210 = 79.5% [73.6, 84.4] | 60-90% | PASS |
| T0 false-positive rate | 2/9600 = 0.02% | < 5% | PASS |
| T0 parse | 40/40 (40 first try) | >= 98% | PASS |
| T2 triage recall, local | 109/109 = 100% [96.6, 100] | >= 80% | PASS |
| T2 triage recall, stateful | 0/105 = 0.0% [0.0, 3.5] | CI contains 9.4% | **FAIL (below chance)** |
| Difficulty rule (Amendment 2) | T0 stateful 79.5% vs local 218/218 = 100%: 20.5 pts | <= 15 pts | **exceeded: contrast labelled difficulty-confounded** |

Per Amendment 3, a failed gate means report and STOP. Per Amendment 4, triage gates govern only T1/T2; T0 is unaffected.

### Descriptive
| Cond | Triage recall local / stateful / contradiction | Monitor catch local / stateful / contradiction | FP | Parse |
|---|---|---|---|---|
| T0 | n/a | 100% / 79.5% / 100% (212/212) | 2/9600 | 40/40 |
| T1 | 109/109 / 105/105 / 106/106 | 109/109 / 105/105 / 106/106 | 0/4800 | 20/20 |
| T2 | 109/109 / 0/105 / 55/106 = 51.9% [42.5, 61.2] | 109/109 / 102/105 = 97.1% / 106/106 | 0/4800 | 20/20 |

- Triage coverage: 5120/5120 actions scored in both T1 and T2 (no unparseable triage output).
- Why T2 stateful recall is 0: Haiku T2 scores stateful errors mean 1.14 (max 2), clean actions mean 1.27 (n=4800); the top-24 cutoff score is 3-4 in every log. Contradictions score mean 3.30 (max 4), at the cutoff, so their 51.9% recall is set by the seeded tie-break.
- Repeat agreement on stateful engagement (T0, log catches >= half its stateful errors): 20/20 seeds; 32/40 logs engaged.
- Monitor calls with thinking tokens > 0: T0 10/40 (25%); T1 8/20 (40%); T2 18/20 (90%). T2 monitor stateful catch (97.1%) exceeds T0 (79.5%) on the same logs although T2 flagged no stateful error.

### Haiku cost per call (calls.jsonl; prices UNVERIFIED against invoice: Haiku 5.5 $0.10/$0.50 per MTok, Opus 5.5 $4/$20)
| Calls | n | Mean in / out (thinking) tokens | $/call mean (max) | Total |
|---|---|---|---|---|
| T1 triage (Haiku, whole log at N=1) | 20 | 15,783 / 6,274 (4,213) | 0.00472 (0.00560) | $0.094 |
| T2 triage (Haiku, one action) | 5,120 | 474 / 88 (79) | 0.0000916 (0.00021) | $0.469 |
| T1 monitor (Opus) | 20 | 16,249 / 1,529 (286) | 0.0956 (0.1038) | $1.911 |
| T2 monitor (Opus) | 20 | 16,249 / 1,825 (829) | 0.1015 (0.1095) | $2.030 |
