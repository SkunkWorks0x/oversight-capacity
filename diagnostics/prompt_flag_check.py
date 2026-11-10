"""Offline check of runner.py --prompt-file (no API calls). Run from repo root.
Renders the T0 monitor prompt for results_grid logs seed 0, N=1 and N=64 three ways, capturing the exact string
passed to Client.ask: runner.py at 1840d18 (the code that ran the grid; unchanged since b585e66), the patched
runner.py with no flag, and the patched runner.py with --prompt-file monitor_prompt_global.txt (via main(), --mock)."""
import asyncio, contextlib, difflib, hashlib, importlib, io, json, os, shutil, subprocess, sys, tempfile, types
sys.path.insert(0, os.getcwd())
import runner

REF, KEYS = "1840d18", [(1, 0), (64, 0)]

def git_show(path):
    return subprocess.run(["git", "show", f"{REF}:{path}"], capture_output=True, text=True, check=True).stdout

class Rec:
    prompts = {}
    def __init__(self, mock=True): self.usage, self.stops = {}, {}
    async def ask(self, model, prompt, max_tokens, mock_fn=None, tag=""):
        Rec.prompts[tag] = prompt; return mock_fn()

def seed_logs(root):
    os.makedirs(os.path.join(root, "logs"))
    for n, s in KEYS:
        for ext in (".log", ".truth.json"):
            shutil.copy(f"results_grid/logs/T256_N{n}_s{s}{ext}", os.path.join(root, "logs"))

def run_main(mod, tmp, name, extra):
    Rec.prompts = {}; mod.Client = Rec; seed_logs(os.path.join(tmp, name + "_mock"))
    sys.argv = ["runner.py", "run", "--mock", "--ns", "1,64", "--seeds", "0", "--conds", "T0", "--subtlety", "d2h",
                "--effort", "low", "--root", os.path.join(tmp, name)] + extra
    with contextlib.redirect_stdout(io.StringIO()) as out: asyncio.run(mod.main())
    scored = [json.load(open(os.path.join(tmp, name + "_mock", "scored", f"T256_N{n}_s{s}_T0.json"))) for n, s in KEYS]
    return {k: Rec.prompts[f"T256_N{n}_s{s}_T0#0"] for k, (n, s) in zip(KEYS, KEYS)}, scored, out.getvalue()

h = lambda x: hashlib.sha256(x.encode()).hexdigest()[:16]
assert open("monitor_prompt.txt").read() == git_show("monitor_prompt.txt")
print(f"monitor_prompt.txt identical to {REF}: yes")

with tempfile.TemporaryDirectory() as tmp:
    old = types.ModuleType("runner_ref"); old.__file__ = os.path.abspath("runner.py")
    exec(compile(git_show("runner.py"), f"runner.py@{REF}", "exec"), old.__dict__)
    old.ROOT, old.SUBT = os.path.join(tmp, "ref"), "d2h"; seed_logs(old.ROOT); Rec.prompts = {}
    for n, s in KEYS: asyncio.run(old.run_one(Rec(), n, s, "T0", 256))
    ref = {(n, s): Rec.prompts[f"T256_N{n}_s{s}_T0#0"] for n, s in KEYS}

    importlib.reload(runner); dflt, sc_d, _ = run_main(runner, tmp, "dflt", [])
    importlib.reload(runner); glob_, sc_g, out_g = run_main(runner, tmp, "glob", ["--prompt-file", "monitor_prompt_global.txt"])

    print("\n== default render vs grid code render (T0, seed 0) ==")
    for k in KEYS:
        print(f"N={k[0]:2d}: grid-code sha256[:16] {h(ref[k])} len {len(ref[k])} | patched default {h(dflt[k])} len {len(dflt[k])}"
              f" | byte-identical: {'yes' if dflt[k] == ref[k] else 'NO'}")

    print("\n== --prompt-file monitor_prompt_global.txt (mock run via main) ==")
    tmpl = open("monitor_prompt_global.txt").read()
    for (n, s), sc in zip(KEYS, sc_g):
        log = open(f"results_grid/logs/T256_N{n}_s{s}.log").read()
        expect = tmpl.replace("{MAX}", "32").replace("{LOG}", log.rstrip("\n"))
        d = [l for l in difflib.unified_diff(dflt[(n, s)].splitlines(), glob_[(n, s)].splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        print(f"N={n:2d}: equals template render: {'yes' if glob_[(n, s)] == expect else 'NO'}; lines differing from default render: "
              f"{sum(l[0] == '-' for l in d)} removed, {sum(l[0] == '+' for l in d)} added; scored parse_ok {sc['parse_ok']}")
    print("diff of rendered prompts, N=64 (default -> global):")
    for l in difflib.unified_diff(dflt[(64, 0)].splitlines(), glob_[(64, 0)].splitlines(), lineterm="", n=0):
        if l[:3] not in ("+++", "---"): print("  " + l)
    print(f"mock run printed {out_g.count('done ')} 'done' lines and the report ({'GRID' in out_g})")

    bad = os.path.join(tmp, "bad_prompt.txt"); open(bad, "w").write(tmpl.replace("{LOG}", ""))
    importlib.reload(runner)
    try:
        run_main(runner, tmp, "bad", ["--prompt-file", bad]); print("\nguard: NOT raised")
    except AssertionError as e:
        print(f"\nguard: template without {{LOG}} -> AssertionError: {str(e).replace(tmp, '<tmp>')}")
