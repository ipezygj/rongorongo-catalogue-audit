"""Add Horley's ~126-basic-glyph reading to the ladder and rerun the comparison.

rongopy ships the Barthel -> Horley map (638 keys -> 126 distinct basic
glyphs, 372 of the keys decomposing a ligature into its parts). Applying it to
the CEIPP XML corpus makes the two ends of the ladder correspond to actual
published positions on what counts as one sign, instead of to reduction rules
I invented.

CEIPP codes are zero-padded and carry variant letters ("022bfy"); Horley keys
are not padded and carry fewer variants ("22f"). Lookup therefore strips the
padding and then peels variant letters one at a time. Codes that reach no entry,
and codes the map sends to "?", are treated as breaks in the chain exactly like
a lacuna -- inventing a token for them would put structure where the map
declines to.
"""
import glob
import io
import math
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
XMLDIR = os.path.join(HERE, "ceipp", "xml")
SHUFFLES = 200
SEED = 20260815
IS_GLYPH = re.compile(r"^\d")

_ns = {}
exec(io.open(os.path.join(HERE, "rongopy", "horley_encoding.py"),
             encoding="utf-8").read(), _ns)
HORLEY = _ns["horley_encoding"]


def horley_lookup(code):
    """Map one CEIPP code to a list of Horley basic glyphs, or None."""
    c = code.replace("!", "")
    m = re.match(r"^0*(\d+)([a-zA-Z]*)$", c)
    if not m:
        return None
    num, suffix = m.group(1), m.group(2)
    # Try the full variant first, then drop variant letters from the right.
    for i in range(len(suffix), -1, -1):
        key = num + suffix[:i]
        if key in HORLEY:
            parts = str(HORLEY[key]).split()
            if any(p == "?" for p in parts):
                return None
            return parts
    return None


def read_lines():
    out = []
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        root = ET.parse(path).getroot()
        for line in root.iter("line"):
            seq = [((g.findtext("code/ceipp") or "").strip(),
                    (g.findtext("link") or "").strip())
                   for g in line.iter("glyph")]
            if seq:
                out.append(seq)
    return out


def tokens_horley(seq):
    runs, cur = [], []
    for code, link in seq:
        if not IS_GLYPH.match(code):
            if cur:
                runs.append(cur); cur = []
            continue
        parts = horley_lookup(code)
        if parts is None:
            if cur:
                runs.append(cur); cur = []
            continue
        cur.extend(parts)
        if link in ("*", "…"):
            if cur:
                runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return runs


def tokens_plain(seq, numeric_only):
    runs, cur = [], []
    for code, link in seq:
        if not IS_GLYPH.match(code):
            if cur:
                runs.append(cur); cur = []
            continue
        s = code.replace("!", "")
        cur.append(re.match(r"^(\d+)", s).group(1) if numeric_only else s)
        if link in ("*", "…"):
            if cur:
                runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return runs


def entropy(c):
    n = sum(c.values())
    return -sum((v / n) * math.log2(v / n) for v in c.values()) if n else 0.0


def stats(runs):
    uni = Counter(t for r in runs for t in r)
    bi = Counter()
    for r in runs:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    L = len(uni)
    h1 = entropy(uni)
    hc = entropy(bi) - h1
    den = math.log2(L) if L > 1 else 1.0
    return {"L": L, "n": sum(uni.values()), "h1n": h1 / den, "hcn": hc / den,
            "cov": len(bi) / (L * L) if L else 0.0}


def reshuffle(runs, rng):
    flat = [t for r in runs for t in r]
    rng.shuffle(flat)
    out, i = [], 0
    for r in runs:
        out.append(flat[i:i + len(r)]); i += len(r)
    return out


def main():
    rng = random.Random(SEED)
    lines = read_lines()

    # How much of the corpus does the map actually reach?
    total = mapped = 0
    unmapped = Counter()
    for seq in lines:
        for code, _l in seq:
            if not IS_GLYPH.match(code):
                continue
            total += 1
            if horley_lookup(code) is None:
                unmapped[code] += 1
            else:
                mapped += 1
    print("=" * 78)
    print("HORLEY-KARTAN KATTAVUUS CEIPP-KORPUKSESSA")
    print("=" * 78)
    print(f"  koodattuja glyfeja      : {total}")
    print(f"  kartta osuu             : {mapped}  ({mapped/total*100:.1f} %)")
    print(f"  ei osu / kartta sanoo ? : {total-mapped}  "
          f"({(total-mapped)/total*100:.1f} %)")
    print(f"  yleisimmat osumattomat  : {unmapped.most_common(8)}")

    ladders = [
        ("full", lambda s: tokens_plain(s, False)),
        ("base", lambda s: tokens_plain(s, True)),
        ("horley", tokens_horley),
    ]
    rows = []
    for name, fn in ladders:
        runs = [r for seq in lines for r in fn(seq)]
        s = stats(runs)
        nulls = [stats(reshuffle(runs, rng))["hcn"] for _ in range(SHUFFLES)]
        m = sum(nulls) / len(nulls)
        sd = math.sqrt(sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1))
        s["null"], s["sd"], s["sig"] = m, sd, s["hcn"] - m
        rows.append((name, s))

    print()
    print("=" * 78)
    print("TIKAPUUT — paatepisteet vastaavat nyt JULKAISTUJA kantoja")
    print("=" * 78)
    print(f"{'luenta':<9}{'L':>7}{'tokenit':>9}{'peitto':>9}{'H1n':>8}"
          f"{'Hcn':>8}{'signaali':>10}{'z':>8}")
    for n, s in rows:
        z = s["sig"] / s["sd"] if s["sd"] else float("nan")
        print(f"{n:<9}{s['L']:>7}{s['n']:>9}{s['cov']*100:>8.2f}%"
              f"{s['h1n']:>8.3f}{s['hcn']:>8.3f}{s['sig']:>10.3f}{z:>8.1f}")

    hcn = [s["hcn"] for _n, s in rows]
    span = max(hcn) - min(hcn)
    sig = max(abs(s["sig"]) for _n, s in rows)
    print()
    print("=" * 78)
    print("RATKAISU")
    print("=" * 78)
    print(f"  luennan hajonta      : {span:.3f}  = {span*100:.1f} % asteikosta")
    print(f"  rakennesignaali      : {sig:.3f}")
    print(f"  suhde                : {span/sig:.1f}x")


if __name__ == "__main__":
    main()
