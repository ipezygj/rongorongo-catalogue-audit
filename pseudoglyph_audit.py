"""Two CEIPP codes are not signs, and the numeric readings count them as signs.

  000  is written 000! in 380 of its 390 occurrences: a glyph is present on the
       object but the edition declines to identify it. Under the numeric reading
       it becomes a single sign type of 390 tokens -- the 6th commonest "sign".
  999  is the vertical divider of the Santiago Staff (Sproat, ror pages), 97
       tokens, all on one object.

The Horley reading drops both (the map returns nothing, and unmapped codes are
treated as breaks). The numeric and full-variant readings keep them. Two of the
three rungs of the ladder in section 4 are therefore measured on a stream
containing a frequent pseudo-sign. This asks how much that matters.
"""
import io, sys, re
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_plain, tokens_horley
from sweep import measure
import random

rng = random.Random(20260822)
NOT_SIGNS = {"000", "999"}
o = []
p = o.append


def strip_pseudo(runs):
    """Treat 000/999 as breaks in the chain, exactly as a lacuna is treated."""
    out = []
    for r in runs:
        cur = []
        for t in r:
            if re.match(r"^(\d+)", t).group(1) in NOT_SIGNS:
                if cur:
                    out.append(cur); cur = []
            else:
                cur.append(t)
        if cur:
            out.append(cur)
    return out


lines = read_lines()
variants = {
    "numeric 633":  [r for s in lines for r in tokens_plain(s, True)],
    "full 1897":    [r for s in lines for r in tokens_plain(s, False)],
    "horley 125":   [r for s in lines for r in tokens_horley(s)],
}

p("=" * 92)
p("EFFECT OF TREATING 000 AND 999 AS NON-SIGNS")
p("=" * 92)
p("%-14s %26s   %26s" % ("reading", "as published", "pseudo-signs removed"))
p("%-14s %6s %7s %7s %5s   %6s %7s %7s %5s" % ("", "L", "Hcn", "sig", "n", "L", "Hcn", "sig", "n"))
res = {}
for name, runs in variants.items():
    a = measure(runs, rng, 60)
    b = measure(strip_pseudo(runs), rng, 60)
    res[name] = (a, b)
    p("%-14s %6d %7.3f %+7.3f %5d   %6d %7.3f %+7.3f %5d"
      % (name, a["L"], a["hcn"], a["sig"], a["n"], b["L"], b["hcn"], b["sig"], b["n"]))

p("")
p("LADDER SPREAD (the headline of section 4)")
for j, lab in ((0, "as published"), (1, "pseudo-signs removed")):
    hs = [res[k][j]["hcn"] for k in variants]
    sig = min(abs(res[k][j]["sig"]) for k in variants), max(abs(res[k][j]["sig"]) for k in variants)
    spread = max(hs) - min(hs)
    best = max(abs(res[k][j]["sig"]) for k in variants)
    p("  %-22s spread %.3f | best |signal| %.3f | ratio %.2fx"
      % (lab, spread, best, spread / best))

txt = "\n".join(o)
io.open("pseudoglyph_audit_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
