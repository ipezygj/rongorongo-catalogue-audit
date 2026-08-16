"""Length or composition, with the length held exactly fixed.

The first attempt let each grouping rule land on its own alphabet size, which
put length back into the comparison it was supposed to remove. Here every
scheme is cut to exactly the same number of classes, so the alphabet size, the
token count and the normalising constant are identical across all of them and
the only thing that differs is which signs share a class.

Each rule supplies an ordering of the uncertain tail; the tail is then cut into
the same number of contiguous blocks whatever the rule. The frequent core that
Korovina describes as identified alike by every researcher is kept distinct
throughout, so the schemes differ only where the field itself is unsure.
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

CORE = 50
TARGET_L = 125            # Horley's published size
N_RANDOM = 300
SEED = 20260815


def read_runs():
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
    uni = Counter(t for r in runs for t in r)
    bi = Counter()
    for r in runs:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    L = len(uni)
    h1 = entropy(uni)
    den = math.log2(L) if L > 1 else 1.0
    return (entropy(bi) - h1) / den, L


def cut(order, n_classes):
    """Cut an ordering of the tail into n_classes contiguous blocks."""
    m, size = {}, len(order) / n_classes
    for i, s in enumerate(order):
        m[s] = f"C{min(int(i / size), n_classes - 1)}"
    return m


def main():
    runs = read_runs()
    freqs = Counter(t for r in runs for t in r)
    ranked = [s for s, _c in freqs.most_common()]
    core, tail = ranked[:CORE], ranked[CORE:]
    n_classes = TARGET_L - CORE

    orders = {
        # Barthel's catalogue is arranged by shape, so numeric proximity is
        # graphical proximity: the standard defence for merging neighbours.
        "numeric": sorted(tail, key=int),
        # A sign seen twice cannot be told from a variant of something else.
        "frequency": sorted(tail, key=lambda s: (-freqs[s], int(s))),
        # The leading digit is the coarsest shape family, ordered within it by
        # frequency rather than by code.
        "family": sorted(tail, key=lambda s: (int(s) // 100, -freqs[s])),
    }

    print(f"corpus L={len(freqs)}  tokens={sum(freqs.values())}")
    print(f"core kept distinct: {CORE} signs = "
          f"{sum(freqs[s] for s in core)/sum(freqs.values())*100:.1f} % of tokens")
    print(f"tail: {len(tail)} signs cut into {n_classes} classes -> L = {TARGET_L}")

    print()
    print("=" * 74)
    print("DEFENDABLE SCHEMES, ALL AT EXACTLY THE SAME L")
    print("=" * 74)
    print(f"{'scheme':<12}{'L':>6}{'H_cond norm':>14}")
    results = {}
    for label, order in orders.items():
        mapping = dict(cut(order, n_classes))
        mapping.update({s: s for s in core})
        h, L = hcn([[mapping[t] for t in r] for r in runs])
        results[label] = (L, h)
        print(f"{label:<12}{L:>6}{h:>14.3f}")

    rng = random.Random(SEED)
    vals = []
    for _ in range(N_RANDOM):
        shuffled = tail[:]
        rng.shuffle(shuffled)
        mapping = dict(cut(shuffled, n_classes))
        mapping.update({s: s for s in core})
        h, _L = hcn([[mapping[t] for t in r] for r in runs])
        vals.append(h)
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))

    print()
    print("=" * 74)
    print(f"ARBITRARY REGROUPING AT THE SAME L — {N_RANDOM} draws")
    print("=" * 74)
    print(f"  mean {m:.4f}   sd {sd:.4f}   range {min(vals):.4f} .. {max(vals):.4f}")

    hs = [h for _L, h in results.values()]
    spread = max(hs) - min(hs)

    print()
    print("=" * 74)
    print("VERDICT")
    print("=" * 74)
    print(f"  composition alone, L fixed at {TARGET_L}        {spread:.3f}")
    print(f"  arbitrary regrouping, same L (sd)          {sd:.4f}")
    print(f"  changing L instead (125 / 633 / 1897)      0.318")
    print()
    for label, (L, h) in results.items():
        z = (h - m) / sd if sd else float("nan")
        print(f"  {label:<11} h={h:.3f}   z vs arbitrary = {z:>8.1f}")
    print()
    print(f"  composition / length  =  {spread:.3f} / 0.318  = "
          f"{spread/0.318*100:.0f} % of the length effect")


if __name__ == "__main__":
    main()
