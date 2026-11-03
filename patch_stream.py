import sys
p = "runner.py"; r = open(p).read()
old = '''            r = await self.c.messages.create(model=model, max_tokens=max_tokens, extra_body=extra or None,
                                             messages=[{"role": "user", "content": prompt}])'''
new = '''            async with self.c.messages.stream(model=model, max_tokens=max_tokens, extra_body=extra or None,
                                              messages=[{"role": "user", "content": prompt}]) as s:
                r = await s.get_final_message()   # streaming: SDK requires it for large max_tokens'''
if new in r: sys.exit("already patched")
assert r.count(old) == 1, "unexpected runner.py - send me a screenshot"
open(p, "w").write(r.replace(old, new)); print("patched")
