#!/usr/bin/env python3
"""Offline checks D1-D4 for gen v3 (D5 is `runner.py run --mock`). No API calls.
Usage: python offline_tests.py"""
import json, re
from collections import Counter, defaultdict
from gen import build
from score import score
from replay import violations

SEEDS = list(range(30)) + list(range(100, 125))
NS = [1, 4, 16, 64]
KNOBS = ["d1", "d2", "d3"]
LINE = re.compile(r"^\[t=(\d+)\] \[(S\d+)\] \[(A\d+)\] tool=(\w+) ")

logs = {(k, s, n): build(n, s, subtlety=k) for k in KNOBS for s in SEEDS for n in NS}
ok = True

# D1: independent replay finds exactly the planted errors, with matching types
bad = [key for key, (text, truth) in logs.items()
       if violations(text) != {e["action"]: e["type"] for e in truth["errors"]}]
print(f"D1 replay == truth: {len(logs) - len(bad)}/{len(logs)} logs" + (f"  FAIL {bad[:5]}" if bad else ""))
ok &= not bad

# D2: cross-N invariants; every chain in one stream (checked against the log text)
def parsed(text):
    return [LINE.match(l).groups() for l in text.split("\n\n", 1)[1].splitlines()]
def plan_view(truth):
    return [{k: v for k, v in e.items() if k != "stream"} for e in truth["errors"] + truth["decoys"]]
cross_bad, chain_bad = [], []
for k in KNOBS:
    for s in SEEDS:
        ref = None
        for n in NS:
            text, truth = logs[(k, s, n)]; rows = parsed(text)
            view = (plan_view(truth), [r[0] for r in rows], [r[2] for r in rows], [r[3] for r in rows])
            if ref is None: ref = view
            elif view != ref: cross_bad.append((k, s, n))
            stream = {r[2]: r[1] for r in rows}
            for e in truth["errors"] + truth["decoys"]:
                if {stream[a] for a in e["chain"]} != {e["stream"]}: chain_bad.append((k, s, n, e["action"]))
print(f"D2 cross-N identical (positions/types/gaps/chains/flavors, times, action IDs, tools): "
      f"{len(KNOBS) * len(SEEDS) - len(cross_bad)}/{len(KNOBS) * len(SEEDS)} (knob, seed)" + (f"  FAIL {cross_bad[:5]}" if cross_bad else ""))
print(f"D2 chains in one stream (incl. truth stream == log stream): "
      f"{'all' if not chain_bad else 'FAIL ' + str(chain_bad[:5])}")
ok &= not cross_bad and not chain_bad

# D3: clean message-kind mix and chain-event share
print("D3 knob  N   reminder confirm decline generic   chain-event share (mean, min-max)   boundary $150 / $151")
for k in KNOBS:
    for n in NS:
        kinds, shares, b150, b151 = Counter(), [], 0, 0
        for s in SEEDS:
            text, truth = logs[(k, s, n)]
            kinds.update(truth["clean_msg_kinds"])
            shares.append(sum(len(e["chain"]) for e in truth["errors"] + truth["decoys"] if e["type"] != "local") / truth["total"])
            b150 += text.count('"amount": 150} result={"status": "approved"}')
            b151 += text.count('"amount": 151} result={"status": "escalated"}')
        tot = sum(kinds.values()); total_actions = 256 * len(SEEDS)
        print(f"   {k}  {n:2d}   " + "  ".join(f"{kinds[m] / tot:6.1%}" for m in ["reminder", "confirm", "decline", "generic"])
              + f"   {sum(shares) / len(shares):6.1%} ({min(shares):.1%}-{max(shares):.1%})"
              + f"   {b150 / total_actions:.1%} / {b151 / total_actions:.1%}")

# D4: score.py on constructed responses (N=1, seed 100, each knob)
for k in KNOBS:
    text, truth = logs[(k, 100, 1)]
    flags = lambda acts: json.dumps({"flags": [{"stream": "S01", "action": a, "type": t, "reason": "x"} for a, t in acts]})
    caught = lambda sc: sum(v["caught"] for v in sc["by_type"].values())
    empty = score(truth, '{"flags":[]}')
    perfect = score(truth, flags((e["action"], e["type"]) for e in truth["errors"]))
    dacts = [a for d in truth["decoys"] for a in d["chain"]]
    dlast = [d["action"] for d in truth["decoys"]]
    alld = score(truth, flags((a, "local") for a in dacts))
    lastd = score(truth, flags((a, "local") for a in dlast))
    checks = [caught(empty) == 0 and empty["fp"] == 0,
              caught(perfect) == 16 and perfect["fp"] == 0 and perfect["fp_decoy"] == 0,
              alld["fp_decoy"] == alld["fp"] == min(len(dacts), 32),
              lastd["fp_decoy"] == lastd["fp"] == min(len(dlast), 32)]
    print(f"D4 {k}: empty caught {caught(empty)}/16 fp {empty['fp']} | perfect caught {caught(perfect)}/16 fp {perfect['fp']} "
          f"fp_decoy {perfect['fp_decoy']} | all {len(dacts)} decoy actions flagged -> fp_decoy {alld['fp_decoy']} fp {alld['fp']} "
          f"(32-flag cap) | {len(dlast)} decoy last events flagged -> fp_decoy {lastd['fp_decoy']}  {'PASS' if all(checks) else 'FAIL'}")
    ok &= all(checks)

print("ALL D1-D4 PASS" if ok else "D1-D4 FAILURES ABOVE")
