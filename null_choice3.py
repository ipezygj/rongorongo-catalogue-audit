"""AA, AAA and ABAB under three nulls, rongorongo and the references.

null_choice.py showed rongorongo's AA figure is an artefact of pooling 25
objects into one unigram distribution: 1.58 (global) -> 1.13 (per object) ->
0.61 (per run), while the languages sit at 0.5-0.75 under all three. Appendix A
also reports AAA at 5-15 times and ABAB at 30-100 times expectation. Those come
from the same pooled null, so they need the same test before anything is claimed.
"""
import io, sys, random, glob, os
sys.path.insert(0, ".")
from fingerprint2 import object_runs
from syllabary_ref import syllabify, load_rap, load_mri, load_linb
from korovina_ref import clean, RAP_C

rng = random.Random(20260822)
REPS = 12
MRI_C = ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"]
o = []; p = o.append


def patterns(runs):
    """AA, AAA, ABAB counts in one pass."""
    aa = aaa = abab = 0
    for r in runs:
        n = len(r)
        for i in range(n - 1):
            if r[i] == r[i + 1]:
                aa += 1
                if i + 2 < n and r[i + 2] == r[i]: aaa += 1
            if i + 3 < n and r[i] == r[i + 2] and r[i + 1] == r[i + 3] and r[i] != r[i + 1]:
                abab += 1
    return aa, aaa, abab


def shuffle_like(runs, mode, pool):
    if mode == "run":
        out = []
        for r in runs:
            q = r[:]; rng.shuffle(q); out.append(q)
        return out
    flat = pool[:] if mode == "global" else [t for r in runs for t in r]
    rng.shuffle(flat)
    out, i = [], 0
    for r in runs:
        out.append(flat[i:i + len(r)]); i += len(r)
    return out


def ratios(runs, mode, pool):
    obs = patterns(runs)
    exp = [0.0, 0.0, 0.0]
    for _ in range(REPS):
        c = patterns(shuffle_like(runs, mode, pool))
        for j in range(3): exp[j] += c[j] / REPS
    return [(obs[j] / exp[j]) if exp[j] > 0.5 else float("nan") for j in range(3)], obs


def recut(runs, lengths):
    flat = [t for r in runs for t in r]
    out, i, j = [], 0, 0
    while i < len(flat) and j < len(lengths):
        L = lengths[j % len(lengths)]
        out.append(flat[i:i + L]); i += L; j += 1
    return [r for r in out if len(r) > 1]


objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    ob = os.path.basename(path)[:-4]
    r = object_runs(path, "horley")
    if sum(len(x) for x in r) >= 300: objs[ob] = r
rr_runs = [r for runs in objs.values() for r in runs]
rr_pool = [t for r in rr_runs for t in r]
rr_lengths = sorted(len(r) for r in rr_runs)

p("=" * 92)
p("AA / AAA / ABAB, observed divided by expectation, under three nulls")
p("=" * 92)
p("%-22s %19s %19s %19s" % ("", "null = global", "null = per text/object", "null = per run"))
p("%-22s %6s%6s%7s %6s%6s%7s %6s%6s%7s" % ("", "AA", "AAA", "ABAB", "AA", "AAA", "ABAB", "AA", "AAA", "ABAB"))

row = ["rongorongo (pooled)"]
for mode in ("global", "object", "run"):
    if mode == "object":
        obs = [0, 0, 0]; exp = [0.0, 0.0, 0.0]
        for ob, runs in objs.items():
            pool = [t for r in runs for t in r]
            o2 = patterns(runs)
            e = [0.0, 0.0, 0.0]
            for _ in range(REPS):
                c = patterns(shuffle_like(runs, "object", pool))
                for j in range(3): e[j] += c[j] / REPS
            for j in range(3): obs[j] += o2[j]; exp[j] += e[j]
        r3 = [(obs[j] / exp[j]) if exp[j] > 0.5 else float("nan") for j in range(3)]
    else:
        r3, _ = ratios(rr_runs, mode, rr_pool)
    row += r3
p("%-22s %6.2f%6.2f%7.1f %6.2f%6.2f%7.1f %6.2f%6.2f%7.1f" % tuple(row))

refs = {}
refs["Rapa Nui (NT)"] = syllabify(load_rap()[0], RAP_C, True)
refs["Maori (NT)"] = syllabify(load_mri(), MRI_C, True)
refs["Linear B"] = load_linb()
refs["Rapa Nui (Isla6)"] = syllabify(clean(io.open("korovina_files/Isla6.txt", encoding="utf-8-sig").read())[0], RAP_C, True)

for name, runs in refs.items():
    runs = recut(runs, rr_lengths)
    pool = [t for r in runs for t in r]
    row = [name]
    for mode in ("global", "object", "run"):
        r3, _ = ratios(runs, mode, pool)
        row += r3
    p("%-22s %6.2f%6.2f%7.1f %6.2f%6.2f%7.1f %6.2f%6.2f%7.1f" % tuple(row))

p("")
p("Appendix A of version 2 states: AA 1.6-2.4, AAA 5-15, ABAB 30-100 for rongorongo,")
p("against languages 0.5-0.6 on AA, AAA near zero, ABAB 2.5-7.7. Those are the")
p("'global' column. The question is whether the contrast survives the other two.")

txt = "\n".join(o)
io.open("null_choice3_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
