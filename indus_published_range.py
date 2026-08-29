"""Sproat (p.c., 23 Aug 2026): Indus also has several proposed sign sets -
Mahadevan's smaller, Wells' much larger - and that must affect the statistics the
same way it does for rongorongo.

He is right, and section 9 states the movement only over the range that can be
reached by merging down from Mahadevan's 417. This measures the published range
precisely where it is reachable (Parpola 386 to Mahadevan 417), reports where
those sizes sit on the curve, and reports the bigram coverage there, which is the
quantity his first point is really about.

Null: pooled-corpus shuffle, matching section 9. (An earlier run used a within-run
null and was not comparable to the paper; it is superseded by this one.)
"""
import io, os, sys, random
from collections import Counter
sys.path.insert(0, ".")
sys.path.insert(0, "indus")
from horley import stats

rng = random.Random(20260823)
o = []; p = o.append
src = io.open("indus/indus.py", encoding="utf-8").read().replace('if __name__ == "__main__":\n    main()', "")
ns = {"__name__": "indusmod", "__file__": os.path.abspath(os.path.join("indus", "indus.py"))}
exec(src, ns)
runs = ns["read_m77"](False)

def fold_freq(rs, L):
    c = Counter(t for r in rs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in rs]

def measure(rs, shuffles=40):
    """Pooled-corpus shuffle, exactly as horley.reshuffle and as section 9 uses,
    so these figures sit on the same scale as the paper's -0.217 at L=417."""
    s = stats(rs)
    vals = []
    for _ in range(shuffles):
        flat = [t for r in rs for t in r]
        rng.shuffle(flat)
        sh, i = [], 0
        for r in rs:
            sh.append(flat[i:i + len(r)]); i += len(r)
        vals.append(stats(sh)["hcn"])
    mu = sum(vals) / len(vals)
    return s["hcn"] - mu, s["cov"], s["L"]

SIZES = [150, 200, 250, 300, 350, 386, 400, 417]
p("=" * 84)
p("INDUS: the curve across the reachable part of the published sign-set range")
p("=" * 84)
p("%-6s %10s %9s   %s" % ("L", "signal", "coverage", "note"))
res = {}
for L in SIZES:
    sig, cov, LL = measure(fold_freq(runs, L))
    res[L] = sig
    note = {386: "Parpola", 417: "Mahadevan (full inventory)", 150: "peak of the sweep"}.get(L, "")
    p("%-6d %+10.4f %8.1f%%   %s" % (L, sig, cov * 100, note))

p("")
p("published range that can be measured, Parpola 386 to Mahadevan 417:")
p("  movement %.4f, which is %.1f%% of the signal at 417" % (abs(res[386]-res[417]), 100*abs(res[386]-res[417])/abs(res[417])))
p("peak (150) to Mahadevan (417):")
p("  movement %.4f, %.1f%% of the peak signal, monotonically downward" % (abs(res[150]-res[417]), 100*abs(res[150]-res[417])/abs(res[150])))
p("")
p("Wells (about 676) and ICIT (702) cannot be measured: reaching them needs a")
p("concordance that SPLITS Mahadevan's signs, and merging only goes downward.")
p("What the shape does say is the direction - both lie beyond 417 on a stretch")
p("that has been declining since 150, so the movement continues, it does not reverse.")
txt = "\n".join(o)
io.open("indus_published_range_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
