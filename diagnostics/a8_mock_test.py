"""Offline tests of the Amendment 8 tooling (no API calls). Run from repo root; prints PASS/FAIL per check.
1. runner.py --cost-cap: $25.10 already recorded, cap $25 -> every call refused, nothing scored; $24.00 recorded ->
   run completes; simulated $0.50 per call from zero, cap $9.75 -> exactly 20 calls, the rest refused.
2. End-to-end mock: runner.py --mock, arm A (default prompt) and arm B (--prompt-file monitor_prompt_global.txt),
   N=64, seeds 0-49, ABBA blocks A r1, B r1, B r2, A r2, --shuffle 8, --cost-cap 25 over both roots; grid logs copied
   in; one synthetic calls.jsonl record per attempt; analysis_global.py on both roots; primary re-derived here.
3. Known answers (scored rows edited so every gate passes; one end_turn call record per cell): readings (1) CI above 0,
   (2) CI upper bound below the grid A drop, (3) CI below 0, and the rule, for B >> A, B a little above A, B = A, B << A.
4. Gates: --gates-only prints no outcome; a changed log byte aborts; first-try parse 98/100 passes and 97/100 fails;
   end_turn 98/100 passes and 97/100 fails.
5. Stage 2 (Amendment 9, --a1/--b1): mock N=1 arms in ABBA blocks; outputs re-derived; known answers for the main
   readings (output 1: includes 0 / above 0 / below 0; output 4: above 0 yes / no), the secondary B-drop reading, both
   predictions (< +10) and the ceiling flag; --gates-only; N=1 log byte."""
import asyncio, contextlib, importlib, io, json, os, random, re, shutil, statistics, subprocess, sys, tempfile
sys.path.insert(0, os.getcwd())
import runner

passed = []
def check(name, cond, detail=""):
    passed.append(bool(cond)); print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

def run(tmp, name, reps, extra, spend_out=None, n=64):
    importlib.reload(runner); random.seed(f"{name}-{reps}")
    if spend_out is not None:
        orig = runner.mock_monitor
        def mock(*args):
            with open(os.path.join(runner.ROOT, "calls.jsonl"), "a") as f:
                f.write(json.dumps({"tag": "sim", "model": "claude-opus-5-5", "stop": "end_turn", "in": 0, "out": spend_out, "thinking": 0}) + "\n")
            return orig(*args)
        runner.mock_monitor = mock
    logs = os.path.join(tmp, name + "_mock", "logs"); os.makedirs(logs, exist_ok=True)
    for s in range(50):
        for ext in (".log", ".truth.json"): shutil.copy(f"results_grid/logs/T256_N{n}_s{s}{ext}", logs)
    sys.argv = ["runner.py", "run", "--mock", "--ns", str(n), "--seeds", "0-49", "--conds", "T0", "--subtlety", "d2h",
                "--effort", "low", "--reps", str(reps), "--root", os.path.join(tmp, name)] + extra
    with contextlib.redirect_stdout(io.StringIO()) as out: asyncio.run(runner.main())
    return out.getvalue()

def n_scored(root): d = os.path.join(root, "scored"); return len(os.listdir(d)) if os.path.isdir(d) else 0
def n_calls(root): p = os.path.join(root, "calls.jsonl"); return sum(1 for _ in open(p)) if os.path.exists(p) else 0
def ledger(root, dollars):
    os.makedirs(root, exist_ok=True)
    open(os.path.join(root, "calls.jsonl"), "w").write(json.dumps({"tag": "prior", "model": "claude-opus-5-5", "stop": "end_turn",
                                                                  "in": 0, "out": round(dollars / 20e-6), "thinking": 0}) + "\n")
def edit(root, fn):
    for f in os.listdir(os.path.join(root, "scored")):
        p = os.path.join(root, "scored", f); r = json.load(open(p)); fn(f, r); json.dump(r, open(p, "w"))
def write_calls(root, n_bad_stop=0):
    with open(os.path.join(root, "calls.jsonl"), "w") as f:
        for i, fn in enumerate(sorted(os.listdir(os.path.join(root, "scored")))):
            for att in range(json.load(open(os.path.join(root, "scored", fn)))["attempts"]):
                f.write(json.dumps({"tag": f"{fn[:-5]}#{att}", "model": "claude-opus-5-5", "stop": "max_tokens" if i < n_bad_stop else "end_turn",
                                    "in": 15863, "out": 1188, "thinking": 0}) + "\n")
def analyse(a, b, *extra):
    p = subprocess.run([sys.executable, "diagnostics/analysis_global.py", "--a", a, "--b", b, *extra], capture_output=True, text=True)
    m = re.search(r"B - A ([+-]\d+\.\d) points  95% CI \[([+-]\d+\.\d), ([+-]\d+\.\d)\]", p.stdout)
    rule = re.search(r"Amendment 8 rule: (.*)", p.stdout)
    return p, (m.groups() if m else None), (rule.group(1) if rule else ""), tuple(re.findall(r"reading \d: .*: (yes|no)", p.stdout))
def derive(root, n=64):
    c, pl = [], []
    for s in range(50):
        rs = [json.load(open(os.path.join(root, "scored", f"T256_N{n}_s{s}_T0{x}.json"))) for x in ("", "_r2")]
        c.append(statistics.mean(r["by_type"]["stateful"]["caught"] for r in rs)); pl.append(rs[0]["by_type"]["stateful"]["planted"])
    return sum(c) / sum(pl)

with tempfile.TemporaryDirectory() as tmp:
    R = lambda n: os.path.join(tmp, n + "_mock")
    print("== 1. cost cap ==")
    ledger(R("over"), 25.10); out = run(tmp, "over", 1, ["--cost-cap", "25", "--cost-roots", R("over")])
    check("$25.10 recorded, cap $25: nothing scored, 50 refusals", n_scored(R("over")) == 0 and out.count("COST CAP") == 50,
          f"scored {n_scored(R('over'))}, refusals {out.count('COST CAP')}")
    ledger(R("under"), 24.00); out = run(tmp, "under", 1, ["--cost-cap", "25", "--cost-roots", R("under")])
    check("$24.00 recorded, cap $25: run completes", n_scored(R("under")) == 50 and "COST CAP" not in out, f"scored {n_scored(R('under'))}")
    out = run(tmp, "mid", 1, ["--cost-cap", "9.75", "--cost-roots", R("mid")], spend_out=25000)
    check("$0.50 per call from $0, cap $9.75: exactly 20 calls, then refusals", n_calls(R("mid")) == 20 and n_scored(R("mid")) + out.count("COST CAP") == 50,
          f"calls {n_calls(R('mid'))}, scored {n_scored(R('mid'))}, refusals {out.count('COST CAP')}")

    print("\n== 2. end-to-end mock, ABBA blocks: A r1, B r1, B r2, A r2 ==")
    cap = ["--shuffle", "8", "--cost-cap", "25", "--cost-roots", f"{R('A')},{R('B')}"]
    pB = ["--prompt-file", "monitor_prompt_global.txt"]
    outs = [run(tmp, "A", 1, cap), run(tmp, "B", 1, cap + pB), run(tmp, "B", 2, cap + pB), run(tmp, "A", 2, cap)]
    order = [[int(x) for x in re.findall(r"done T256_N64_s(\d+)_T0(?:_r2)?  ", o)] for o in outs]
    check("each block runs 50 cells in a shuffled order (a permutation of 0-49, not sorted)",
          all(sorted(o) == list(range(50)) and o != list(range(50)) for o in order), f"block 1 starts {order[0][:6]}")
    check("blocks 3 (B) and 4 (A) run only rep-2 cells", all(o.count("_r2  parse") == 50 for o in outs[2:]))
    check("100 scored cells per arm, no cost-cap refusals", n_scored(R("A")) == n_scored(R("B")) == 100 and not any("COST CAP" in o for o in outs))
    for arm in "AB": write_calls(R(arm))
    p, est, rule, readings = analyse(R("A"), R("B"))
    d = f"{(derive(R('B')) - derive(R('A'))) * 100:+.1f}"
    check("analysis runs; printed B - A equals the independent re-derivation", p.returncode == 0 and est and est[0] == d, f"printed {est}, derived {d}")
    check("mock misses local/contradiction, so those gates FAIL: rule GATE FAILURE, no readings printed",
          "FAIL  local catch" in p.stdout and "FAIL  contradiction catch" in p.stdout and rule.startswith("GATE FAILURE") and readings == (), rule)
    print("  --- analysis_global.py output on the mock roots ---")
    print("\n".join("  " + l for l in p.stdout.splitlines()))

    print("\n== 3. known answers (all gates made to pass) ==")
    def make(name, fa, fb, src=("A", "B")):
        roots = []
        for arm, f in zip(src, (fa, fb)):
            dst = os.path.join(tmp, f"{name}_{arm}"); shutil.copytree(R(arm), dst)
            def fix(fn, r, f=f):
                r["parse_ok"], r["attempts"] = True, 1
                for t in ("local", "contradiction"): r["by_type"][t]["caught"] = r["by_type"][t]["planted"]
                r["by_type"]["stateful"]["caught"] = f(int(fn.split("_s")[1].split("_")[0]), r["by_type"]["stateful"]["planted"])
            edit(dst, fix); write_calls(dst); roots.append(dst)
        return roots
    cases = (("up", lambda s, p: 0, lambda s, p: p, ("yes", "no", "no"), "CI above 0"),
             ("partial", lambda s, p: 2, lambda s, p: 3 if s < 25 else 2, ("yes", "yes", "no"), "CI above 0"),
             ("same", lambda s, p: 2, lambda s, p: 2, ("no", "yes", "no"), "CI includes 0"),
             ("down", lambda s, p: p, lambda s, p: 0, ("no", "yes", "yes"), "CI below 0"))
    for name, fa, fb, want, rule_want in cases:
        a_root, b_root = make(name, fa, fb)
        p, est, rule, readings = analyse(a_root, b_root)
        d = f"{(derive(b_root) - derive(a_root)) * 100:+.1f}"
        check(f"{name}: readings {want}, rule '{rule_want}', estimate = re-derivation",
              readings == want and rule.startswith(rule_want) and est[0] == d, f"B - A {est}; readings {readings}; {rule}")
    print("  " + next(l.strip() for l in p.stdout.splitlines() if "grid A drop" in l))

    print("\n== 4. gates ==")
    p, _, _, _ = analyse(os.path.join(tmp, "up_A"), os.path.join(tmp, "up_B"), "--gates-only")
    check("--gates-only: ALL PASS printed, no estimate, readings or secondary", "GATES: ALL PASS" in p.stdout and "B - A" not in p.stdout
          and "reading" not in p.stdout and "SECONDARY" not in p.stdout)
    bad = os.path.join(tmp, "up_B", "logs", "T256_N64_s7.log"); t = open(bad).read(); open(bad, "w").write("X" + t[1:])
    p, _, _, _ = analyse(os.path.join(tmp, "up_A"), os.path.join(tmp, "up_B"))
    check("one byte changed in arm B's seed-7 log: analysis exits non-zero", p.returncode != 0 and "ABORT" in p.stderr + p.stdout, (p.stderr + p.stdout).strip()[-90:])
    open(bad, "w").write(t)
    for k, want in ((2, "PASS"), (3, "FAIL")):
        a_root, b_root = make(f"retry{k}", lambda s, p: 0, lambda s, p: p)
        edit(b_root, lambda fn, r: r.update(attempts=2) if int(fn.split("_s")[1].split("_")[0]) < k and "_r2" not in fn else None); write_calls(b_root)
        p, _, rule, _ = analyse(a_root, b_root)
        line = next(l.strip() for l in p.stdout.split("Gates, arm B:")[1].splitlines() if "first try" in l)
        check(f"{k} cells in B needed a retry: first-try parse gate {want}", line.startswith(want) and f"{k} retried" in line, line)
    for k, want in ((2, "PASS"), (3, "FAIL")):
        a_root, b_root = make(f"stop{k}", lambda s, p: 0, lambda s, p: p); write_calls(b_root, n_bad_stop=k)
        p, _, rule, _ = analyse(a_root, b_root)
        line = next(l.strip() for l in p.stdout.split("Gates, arm B:")[1].splitlines() if "end_turn" in l)
        check(f"{k} of 100 B calls stopped at max_tokens: end_turn gate {want}", line.startswith(want) and (rule.startswith("GATE FAILURE") == (want == "FAIL")), line)

    print("\n== 5. Stage 2 (Amendment 9): N=1 arms, ABBA blocks ==")
    cap1 = ["--shuffle", "8", "--cost-cap", "25", "--cost-roots", f"{R('A1')},{R('B1')}"]
    outs = [run(tmp, "A1", 1, cap1, n=1), run(tmp, "B1", 1, cap1 + pB, n=1), run(tmp, "B1", 2, cap1 + pB, n=1), run(tmp, "A1", 2, cap1, n=1)]
    check("N=1 arms: 100 scored cells each, rep-2 blocks run only rep-2 cells, no refusals",
          n_scored(R("A1")) == n_scored(R("B1")) == 100 and all(o.count("_r2  parse") == 50 for o in outs[2:]) and not any("COST CAP" in o for o in outs))
    for arm in ("A1", "B1"): write_calls(R(arm))
    def analyse2(a, b, a1, b1, *extra):
        p = subprocess.run([sys.executable, "diagnostics/analysis_global.py", "--a", a, "--b", b, "--a1", a1, "--b1", b1, *extra], capture_output=True, text=True)
        vals = dict(re.findall(r"  \((\d)\) [^:]*: ([+-]\d+\.\d) points", p.stdout))
        g = lambda rx: (m.group(1) if (m := re.search(rx, p.stdout)) else "")
        return p, tuple(vals.get(str(i)) for i in range(1, 5)), {
            "out1": g(r"main reading, output 1: interval (.*)"), "out4": g(r"main reading, output 4: .*: (yes|no)"),
            "out2": g(r"secondary reading, output 2: interval (.*)"), "pred1": g(r"prediction 1 .*: (met|not met)"),
            "pred2": g(r"prediction 2 .*: (met|not met)"), "ceiling": g(r"ceiling \(.*?\): (\w+)")}
    def expected(a, b, a1, b1):
        cA1, cB1, cA, cB = derive(a1, 1), derive(b1, 1), derive(a), derive(b)
        return tuple(f"{v * 100:+.1f}" for v in (cB1 - cA1, cB1 - cB, cA1 - cA, (cA1 - cA) - (cB1 - cB)))
    p, vals, r = analyse2(R("A"), R("B"), R("A1"), R("B1"))
    check("mock Stage 2: four outputs equal the independent re-derivation", p.returncode == 0 and vals == expected(R("A"), R("B"), R("A1"), R("B1")), f"{vals}")
    check("mock N=1 misses local/contradiction: Stage 2 gates FAIL, no readings or predictions printed",
          "GATE FAILURE" in p.stdout and all(r[k] == "" for k in ("out1", "out4", "out2", "pred1", "pred2")),
          next((l.strip() for l in p.stdout.splitlines() if "GATE FAILURE" in l), ""))
    print("  --- analysis_global.py Stage 2 output on the mock roots ---")
    print("\n".join("  " + l for l in p.stdout.splitlines()))
    NO_LIFT, LIFT1, NEITHER = "includes 0: no detectable lift from B at N=1", "entirely above 0: B lifts at N=1 too", "entirely below 0: matches neither reading"
    NO_DROP, PERSIST = "includes 0: no detectable drop under B", "entirely above 0: the drop persists under B"
    cases = (("nodrop", (1, 3, 3, 3), (NO_LIFT, "yes", NO_DROP, "met", "met", "no")),
             ("persist", (1, 1, 3, 3), (NO_LIFT, "no", PERSIST, "met", "not met", "no")),
             ("lift1", (1, 3, 1, 3), (LIFT1, "no", NO_DROP, "not met", "met", "no")),
             ("negative", (1, 3, 3, 1), (NEITHER, "yes", NEITHER, "met", "met", "no")),
             ("ceiling", (0, "p", "p", "p"), (NO_LIFT, "yes", NO_DROP, "met", "met", "yes")))
    f = lambda v: (lambda s, p: p) if v == "p" else (lambda s, p, v=v: v)
    for name, (A64, B64, A1, B1), want in cases:
        a, b = make(name + "64", f(A64), f(B64)); a1, b1 = make(name + "1", f(A1), f(B1), src=("A1", "B1"))
        p, vals, r = analyse2(a, b, a1, b1)
        got = (r["out1"], r["out4"], r["out2"], r["pred1"], r["pred2"], r["ceiling"])
        check(f"{name}: output 1 '{want[0]}', output 4 above 0 {want[1]}, B drop '{want[2]}', predictions {want[3]}/{want[4]}, ceiling {want[5]}",
              got == want and vals == expected(a, b, a1, b1), f"{vals}; {got}")
    p, *_ = analyse2(*[os.path.join(tmp, x) for x in ("nodrop64_A", "nodrop64_B", "nodrop1_A1", "nodrop1_B1")], "--gates-only")
    check("Stage 2 --gates-only: ALL PASS, no outputs", "GATES: ALL PASS" in p.stdout and "OUTPUTS" not in p.stdout and "B drop" not in p.stdout)
    bad = os.path.join(tmp, "nodrop1_B1", "logs", "T256_N1_s3.log"); t = open(bad).read(); open(bad, "w").write("X" + t[1:])
    p, *_ = analyse2(*[os.path.join(tmp, x) for x in ("nodrop64_A", "nodrop64_B", "nodrop1_A1", "nodrop1_B1")])
    check("one byte changed in a Stage 2 N=1 log: analysis exits non-zero", p.returncode != 0 and "ABORT" in p.stderr + p.stdout)

print(f"\n{sum(passed)}/{len(passed)} checks passed")
