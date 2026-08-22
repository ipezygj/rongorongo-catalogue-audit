"""Is rongorongo's 'repetition seeking' a property of the script or of the null?

Appendix A of the paper says rongorongo seeks immediate repetition, AA at 1.6-2.4
times expectation, where syllabified Rapa Nui and Maori avoid it at 0.5-0.6. The
languages were single homogeneous texts. The rongorongo figure was computed
against a CORPUS-WIDE unigram shuffle -- but the corpus is 25 objects with
different vocabularies, so a corpus-wide unigram distribution is a mixture, and
any locally concentrated stream looks repetition-seeking against a mixture.

This compares three nulls on the same data:
  global    shuffle all tokens of the corpus together (what the paper used)
  object    shuffle within each object
  run       shuffle within each run (the strictest local null)
"""
import io, re, sys, glob, os, random
from collections import Counter
import xml.etree.ElementTree as ET
sys.path.insert(0, ".")
from fingerprint2 import object_runs

rng = random.Random(20260822)
REPS = 15
o = []; p = o.append


def aa_rate(runs):
    hit = tot = 0
    for r in runs:
        for i in range(len(r) - 1):
            tot += 1
            if r[i] == r[i + 1]: hit += 1
    return hit, tot


def shuffled_rate(runs, mode, objid=None, pool=None):
    hits = 0.0; tot = 0
    for _ in range(REPS):
        if mode == "run":
            sh = []
            for r in runs:
                q = r[:]; rng.shuffle(q); sh.append(q)
        else:
            flat = pool[:] if mode == "global" else [t for r in runs for t in r]
            rng.shuffle(flat)
            sh, i = [], 0
            for r in runs:
                sh.append(flat[i:i + len(r)]); i += len(r)
                if i > len(flat): break
        h, t = aa_rate(sh); hits += h; tot = t
    return hits / REPS, tot


objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    obj = os.path.basename(path)[:-4]
    runs = object_runs(path, "horley")
    if sum(len(r) for r in runs) >= 300:
        objs[obj] = runs
allpool = [t for runs in objs.values() for r in runs for t in r]

p("=" * 86)
p("AA (immediate repetition), observed / expected, under three nulls")
p("=" * 86)
p("%-6s %7s %9s %9s %9s" % ("object", "tokens", "global", "object", "run"))
tot_obs = 0; tot_n = 0
for obj, runs in objs.items():
    h, t = aa_rate(runs); tot_obs += h; tot_n += t
    row = [obj, sum(len(r) for r in runs)]
    for mode in ("global", "object", "run"):
        e, _ = shuffled_rate(runs, mode, obj, allpool)
        row.append(h / e if e > 0.5 else float("nan"))
    p("%-6s %7d %9.2f %9.2f %9.2f" % tuple(row))

p("")
p("WHOLE CORPUS pooled (this is the figure Appendix A reports)")
allruns = [r for runs in objs.values() for r in runs]
h, t = aa_rate(allruns)
for mode in ("global", "object", "run"):
    if mode == "object":
        # expected under per-object shuffles, summed
        e = sum(shuffled_rate(runs, "object", obj, allpool)[0] for obj, runs in objs.items())
    else:
        e, _ = shuffled_rate(allruns, mode, None, allpool)
    p("  null = %-7s  AA observed %d, expected %.1f  ->  %.2fx" % (mode, h, e, h / e))

txt = "\n".join(o)
io.open("null_choice_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
