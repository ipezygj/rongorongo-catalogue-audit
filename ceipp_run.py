"""Repeat the whole battery on the independent CEIPP/Spaelti XML corpus.

Source: kohaumotu.org/Rongorongo/xml/{A..Y}.xml -- 25 objects, one <glyph>
element each carrying a <ceipp> code and a <link> separator. rongopy covers
13 objects; this is the full corpus, so it answers whether the earlier result
was an artefact of the smaller selection.

Sequence breaks are respected rather than glossed: a bigram is only counted
when both glyphs are genuinely adjacent on the object. Lacunae ("(3-5)!" marks
an estimated number of lost signs), illegible glyphs ("_"), empty placeholder
elements, line ends and text ends all cut the chain. Counting across a gap
would invent adjacencies that the artefact does not attest.

Three readings of the same edition, each matching a stated position in the
literature on what counts as one sign:

    full    numeric code + variant letters, compounds split   (Barthel/CEIPP)
    base    numeric code only, compounds split                (variants merged)
    fused   numeric code only, ligature-joined glyphs merged  (Horley-style)
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
SHUFFLES = 200
SEED = 20260815

IS_GLYPH = re.compile(r"^\d")
NUMERIC = re.compile(r"^(\d+)")


def read_corpus():
    """Yield one list of (code, link) per inscribed line, per object."""
    out = []
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        obj = os.path.splitext(os.path.basename(path))[0]
        root = ET.parse(path).getroot()
        for line in root.iter("line"):
            seq = []
            for g in line.iter("glyph"):
                code = (g.findtext("code/ceipp") or "").strip()
                link = (g.findtext("link") or "").strip()
                seq.append((code, link))
            if seq:
                out.append((obj, seq))
    return out


def to_tokens(seq, mode):
    """Turn one line into runs of adjacent tokens, splitting at every break."""
    runs, cur = [], []
    pending_fuse = False
    for code, link in seq:
        if not IS_GLYPH.match(code):
            # empty, "_", or a lacuna estimate such as "(3-5)!" -- chain breaks
            if cur:
                runs.append(cur)
                cur = []
            pending_fuse = False
            continue

        stripped = code.replace("!", "")
        if mode == "full":
            tok = stripped
        else:
            m = NUMERIC.match(stripped)
            tok = m.group(1) if m else stripped

        if mode == "fused" and pending_fuse and cur:
            cur[-1] = cur[-1] + "+" + tok
        else:
            cur.append(tok)

        pending_fuse = (mode == "fused" and link == ".")
        if link in ("*", "…"):
            if cur:
                runs.append(cur)
                cur = []
            pending_fuse = False
    if cur:
        runs.append(cur)
    return runs


def entropy(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


def stats(runs):
    uni = Counter(t for r in runs for t in r)
    bi = Counter()
    for r in runs:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    L = len(uni)
    n = sum(uni.values())
    h1 = entropy(uni)
    hc = entropy(bi) - h1
    den = math.log2(L) if L > 1 else 1.0
    return {"L": L, "n": n, "runs": len(runs), "h1": h1, "hc": hc,
            "h1n": h1 / den, "hcn": hc / den,
            "bi_types": len(bi), "bi_tok": sum(bi.values()),
            "cov": len(bi) / (L * L) if L else 0.0,
            "hapax": sum(1 for c in uni.values() if c == 1) / L if L else 0.0}


def reshuffle(runs, rng):
    flat = [t for r in runs for t in r]
    rng.shuffle(flat)
    out, i = [], 0
    for r in runs:
        out.append(flat[i:i + len(r)])
        i += len(r)
    return out


def main():
    rng = random.Random(SEED)
    corpus = read_corpus()
    objects = len({o for o, _ in corpus})
    print(f"esineita: {objects}   rivielementteja: {len(corpus)}")

    rows = []
    for mode in ("full", "base", "fused"):
        runs = [r for _o, seq in corpus for r in to_tokens(seq, mode)]
        s = stats(runs)
        nulls = [stats(reshuffle(runs, rng))["hcn"] for _ in range(SHUFFLES)]
        m = sum(nulls) / len(nulls)
        sd = math.sqrt(sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1))
        s["null"] = m
        s["sd"] = sd
        s["sig"] = s["hcn"] - m
        rows.append((mode, s))

    print()
    print("=" * 78)
    print("OTOSKOKO")
    print("=" * 78)
    print(f"{'luenta':<8}{'jaksot':>9}{'tokenit':>10}{'tyypit':>9}"
          f"{'tok/tyyppi':>12}{'hapax%':>9}")
    for m, s in rows:
        print(f"{m:<8}{s['runs']:>9}{s['n']:>10}{s['L']:>9}"
              f"{s['n']/s['L']:>12.1f}{s['hapax']*100:>8.1f}%")

    print()
    print("=" * 78)
    print("BIGRAMMIPEITTO")
    print("=" * 78)
    print(f"{'luenta':<8}{'bi.tok':>9}{'bi.tyyp':>10}{'V^2':>11}{'peitto':>10}")
    for m, s in rows:
        print(f"{m:<8}{s['bi_tok']:>9}{s['bi_types']:>10}"
              f"{s['L']**2:>11}{s['cov']*100:>9.2f}%")

    print()
    print("=" * 78)
    print("NORMALISOITU (log kanta L) + SEKOITUSNOLLA")
    print("=" * 78)
    print(f"{'luenta':<8}{'H1n':>8}{'Hcn':>8}{'nolla':>8}{'signaali':>10}{'z':>9}")
    for m, s in rows:
        z = s["sig"] / s["sd"] if s["sd"] else float("nan")
        print(f"{m:<8}{s['h1n']:>8.3f}{s['hcn']:>8.3f}{s['null']:>8.3f}"
              f"{s['sig']:>10.3f}{z:>9.1f}")

    print()
    print("=" * 78)
    print("RATKAISU — 25 esinetta, riippumaton editio")
    print("=" * 78)
    hcn = [s["hcn"] for _m, s in rows]
    span = max(hcn) - min(hcn)
    sig = max(abs(s["sig"]) for _m, s in rows)
    print(f"  luennan aiheuttama hajonta   : {span:.3f}  = {span*100:.1f} % asteikosta")
    print(f"  suurin rakennesignaali       : {sig:.3f}")
    print(f"  suhde                        : {span/sig:.1f}x")


if __name__ == "__main__":
    main()
