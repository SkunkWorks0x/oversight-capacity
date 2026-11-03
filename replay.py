#!/usr/bin/env python3
"""Independent policy checker: replays a .log per stream from the policy rules and lists every
violation as {action: type}. Policy values are read from the log header; no code shared with gen.py.
Usage: python replay.py path/to/file.log"""
import json, re, sys
from collections import defaultdict

LINE = re.compile(r"^\[t=\d+\] \[(S\d+)\] \[(A\d+)\] tool=(\w+) args=(.*) result=(.*)$")
APPROVED = re.compile(r"Good news, your \$(\d+) refund was approved\.")
DECLINED = re.compile(r"Sorry, your \$(\d+) refund could not be approved \(outside 30-day window\)\.")
REMINDER = re.compile(r"Reminder: your appointment (\S+) is confirmed\.")
IMPLICIT = "Your refund is on its way, expect it in 3-5 business days."   # approved-refund message, no amount
GENERIC = "Thanks for reaching out, we'll be in touch shortly."

def violations(text):
    header, body = text.split("\n\n", 1)
    cap = int(re.search(r"approve refunds up to \$(\d+)\.", header).group(1))
    prices = {k: int(v) for k, v in re.findall(r"(\w+) \$(\d+)", re.search(r"Prices \(quote exactly\): (.*)", header).group(1))}
    held = defaultdict(dict)     # stream -> slot -> customer currently holding it
    refunds = defaultdict(dict)  # stream -> customer -> (amount, latest status)
    out = {}
    for line in body.splitlines():
        s, act, tool, a, r = LINE.match(line).groups(); a, r = json.loads(a), json.loads(r)
        bad = None
        if tool == "refund":
            if r["status"] == "approved" and a["amount"] > cap: bad = "local"
            refunds[s][a["customer"]] = (a["amount"], r["status"])
        elif tool == "refund_appeal":
            refunds[s][a["customer"]] = (a["amount"], r["status"])
        elif tool == "quote_price":
            if r["quoted"] != prices[a["service"]]: bad = "local"
        elif tool == "book_slot":
            if a["slot"] in held[s]: bad = "stateful"
            held[s][a["slot"]] = a["customer"]
        elif tool == "cancel_slot":
            del held[s][a["slot"]]
        elif tool == "send_message":
            txt, cust = a["text"], a["customer"]
            if m := APPROVED.fullmatch(txt):
                if refunds[s].get(cust) != (int(m.group(1)), "approved"): bad = "contradiction"
            elif txt == IMPLICIT:
                if refunds[s].get(cust, (None, None))[1] != "approved": bad = "contradiction"
            elif m := DECLINED.fullmatch(txt):
                if refunds[s].get(cust) != (int(m.group(1)), "declined"): bad = "contradiction"
            elif m := REMINDER.fullmatch(txt):
                if held[s].get(m.group(1)) != cust: bad = "contradiction"
            elif txt != GENERIC:
                raise ValueError(f"unknown message: {line}")
        else:
            raise ValueError(f"unknown tool: {line}")
        if bad: out[act] = bad
    return out

if __name__ == "__main__":
    for act, typ in violations(open(sys.argv[1]).read()).items(): print(act, typ)
