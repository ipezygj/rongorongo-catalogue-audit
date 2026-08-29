"""The specific ABAB event instances for TOKI ADZE (Horley 63), SHELL (70), and
SMALL SHELL (17) -- Davletshin asked to see these directly, to check whether they
are real or a transliteration artefact.

    python davletshin_examples.py 63 70 17
"""
import io, sys, glob, os
sys.path.insert(0, ".")
from fingerprint2 import object_runs

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
TARGETS = set(sys.argv[1:]) or {"63", "70", "17"}


def find_abab(run):
    """Yield (i, a, b) for every ABAB window r[i..i+3] = a,b,a,b, a != b."""
    for i in range(len(run) - 3):
        a, b = run[i], run[i + 1]
        if run[i + 2] == a and run[i + 3] == b and a != b:
            yield i, a, b


def context(run, i, span=3):
    lo, hi = max(0, i - span), min(len(run), i + 4 + span)
    marked = []
    for j in range(lo, hi):
        tok = run[j]
        marked.append(f"[{tok}]" if i <= j < i + 4 else tok)
    return " ".join(marked)


total_by_code = {c: 0 for c in TARGETS}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    runs = object_runs(path, "horley")
    if sum(len(r) for r in runs) < 100:
        continue
    name = os.path.basename(path)[:-4]
    for run in runs:
        for i, a, b in find_abab(run):
            hit = {c for c in (a, b) if c in TARGETS}
            if not hit:
                continue
            for c in hit:
                total_by_code[c] += 1
            print(f"{name}  pos {i}  pair ({a},{b})  hit={sorted(hit)}", file=out)
            print(f"    {context(run, i)}", file=out)

print("\nTotals (each event counted once per target code it involves,", file=out)
print("matching davletshin_signs.py's per-sign abab[] counter):", file=out)
for c in sorted(TARGETS):
    print(f"  {c}: {total_by_code[c]}", file=out)
out.flush()
