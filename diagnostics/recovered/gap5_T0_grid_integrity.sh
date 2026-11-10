# RECOVERED one-off command, not a maintained script. Bash tool input copied verbatim from the session transcript; not edited.
# Original run: 2026-11-10T02:22:07.301Z UTC = 2026-11-09 21:22:07 EST (-0500)
# Recovered: 2026-11-09 (EST)
# Transcript source: ~/.claude/projects/-Users-imani-dev-oversight-capacity/713cce0c-02bf-420e-b85b-20fde824b5a5.jsonl line 273, tool_use_id toolu_01JPXARyZ5dNDvtrHbDRxmeE
# Original output (verbatim tool result): diagnostics/recovered/gap5_T0_grid_integrity.transcript_out.txt
# Reported in: 2026-11-09 run report, overwritten (T0 grid integrity, $35.28 spent)
cd ~/dev/oversight-capacity && L=results_grid/run_stdout.log && grep -E '^EXIT|JOB ERROR|jobs failed|API usage|stop reasons|MISMATCH|Traceback' $L; echo "done lines: $(grep -c '^done ' $L)  FAIL: $(grep -c 'parse=FAIL' $L)"; .venv/bin/python - <<'EOF'
import json, glob, os, re
from collections import Counter
rows=[json.load(open(f)) for f in glob.glob('results_grid/scored/*.json')]
print('scored files', len(rows), 'raw files', len(glob.glob('results_grid/raw/*.json')))
cells=Counter((r['n'],r['seed']) for r in rows)
print('cells', len(cells), 'reps/cell', set(cells.values()), 'conds', set(r['cond'] for r in rows), 'effort', set(r['effort'] for r in rows), 'total', set(r['total'] for r in rows))
print('N x seeds', {n: len({s for (m,s) in cells if m==n}) for n in [1,4,16,64]}, 'seed range', min(s for _,s in cells), max(s for _,s in cells))
print('parse_ok', sum(r['parse_ok'] for r in rows), 'first try', sum(r['parse_ok'] and r['attempts']==1 for r in rows))
odd=[f for f in os.listdir('results_grid/scored')+os.listdir('results_grid/raw')+os.listdir('results_grid/logs') if ' ' in f or not re.match(r'^T256_N\d+_s\d+', f)]
print('odd/conflict-named files', odd[:5], len(odd))
t=[json.load(open(f)) for f in glob.glob('results_grid/logs/*.truth.json')]
print('truth gen/subtlety', Counter((x['gen_version'],x['subtlety']) for x in t))
cs=[json.loads(l) for l in open('results_grid/calls.jsonl')]
c=lambda r:r['in']*4e-6+r['out']*20e-6
print('calls', len(cs), 'models', Counter(r['model'] for r in cs), 'stops', Counter(r['stop'] for r in cs), 'retries(#1)', sum(r['tag'].endswith('#1') for r in cs))
print('spent $%.2f  $/call %.4f  in mean %.0f  out mean %.0f max %d' % (sum(map(c,cs)), sum(map(c,cs))/len(cs), sum(r['in'] for r in cs)/len(cs), sum(r['out'] for r in cs)/len(cs), max(r['out'] for r in cs)))
EOF
ls results_grid; git status --porcelain=v1
