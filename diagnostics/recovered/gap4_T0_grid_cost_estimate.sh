# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:13:08.625Z UTC = 2026-11-09 21:13:08 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 89, tool_use_id toolu_01V6QKexSoVpysoGgoaLDXKR
# Original output (verbatim tool result): diagnostics/recovered/gap4_T0_grid_cost_estimate.transcript_out.txt
# Reported in: 2026-11-09 run report, overwritten (T0 grid pre-run estimate $36)
cd ~/dev/oversight-capacity && python3 -c "
import json
rs=[json.loads(l) for l in open('results_pilot/calls.jsonl')]
import statistics as st
ins=[r['in'] for r in rs]; outs=[r['out'] for r in rs]
print('n',len(rs),'models',set(r['model'] for r in rs),'stops',set(r['stop'] for r in rs))
print('in mean',st.mean(ins),'max',max(ins),'out mean',st.mean(outs),'max',max(outs))
c=[r['in']*4e-6+r['out']*20e-6 for r in rs]
print('cost/call mean %.4f max %.4f'%(st.mean(c),max(c)))
print('T0 grid 400 calls est \$%.2f (+1 parse retry per 2%% -> \$%.2f)'%(400*st.mean(c),400*st.mean(c)*1.02))
"; ls results_grid 2>/dev/null; echo "grid dir exists: $?"; ls ~/.anthropic_key && stat -f '%z bytes' ~/.anthropic_key
