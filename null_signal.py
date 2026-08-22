"""The headline signal is measured against a pooled shuffle. Is it null-dependent too?

horley.reshuffle flattens every run of the whole corpus into one list, shuffles it
and re-cuts. The corpus is 25 objects with different vocabularies, so that null
destroys between-object vocabulary differences as well as sequential order, and
credits both to "signal". The reference languages are single texts, where the
distinction does not arise -- so section 7 compares an object-mixed signal against
an unmixed one.

Three nulls, same data, same estimator:
  pooled   shuffle the whole corpus together        (what the paper reports)
  object   shuffle within each object               (keeps each object's vocabulary)
  run      shuffle within each run                  (keeps local vocabulary too)
"""
import io, sys, glob, os, random, math
from collections import Counter
sys.path.insert(0, ".")
from horley import stats
from fingerprint2 import object_runs

rng = random.Random(20260822)
SHUF = 60
o = []; p = o.append


def shuffled(objruns, mode):
    """objruns: dict obj -> runs. Returns one shuffled corpus as a flat run list."""
    if mode == "pooled":
        flat = [t for runs in objruns.values() for r in runs for t in r]
        rng.shuffle(flat)
        out, i = [], 0
        for runs in objruns.values():
            for r in runs:
                out.append(flat[i:i + len(r)]); i += len(r)
        return out
    out = []
    for runs in objruns.values():
        if mode == "object":
            flat = [t for r in runs for t in r]
            rng.shuffle(flat)
            i = 0
            for r in runs:
                out.append(flat[i:i + len(r)]); i += len(r)
        else:
            for r in runs:
                q = r[:]; rng.shuffle(q); out.append(q)
    return out


for reading in ("horley", "numeric"):
    objruns = {}
    for path in sorted(glob.glob("ceipp/xml/*.xml")):
        ob = os.path.basename(path)[:-4]
        r = object_runs(path, reading)
        if sum(len(x) for x in r) >= 100:
            objruns[ob] = r
    allruns = [r for runs in objruns.values() for r in runs]
    s = stats(allruns)
    p("=" * 78)
    p("READING: %-8s  L=%d  n=%d  Hcn=%.4f" % (reading, s["L"], s["n"], s["hcn"]))
    p("=" * 78)
    p("  %-8s %10s %10s %10s" % ("null", "null Hcn", "signal", "z"))
    res = {}
    for mode in ("pooled", "object", "run"):
        vals = [stats(shuffled(objruns, mode))["hcn"] for _ in range(SHUF)]
        mu = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - mu) ** 2 for v in vals) / (len(vals) - 1))
        sig = s["hcn"] - mu
        res[mode] = sig
        p("  %-8s %10.4f %+10.4f %10.1f" % (mode, mu, sig, sig / sd if sd else float("nan")))
    p("  -> object-preserving null gives %.0f%% of the pooled signal"
      % (100 * res["object"] / res["pooled"]))

p("")
p("=" * 78)
p("CONSEQUENCE FOR THE HEADLINE (section 4)")
p("=" * 78)
p("  ladder spread (published)                 0.318")
p("  best |signal|, pooled null (published)    0.077  -> ratio 4.14x")
txt = "\n".join(o)
io.open("null_signal_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
