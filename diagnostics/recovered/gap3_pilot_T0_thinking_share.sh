# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:36:35.004Z UTC = 2026-11-09 21:36:35 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 409, tool_use_id toolu_01G2DEmpx73myTcKj6QMcUBV
# Original output (verbatim tool result): diagnostics/recovered/gap3_pilot_T0_thinking_share.transcript_out.txt
# Reported in: reports/pilot.md (T0 monitor thinking 10/40); PREREG Amendment 7 (25%)
cd ~/dev/oversight-capacity && .venv/bin/python -c "
import json
cs=[json.loads(l) for l in open('results_pilot/calls.jsonl')][:40]
print(sum((r['thinking'] or 0)>0 for r in cs),'/',len(cs), set(r['tag'].split('_')[3][:2] for r in cs))"
