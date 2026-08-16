"""Does conditional entropy have any resolving power on a corpus this small?

Two checks, both self-contained — neither needs a value quoted from the
literature:

  1. SHUFFLE NULL. Tokens are permuted within the corpus, which preserves the
     unigram distribution exactly and destroys all bigram structure. Whatever
     H_cond the null produces is what the estimator returns when there is
     nothing to find. If the real corpus does not sit far outside that null,
     the metric is not measuring structure here.

  2. LEARNING CURVE. H_cond recomputed on growing subsamples. A converged
     estimator flattens; one still climbing at 100% has not converged, so its
     value at 100% is an artefact of sample size rather than a property of the
     script.
"""
import json
import math
import os
import random
from collections import Counter

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "rongopy", "ga_lstm", "tablets")
ENCODINGS = [("barthel", "tablets.json"),
             ("clean", "tablets_clean.json"),
             ("simple", "tablets_simple.json")]
SHUFFLES = 200
SEED = 20260815


def load_lines(fn):
    d = json.load(open(os.path.join(BASE, fn), encoding="utf-8"))
    out = []
    for _obj, lines in d.items():
        for _lid, text in lines.items():
            toks = [t for t in str(text).split("-") if t]
            if toks:
                out.append(toks)
    return out


def entropy(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


def h_cond(lines):
    uni = Counter(t for line in lines for t in line)
    bi = Counter()
    for line in lines:
        for a, b in zip(line, line[1:]):
            bi[(a, b)] += 1
    return entropy(bi) - entropy(uni)


def reshuffle(lines, rng):
    """Permute all tokens, keeping the original line-length profile."""
    flat = [t for line in lines for t in line]
    rng.shuffle(flat)
    out, i = [], 0
    for line in lines:
        out.append(flat[i:i + len(line)])
        i += len(line)
    return out


def main():
    rng = random.Random(SEED)

    print("=" * 78)
    print("1) SEKOITUSNOLLA — H_cond kun rakennetta EI ole")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'oikea':>9}{'nolla ka.':>11}{'nolla sd':>10}"
          f"{'ero':>9}{'z':>9}")
    real_vs_null = {}
    for key, fn in ENCODINGS:
        lines = load_lines(fn)
        real = h_cond(lines)
        nulls = [h_cond(reshuffle(lines, rng)) for _ in range(SHUFFLES)]
        m = sum(nulls) / len(nulls)
        sd = math.sqrt(sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1))
        z = (real - m) / sd if sd else float("nan")
        real_vs_null[key] = (real, m, sd, real - m)
        print(f"{key:<10}{real:>9.3f}{m:>11.3f}{sd:>10.4f}"
              f"{real - m:>9.3f}{z:>9.1f}")

    print()
    print("=" * 78)
    print("2) OPPIMISKAYRA — onko estimaattori konvergoitunut 100%:ssa")
    print("=" * 78)
    fracs = [0.25, 0.50, 0.75, 1.00]
    header = "".join(f"{str(int(f * 100)) + '%':>10}" for f in fracs)
    print(f"{'enkoodaus':<10}{header}{'75->100':>10}")
    # Lines are stored object by object, so taking a prefix samples a handful of
    # tablets rather than the corpus; subsamples are drawn at random and averaged.
    draws = 40
    for key, fn in ENCODINGS:
        lines = load_lines(fn)
        vals = []
        for f in fracs:
            k = max(2, int(len(lines) * f))
            if k >= len(lines):
                vals.append(h_cond(lines))
                continue
            reps = [h_cond(rng.sample(lines, k)) for _ in range(draws)]
            vals.append(sum(reps) / len(reps))
        drift = vals[-1] - vals[-2]
        print(f"{key:<10}" + "".join(f"{v:>10.3f}" for v in vals)
              + f"{drift:>10.3f}")

    print()
    print("=" * 78)
    print("3) VERTAILU — rakenteen signaali vs transkription aiheuttama hajonta")
    print("=" * 78)
    signals = [real_vs_null[k][3] for k, _ in ENCODINGS]
    reals = [real_vs_null[k][0] for k, _ in ENCODINGS]
    span = max(reals) - min(reals)
    print(f"  suurin todellinen rakennesignaali (oikea - nolla): "
          f"{max(signals):.3f} bittia")
    print(f"  pienin todellinen rakennesignaali                : "
          f"{min(signals):.3f} bittia")
    print(f"  H_cond:n hajonta pelkasta transkriptiosta        : "
          f"{span:.3f} bittia")
    if span > max(signals):
        print()
        print("  => transkription valinta siirtaa mittaria ENEMMAN kuin")
        print("     mitattava rakenne itse.")


if __name__ == "__main__":
    main()
