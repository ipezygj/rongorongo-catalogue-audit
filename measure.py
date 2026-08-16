"""Measure how far the standard 'is it language?' metrics move when only the
transcription changes.

rongopy ships three encodings of the SAME 13 rongorongo objects:

    tablets.json         Barthel codes, ligature dots and variant letters intact
    tablets_clean.json   variants and ligature marks stripped
    tablets_simple.json  Horley-style reduction to ~130 basic glyphs

The physical inscriptions are identical across all three, so any movement in the
metrics is attributable to the transcription alone. Sample size is reported
before any metric, because bigram entropy on a corpus this small is estimated
from a nearly empty table and a plug-in number would otherwise read as solid.
"""
import json
import math
import os
from collections import Counter

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "rongopy", "ga_lstm", "tablets")

ENCODINGS = [
    ("barthel", "tablets.json", "Barthel: ligatuurit ja variantit tallella"),
    ("clean", "tablets_clean.json", "variantit ja ligatuurimerkit riisuttu"),
    ("simple", "tablets_simple.json", "Horley-tyylinen pelkistys"),
]


def load_lines(filename):
    """Return one token list per inscribed line, preserving line boundaries.

    Bigrams must not run across a line break, so lines are kept separate rather
    than concatenated into one stream.
    """
    d = json.load(open(os.path.join(BASE, filename), encoding="utf-8"))
    lines = []
    for _obj, obj_lines in d.items():
        for _line_id, text in obj_lines.items():
            toks = [t for t in str(text).split("-") if t]
            if toks:
                lines.append(toks)
    return lines


def entropy(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


def zipf_slope(freqs):
    """Least-squares slope of log(freq) on log(rank)."""
    ys = [math.log10(f) for f in sorted(freqs, reverse=True)]
    xs = [math.log10(i + 1) for i in range(len(ys))]
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else float("nan")


def analyse(lines):
    tokens = [t for line in lines for t in line]
    uni = Counter(tokens)
    bi = Counter()
    for line in lines:
        for a, b in zip(line, line[1:]):
            bi[(a, b)] += 1

    n, v = len(tokens), len(uni)
    h1, h2 = entropy(uni), entropy(bi)
    hapax = sum(1 for c in uni.values() if c == 1)

    return {
        "objects": None,
        "lines": len(lines),
        "tokens": n,
        "types": v,
        "hapax": hapax,
        "hapax_rate": hapax / v if v else 0.0,
        "tokens_per_type": n / v if v else 0.0,
        "H1": h1,
        "H2": h2,
        "H_cond": h2 - h1,
        "bigram_tokens": sum(bi.values()),
        "bigram_types": len(bi),
        # What fraction of the V^2 bigram table was observed even once.
        "bigram_coverage": len(bi) / (v * v) if v else 0.0,
        "zipf": zipf_slope(list(uni.values())),
    }


def main():
    rows = []
    for key, fn, note in ENCODINGS:
        lines = load_lines(fn)
        objects = len(json.load(open(os.path.join(BASE, fn), encoding="utf-8")))
        r = analyse(lines)
        r["objects"] = objects
        rows.append((key, note, r))

    print("=" * 78)
    print("OTOSKOKO ENSIN")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'esineet':>9}{'rivit':>8}{'tokenit':>10}"
          f"{'tyypit':>9}{'tok/tyyppi':>12}")
    for key, _note, r in rows:
        print(f"{key:<10}{r['objects']:>9}{r['lines']:>8}{r['tokens']:>10}"
              f"{r['types']:>9}{r['tokens_per_type']:>12.1f}")

    print()
    print("=" * 78)
    print("BIGRAMMITAULUKON TAYTTOASTE  (H_cond lasketaan tasta)")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'bigr.tok':>10}{'bigr.tyyp':>11}"
          f"{'V^2':>10}{'peitto':>10}")
    for key, _note, r in rows:
        v2 = r["types"] ** 2
        print(f"{key:<10}{r['bigram_tokens']:>10}{r['bigram_types']:>11}"
              f"{v2:>10}{r['bigram_coverage']*100:>9.2f}%")

    print()
    print("=" * 78)
    print("METRIIKAT — sama kivi, eri transkriptio")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'H1':>8}{'H_cond':>9}{'hapax%':>9}{'Zipf':>8}   selite")
    for key, note, r in rows:
        print(f"{key:<10}{r['H1']:>8.3f}{r['H_cond']:>9.3f}"
              f"{r['hapax_rate']*100:>8.1f}%{r['zipf']:>8.2f}   {note}")

    print()
    print("=" * 78)
    print("HAJONTA PELKASTA TRANSKRIPTIOSTA")
    print("=" * 78)
    for field, label in (("H1", "H1 (bittia)"), ("H_cond", "H_cond (bittia)"),
                         ("hapax_rate", "hapax-osuus"), ("zipf", "Zipf-kulma"),
                         ("types", "merkkivalikoima")):
        vals = [r[field] for _k, _n, r in rows]
        lo, hi = min(vals), max(vals)
        span = hi - lo
        if field == "hapax_rate":
            print(f"  {label:<20} {lo*100:.1f}% .. {hi*100:.1f}%"
                  f"   vaihteluvali {span*100:.1f} pistetta")
        elif field == "types":
            print(f"  {label:<20} {lo} .. {hi}"
                  f"   suhde {hi/lo:.2f}x")
        else:
            print(f"  {label:<20} {lo:.3f} .. {hi:.3f}"
                  f"   vaihteluvali {span:.3f}")


if __name__ == "__main__":
    main()
