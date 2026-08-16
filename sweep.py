"""Catalogue-size sweep: what does a catalogue of L signs let you see?

Korovina (16 Aug 2026) asked which catalogue size gives "the best result", and
predicted that shrinking to ~50 (the Rapa Nui syllable count) must make the
corpus look syllabic whatever it is. "Best" is defined here as it was in the
15 Aug proposal, before the run:

  (a) distance of the corpus from its own unigram-matched shuffle, on the
      log-base-L scale (signal = Hcond_n(real) - Hcond_n(null), and z);
  (b) bigram coverage at that size (fraction of the L*L table observed),
      i.e. whether the number is estimable at all.

Sizes run 25 .. 633 with the SAME merge rule throughout, so nothing but the
size changes. Rules (each starts from the 633 numeric Barthel codes of the
CEIPP corpus; "horley" starts from Horley's 125 published classes):

  numeric   sort codes by Barthel number, cut into L contiguous groups of
            equal type-count. Barthel's numbering follows shape, so this is
            the cheapest shape-based catalogue of size L.
  horley    Horley's 125 classes, merged numerically further below 125
            (above 125 the published catalogue is used as is; L capped).
  freq      keep the L-1 most frequent codes, merge everything else into
            one class. What a "just drop the rare stuff" catalogue does.
  random    L classes of equal type-count drawn at random (20 draws,
            mean +- sd). What a catalogue of size L with NO information
            in its composition does. Everything above this line is what
            composition adds; the line itself is what size adds.
"""
import math
import random
import sys
from collections import Counter

sys.path.insert(0, ".")
from horley import (read_lines, tokens_plain, tokens_horley, stats,
                    reshuffle)

SIZES = [25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 400, 500, 633]
SHUFFLES = 100
RANDOM_DRAWS = 20
SEED = 20260816


def num_key(code):
    d = ""
    for ch in code:
        if ch.isdigit():
            d += ch
        else:
            break
    return (int(d) if d else 10**9, code)


def bin_map(types_sorted, L):
    """Cut an ordered list of types into L contiguous classes of ~equal size."""
    n = len(types_sorted)
    if L >= n:
        return {t: t for t in types_sorted}
    m = {}
    for i, t in enumerate(types_sorted):
        m[t] = "c%d" % (i * L // n)
    return m


def apply(runs, m):
    return [[m[t] for t in r] for r in runs]


def measure(runs, rng, shuffles=SHUFFLES):
    s = stats(runs)
    nulls = [stats(reshuffle(runs, rng))["hcn"] for _ in range(shuffles)]
    mu = sum(nulls) / len(nulls)
    sd = math.sqrt(sum((x - mu) ** 2 for x in nulls) / (len(nulls) - 1))
    s["null"], s["sd"], s["sig"] = mu, sd, s["hcn"] - mu
    s["z"] = s["sig"] / sd if sd else float("nan")
    return s


def main():
    rng = random.Random(SEED)
    lines = read_lines()
    base = [r for seq in lines for r in tokens_plain(seq, True)]
    horl = [r for seq in lines for r in tokens_horley(seq)]
    base_types = sorted(Counter(t for r in base for t in r), key=num_key)
    horl_types = sorted(Counter(t for r in horl for t in r), key=num_key)
    base_freq = [t for t, _ in Counter(t for r in base for t in r).most_common()]
    print("base types %d, horley types %d" % (len(base_types), len(horl_types)))

    rows = []
    for L in SIZES:
        row = {"L": L}
        # numeric
        row["numeric"] = measure(apply(base, bin_map(base_types, L)), rng)
        # horley (numeric merge below 125)
        if L <= len(horl_types):
            row["horley"] = measure(apply(horl, bin_map(horl_types, L)), rng)
        # freq
        keep = set(base_freq[:L - 1])
        m = {t: (t if t in keep else "OTHER") for t in base_types}
        row["freq"] = measure(apply(base, m), rng)
        # random
        draws = []
        for _ in range(RANDOM_DRAWS):
            perm = base_types[:]
            rng.shuffle(perm)
            draws.append(measure(apply(base, bin_map(perm, L)), rng,
                                 shuffles=30))
        def agg(k):
            xs = [d[k] for d in draws]
            mu = sum(xs) / len(xs)
            sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1))
            return mu, sd
        row["random"] = {k: agg(k) for k in ("hcn", "sig", "z", "cov")}
        rows.append(row)
        print("L=%d done" % L, flush=True)

    out = []
    p = out.append
    p("=" * 96)
    p("KATALOGIKOKO-SWEEP  (log kanta L, [0,1]; signaali = Hcn(oikea) - Hcn(sekoitus); z; bigram-peitto)")
    p("=" * 96)
    p("%-5s | %-26s | %-26s | %-26s | %-28s" % ("L", "numeric", "horley", "freq", "random (ka +- sd)"))
    p("%-5s | %-26s | %-26s | %-26s | %-28s" % ("", "Hcn   sig    z    cov", "Hcn   sig    z    cov", "Hcn   sig    z    cov", "Hcn    sig     z     cov"))
    def cell(s):
        return "%.3f %+.3f %6.1f %5.1f%%" % (s["hcn"], s["sig"], s["z"], s["cov"] * 100)
    for row in rows:
        r = row["random"]
        rc = "%.3f %+.3f %5.1f %5.1f%% (sd sig %.3f)" % (r["hcn"][0], r["sig"][0], r["z"][0], r["cov"][0] * 100, r["sig"][1])
        p("%-5d | %s | %s | %s | %s" % (row["L"], cell(row["numeric"]),
            cell(row["horley"]) if "horley" in row else " " * 26, cell(row["freq"]), rc))
    p("")
    p("=" * 96)
    p("KOOSTUMUKSEN LISA = signaali(saanto) - signaali(random) samalla L, yksikkona random-hajontaa")
    p("=" * 96)
    p("%-5s %10s %10s %10s" % ("L", "numeric", "horley", "freq"))
    for row in rows:
        r = row["random"]
        def d(k):
            if k not in row: return "        -"
            sd = r["sig"][1] or 1e-9
            return "%+9.1f" % ((row[k]["sig"] - r["sig"][0]) / sd)
        p("%-5d %10s %10s %10s" % (row["L"], d("numeric"), d("horley"), d("freq")))
    p("")
    # knee: where |sig| is maximal per rule
    p("=" * 96)
    p("MISSA |signaali| ON SUURIN (\"paras\" maaritelman (a) mukaan) ja missa peitto ylittaa 10 %/25 % (b)")
    p("=" * 96)
    for k in ("numeric", "horley", "freq"):
        rs = [row for row in rows if k in row]
        best = max(rs, key=lambda row: abs(row[k]["sig"]))
        bz = max(rs, key=lambda row: abs(row[k]["z"]))
        c10 = [row["L"] for row in rs if row[k]["cov"] >= 0.10]
        c25 = [row["L"] for row in rs if row[k]["cov"] >= 0.25]
        p("  %-8s max|sig| at L=%-4d (%.3f)   max|z| at L=%-4d (%.1f)   cov>=10%%: L<=%s   cov>=25%%: L<=%s"
          % (k, best["L"], best[k]["sig"], bz["L"], bz[k]["z"],
             max(c10) if c10 else "-", max(c25) if c25 else "-"))
    rs = rows
    best = max(rs, key=lambda row: abs(row["random"]["sig"][0]))
    p("  %-8s max|sig| at L=%-4d (%.3f)" % ("random", best["L"], best["random"]["sig"][0]))
    txt = "\n".join(out)
    print(txt)
    open("sweep_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
