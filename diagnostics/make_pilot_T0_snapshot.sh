#!/bin/bash
# Rebuild results_pilot as it stood after the T0 pilot (2026-11-03) and before the T1/T2 pilot (2026-11-09)
# appended to it, so the recovered gap1/gap4 commands can be re-run verbatim from a different working folder.
# Offline; reads results_pilot/ only. Run from the repo root. Output: results_pilot_T0_snapshot/ (gitignored by results*/).
set -euo pipefail
SRC=results_pilot
SNAP=results_pilot_T0_snapshot
[ -e "$SNAP" ] && { echo "$SNAP exists; remove it first" >&2; exit 1; }
mkdir -p "$SNAP/$SRC/scored"
ln -s ../.venv "$SNAP/.venv"   # gap1 calls .venv/bin/python relative to its working folder

# scored: T0 files by name (rep 1 has no suffix, rep 2 is _r2)
files=$(find -E "$SRC/scored" -type f -regex '.*/T256_N1_s[0-9]+_T0(_r[0-9]+)?\.json' | sort)
n=$(echo "$files" | grep -c .)
[ "$n" -eq 40 ] || { echo "expected 40 T0 scored files, found $n" >&2; exit 1; }
bad=$(for f in $files; do [ "$(stat -f '%Sm' -t '%Y-%m-%d' "$f")" = 2026-11-03 ] || echo "$f"; done)
[ -z "$bad" ] || { echo "scored files not dated 2026-11-03: $bad" >&2; exit 1; }
cp -p $files "$SNAP/$SRC/scored/"

# calls.jsonl: T0 monitor records by tag; they must be exactly lines 1-40
grep -nE '^\{"tag": "T256_N1_s[0-9]+_T0(_r[0-9]+)?#[0-9]+"' "$SRC/calls.jsonl" > "$SNAP/.t0_lines"
k=$(wc -l < "$SNAP/.t0_lines" | tr -d ' ')
[ "$k" -eq 40 ] || { echo "expected 40 T0 records, found $k" >&2; exit 1; }
[ "$(cut -d: -f1 "$SNAP/.t0_lines" | paste -sd, -)" = "$(seq 1 40 | paste -sd, -)" ] || { echo "T0 records are not lines 1-40" >&2; exit 1; }
cut -d: -f2- "$SNAP/.t0_lines" > "$SNAP/$SRC/calls.jsonl"
rm "$SNAP/.t0_lines"
cmp -s "$SNAP/$SRC/calls.jsonl" <(head -n 40 "$SRC/calls.jsonl") || { echo "snapshot calls.jsonl != first 40 lines" >&2; exit 1; }
echo "snapshot OK: $n scored files (all mtime 2026-11-03), $k calls.jsonl records = lines 1-40"
