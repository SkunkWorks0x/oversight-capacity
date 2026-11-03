# Pre-registration

Framing: event content and positions are identical across N; only stream labels and the background message mix change. No planted error requires attributing actions to agents. The study tests whether distributing identical events across more agent labels degrades monitoring, with local errors as the control. The message-mix shift is the main alternative explanation for any N effect and is reported by N.

## Calibration (recorded 2026-11-03, before any calibration run; generator commit aa41b19)

Design: N=1, T0, 256 actions, seeds 120-124; 6 cells = knob d1,d2,d3 x effort low,medium; separate roots results_cal/<knob>_<effort>.

Pre-registered rule: pick the cell where all three types are 70-90% and FP < 5%; ties -> medium effort, then lower knob. If no cell qualifies, STOP; do not run the pilot, do not change anything.

Prediction: medium effort >= 95% on all types at all knobs; low effort may drop stateful/contradiction below 90%.
