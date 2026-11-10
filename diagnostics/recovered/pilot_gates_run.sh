# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:35:26.095Z UTC = 2026-11-09 21:35:26 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 372, tool_use_id toolu_018LqCKVt7g83nszE3rheZvw
# Original output (verbatim tool result): diagnostics/recovered/pilot_gates_run.transcript_out.txt
# Reported in: wrapper that ran pilot_gates.py: reports/pilot.md (T1/T2 rows, Haiku cost table); 2026-11-09 run report (T1/T2 grid cost estimate)
cd ~/dev/oversight-capacity && L=results_pilot/run_stdout_T1T2.log && grep -E '^EXIT|JOB ERROR|jobs failed|API usage|stop reasons|MISMATCH|Traceback|parse=FAIL' $L; echo "done: $(grep -c '^done ' $L)"; ls results_pilot results_pilot/triage/*| head; ls results_pilot/triage/T1 | wc -l; ls results_pilot/triage/T2 | wc -l; .venv/bin/python /private/tmp/claude-501/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5/scratchpad/pilot_gates.py results_pilot
