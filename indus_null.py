"""Indus under the same three nulls. Section 9's claim is that Indus is the safe
case: large signal, close catalogues. The signal there was measured against the
same pooled shuffle that turned out to be wrong for rongorongo's AA, and the
Indus corpus is 3 574 short texts, so pooling mixes across texts too.
"""
import io, sys, math, random
sys.path.insert(0, ".")
sys.path.insert(0, "indus")
from horley import stats

rng = random.Random(20260822)
SHUF = 50
o = []; p = o.append

# reuse the loader from indus.py without running its main()
src = io.open("indus/indus.py", encoding="utf-8").read()
src = src.replace('if __name__ == "__main__":\n    main()', "")
import os
ns = {"__name__": "indusmod", "__file__": os.path.abspath(os.path.join("indus","indus.py"))}
cwd = os.getcwd()
exec(src, ns)

loader = ns.get("read_m77")
p("loader: read_m77 (Mahadevan 1977, uncertain readings dropped)")
if loader:
    runs = loader(False)
    if isinstance(runs, tuple): runs = runs[0]
    s = stats(runs)
    p("Indus: L=%d n=%d Hcn=%.4f  texts=%d" % (s["L"], s["n"], s["hcn"], len(runs)))

    def shuffled(mode):
        if mode == "pooled":
            flat = [t for r in runs for t in r]
            rng.shuffle(flat)
            out, i = [], 0
            for r in runs:
                out.append(flat[i:i+len(r)]); i += len(r)
            return out
        out = []
        for r in runs:
            q = r[:]; rng.shuffle(q); out.append(q)
        return out

    p("  %-8s %10s %10s" % ("null", "null Hcn", "signal"))
    res = {}
    for mode in ("pooled", "run"):
        vals = [stats(shuffled(mode))["hcn"] for _ in range(SHUF)]
        mu = sum(vals)/len(vals)
        res[mode] = s["hcn"] - mu
        p("  %-8s %10.4f %+10.4f" % (mode, mu, s["hcn"] - mu))
    p("  -> within-text null keeps %.0f%% of the pooled signal" % (100*res["run"]/res["pooled"]))
    p("")
    p("  For comparison, rongorongo keeps 75%% (horley) / 71%% (numeric) under its")
    p("  strictest local null, and Indus texts are so short (mean 3.7) that the")
    p("  within-text null is nearly the strictest one available.")

txt="\n".join(o)
io.open("indus_null_results.txt","w",encoding="utf-8").write(txt+"\n")
sys.stdout.buffer.write((txt+"\n").encode("utf-8","replace"))
