# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:36:03.578Z UTC = 2026-11-09 21:36:03 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 381, tool_use_id toolu_01JTAAG3XP4a2a8pZ7nST4Xp
# Original output (verbatim tool result): diagnostics/recovered/gap2_T2_scores_and_thinking.transcript_out.txt
# Reported in: reports/pilot.md (T2 score means and cutoff; T1/T2 monitor thinking shares); PREREG Amendment 7 (90%)
cd ~/dev/oversight-capacity && .venv/bin/python - <<'EOF'
import json, glob, statistics as st
from collections import defaultdict
cs=[json.loads(l) for l in open('results_pilot/calls.jsonl')]
t0=[r for r in cs[:40]]; print('pilot T0 mon thinking mean', st.mean(r['thinking'] or 0 for r in t0), 'out', st.mean(r['out'] for r in t0))
g=[json.loads(l) for l in open('results_grid/calls.jsonl')]; print('grid T0 mon thinking mean', st.mean(r['thinking'] or 0 for r in g), 'share>0', sum((r['thinking'] or 0)>0 for r in g)/len(g))
for c in ['T1','T2']:
    m=[r for r in cs if f'_{c}#' in r['tag']]; print(c,'mon thinking share>0', sum((r['thinking'] or 0)>0 for r in m)/len(m))
# T2 score distribution by action class
by=defaultdict(list); thr=[]
for f in glob.glob('results_pilot/triage/T2/*.json'):
    tri=json.load(open(f)); truth=json.load(open(f.replace('triage/T2','logs').replace('.json','.truth.json')))
    et={e['action']:e['type'] for e in truth['errors']}
    for a,s in tri['scores'].items(): by[et.get(a,'clean')].append(s)
    thr.append(min(tri['scores'][a] for a in tri['top_k']))
for k,v in by.items(): print(f'T2 score {k:13s} n={len(v)} mean={st.mean(v):.2f} max={max(v)} share>=5={sum(x>=5 for x in v)/len(v):.2f}')
print('top-24 cutoff score per log: min', min(thr), 'median', st.median(thr), 'max', max(thr))
EOF
stat -f '%SB start  %Sm end' results_pilot/run_stdout_T1T2.log; stat -f '%SB start  %Sm end' results_grid/run_stdout.log
