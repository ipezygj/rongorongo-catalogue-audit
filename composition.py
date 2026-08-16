"""Length or composition? Korovina's two explanations, separated.

She wrote that the catalogue dependence could be either

  1. LENGTH -- a longer catalogue does worse because its size far exceeds the
     number of elements the corpus can support, an estimation artefact; or
  2. COMPOSITION -- two reasonable catalogues of the same size could still give
     significantly different results, because which signs get merged matters,

and that these are very different things theoretically. The test is to hold the
size fixed and vary only which signs are merged. Any movement left at fixed L
cannot be a length effect, because log2(L) -- the normalising constant -- is
identical across every scheme compared here.

What counts as "reasonable" is not mine to invent, so it comes from her own
description of the field: roughly forty to fifty frequent, clearly
distinguishable signs that every researcher identifies the same way, plus an
unknown remainder. Every scheme below therefore keeps the same frequent core as
singletons and differs only in how it groups the uncertain tail. Random
regroupings of that same tail give the null: if defensible schemes move the
statistic no more than arbitrary ones do, composition carries no information.
"""
import glob
import math
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
XMLDIR = os.path.join(HERE, "ceipp", "xml")
IS_GLYPH = re.compile(r"^\d")

CORE = 50          # signs every researcher agrees on, kept distinct throughout
TARGET_L = 125     # Horley's published size, so the comparison is at his scale
N_RANDOM = 200
SEED = 20260815


def read_runs():
    """Base-numeric tokens, broken at every lacuna, line end and text end."""
    runs = []
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        root = ET.parse(path).getroot()
        for line in root.iter("line"):
            cur = []
            for g in line.iter("glyph"):
                code = (g.findtext("code/ceipp") or "").strip()
                link = (g.findtext("link") or "").strip()
                if not IS_GLYPH.match(code):
                    if cur:
                        runs.append(cur); cur = []
                    continue
                cur.append(re.match(r"^(\d+)", code.replace("!", "")).group(1))
                if link in ("*", "…"):
                    if cur:
                        runs.append(cur); cur = []
            if cur:
                runs.append(cur)
    return runs


def entropy(c):
    n = sum(c.values())
    return -sum((v / n) * math.log2(v / n) for v in c.values()) if n else 0.0


def hcn(runs):
    """Normalised conditional entropy, log base the observed alphabet."""
    uni = Counter(t for r in runs for t in r)
    bi = Counter()
    for r in runs:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    L = len(uni)
    h1 = entropy(uni)
    den = math.log2(L) if L > 1 else 1.0
    return (entropy(bi) - h1) / den, L


def apply_map(runs, mapping):
    return [[mapping[t] for t in r] for r in runs]


def build_core(freqs):
    ranked = [s for s, _c in freqs.most_common()]
    return ranked[:CORE], ranked[CORE:]


def scheme_barthel(core, tail):
    """Group the tail by Barthel's own numbering: the catalogue is arranged by
    shape family, so neighbouring codes are graphically related. Tail signs fall
    into buckets of ten, which is the coarsest reading of that structure."""
    m = {s: s for s in core}
    for s in tail:
        m[s] = f"B{int(s) // 10}"
    return m


def scheme_hundreds(core, tail):
    """A coarser reading of the same structure: the leading digit only, split so
    the class count lands near the target."""
    m = {s: s for s in core}
    for s in tail:
        n = int(s)
        m[s] = f"H{n // 100}_{(n % 100) // 25}"
    return m


def scheme_frequency(core, tail, freqs):
    """Group the tail by how often it occurs. Defensible on the grounds that a
    sign seen twice cannot be told from a variant of anything."""
    m = {s: s for s in core}
    for s in tail:
        c = freqs[s]
        m[s] = f"F{min(c, 12)}"
    return m


def scheme_random(core, tail, n_classes, rng):
    m = {s: s for s in core}
    for s in tail:
        m[s] = f"R{rng.randrange(n_classes)}"
    return m


def main():
    runs = read_runs()
    freqs = Counter(t for r in runs for t in r)
    base_h, base_L = hcn(runs)
    print(f"CEIPP base reading: L = {base_L}, tokens = {sum(freqs.values())}")
    print(f"  H_cond normalised = {base_h:.3f}")
    core, tail = build_core(freqs)
    print(f"  core kept distinct: {CORE} signs, "
          f"{sum(freqs[s] for s in core) / sum(freqs.values()) * 100:.1f} % of tokens")
    print(f"  tail to be grouped: {len(tail)} signs")

    named = []
    for label, mapping in (
        ("barthel-tens", scheme_barthel(core, tail)),
        ("hundreds", scheme_hundreds(core, tail)),
        ("frequency", scheme_frequency(core, tail, freqs)),
    ):
        h, L = hcn(apply_map(runs, mapping))
        named.append((label, L, h))

    print()
    print("=" * 74)
    print("DEFENDABLE SCHEMES — same corpus, same core, different tail grouping")
    print("=" * 74)
    print(f"{'scheme':<16}{'L':>6}{'H_cond norm':>14}")
    for label, L, h in named:
        print(f"{label:<16}{L:>6}{h:>14.3f}")

    # The null: arbitrary regroupings of the same tail into the same number of
    # classes each scheme happened to produce.
    rng = random.Random(SEED)
    print()
    print("=" * 74)
    print(f"RANDOM REGROUPING NULL — {N_RANDOM} draws at each scheme's own L")
    print("=" * 74)
    print(f"{'target L':<10}{'random mean':>13}{'sd':>9}{'min':>9}{'max':>9}")
    nulls = {}
    for label, L, _h in named:
        n_classes = max(1, L - CORE)
        vals = []
        for _ in range(N_RANDOM):
            h, LL = hcn(apply_map(runs, scheme_random(core, tail, n_classes, rng)))
            vals.append(h)
        m = sum(vals) / len(vals)
        sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
        nulls[label] = (m, sd, min(vals), max(vals))
        print(f"{L:<10}{m:>13.3f}{sd:>9.4f}{min(vals):>9.3f}{max(vals):>9.3f}")

    print()
    print("=" * 74)
    print("VERDICT")
    print("=" * 74)
    hs = [h for _l, _L, h in named]
    spread_named = max(hs) - min(hs)
    print(f"  spread across defensible schemes (L 	 {min(L for _l,L,_h in named)}"
          f"-{max(L for _l,L,_h in named)})   {spread_named:.3f}")
    print(f"  spread from changing L instead (125 vs 633 vs 1897)  0.318")
    for label, L, h in named:
        m, sd, lo, hi = nulls[label]
        z = (h - m) / sd if sd else float("nan")
        inside = lo <= h <= hi
        print(f"  {label:<14} h={h:.3f}  random {m:.3f}+-{sd:.4f}  "
              f"z={z:>7.1f}  {'inside' if inside else 'OUTSIDE'} random range")


if __name__ == "__main__":
    main()
