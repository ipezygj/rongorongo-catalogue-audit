"""Same three nulls applied to the reference languages, run lengths matched.

If the languages also fall to ~0.5 under a run-level null, then the contrast in
Appendix A survives in reduced form. If they stay at 0.5 under every null while
rongorongo moves from 1.58 to 0.61, the claim does not survive as stated.
"""
import io, sys, random
from collections import Counter
sys.path.insert(0, ".")
from syllabary_ref import syllabify, load_rap, load_mri, load_linb
from fingerprint2 import object_runs
from korovina_ref import clean, RAP_C
import glob, os

rng = random.Random(20260822)
REPS = 12
MRI_C = ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"]
o = []; p = o.append


def aa(runs):
    h = t = 0
    for r in runs:
        for i in range(len(r) - 1):
            t += 1
            if r[i] == r[i + 1]: h += 1
    return h, t


def exp_aa(runs, mode, pool=None):
    tot = 0.0
    for _ in range(REPS):
        if mode == "run":
            sh = [(lambda q: (rng.shuffle(q), q)[1])(r[:]) for r in runs]
        else:
            flat = (pool[:] if mode == "global" else [t for r in runs for t in r])
            rng.shuffle(flat)
            sh, i = [], 0
            for r in runs:
                sh.append(flat[i:i + len(r)]); i += len(r)
        tot += aa(sh)[0]
    return tot / REPS


def recut(runs, lengths):
    """Re-cut a token stream into the given multiset of run lengths."""
    flat = [t for r in runs for t in r]
    out, i, j = [], 0, 0
    while i < len(flat) and j < len(lengths):
        L = lengths[j % len(lengths)]
        out.append(flat[i:i + L]); i += L; j += 1
    return [r for r in out if len(r) > 1]


# rongorongo run-length profile, per object
objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    ob = os.path.basename(path)[:-4]
    r = object_runs(path, "horley")
    if sum(len(x) for x in r) >= 300: objs[ob] = r
rr_lengths = sorted(len(r) for runs in objs.values() for r in runs)

refs = {}
refs["Rapa Nui (NT)"] = syllabify(load_rap()[0], RAP_C, True)
refs["Maori (NT)"] = syllabify(load_mri(), MRI_C, True)
refs["Linear B"] = load_linb()
for nm in ["Isla6", "Englert"]:
    refs["Rapa Nui (%s)" % nm] = syllabify(
        clean(io.open("korovina_files/%s.txt" % nm, encoding="utf-8-sig").read())[0], RAP_C, True)

p("=" * 88)
p("AA observed/expected under three nulls, references RE-CUT to rongorongo run lengths")
p("=" * 88)
p("%-20s %8s %9s %9s %9s" % ("reference", "tokens", "global", "text", "run"))
for name, runs in refs.items():
    runs = recut(runs, rr_lengths)
    pool = [t for r in runs for t in r]
    h, _ = aa(runs)
    row = [name, len(pool)]
    for mode in ("global", "object", "run"):
        e = exp_aa(runs, mode, pool)
        row.append(h / e if e > 0.5 else float("nan"))
    p("%-20s %8d %9.2f %9.2f %9.2f" % tuple(row))

p("")
p("rongorongo, same three nulls (from null_choice.py): global 1.58, object 1.13, run 0.61")
txt = "\n".join(o)
io.open("null_choice2_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
