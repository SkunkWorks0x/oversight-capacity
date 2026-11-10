# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:14:12.505Z UTC = 2026-11-09 21:14:12 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 161, tool_use_id toolu_01GLwVGwzajcZaYR28P6sHs9
# Original output (verbatim tool result): diagnostics/recovered/gap1_pilot_T0_gates.transcript_out.txt
# Reported in: reports/pilot.md (T0 gate rows, difficulty rule, T0 descriptive row, repeat agreement); PREREG Amendment 7 (79.5%, 20.5 points)
cd ~/dev/oversight-capacity && .venv/bin/python - <<'EOF'
import json, glob, math, re
def wilson(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return p,c-h,c+h
rows=[json.load(open(f)) for f in sorted(glob.glob('results_pilot/scored/*.json'))]
print(len(rows), sorted(set((r['cond'],r['n'],r['effort'],r['rep']) for r in rows)))
for t in ['local','stateful','contradiction']:
    k=sum(r['by_type'][t]['caught'] for r in rows); n=sum(r['by_type'][t]['planted'] for r in rows)
    p,lo,hi=wilson(k,n); print(f"{t:13s} {k}/{n} = {p:.1%} [{lo:.1%},{hi:.1%}]")
fp=sum(r['fp'] for r in rows); cl=sum(r['clean_actions'] for r in rows); print('FP',fp,cl,f"{fp/cl:.2%}", 'fp_decoy',sum(r['fp_decoy'] for r in rows))
print('parse_ok',sum(r['parse_ok'] for r in rows),'first try',sum(r['parse_ok'] and r['attempts']==1 for r in rows))
# engagement: log catches >= half its stateful errors
eng={}
for r in rows:
    s=r['by_type']['stateful']; eng[(r['seed'],r['rep'])]= s['caught']>=s['planted']/2
seeds=sorted(set(r['seed'] for r in rows))
agree=sum(eng[(s,1)]==eng[(s,2)] for s in seeds); print('engaged logs',sum(eng.values()),'/',len(eng),' rep agreement',agree,'/',len(seeds))
print('per-log stateful caught:', [(r['seed'],r['rep'],r['by_type']['stateful']['caught'],r['by_type']['stateful']['planted']) for r in rows][:6])
EOF
ls /private/tmp/claude-501/-Users-imani-dev-oversight-capacity/*/scratchpad/*.md 2>/dev/null
