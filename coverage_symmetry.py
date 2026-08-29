"""Bigram coverage for rongorongo and Indus on ONE grid, ONE merge rule.

Sproat (p.c., 23 Aug 2026) made two points. The second - that Indus also has
several proposed sign sets - is answered in indus_published_range.py: over the
reachable published range the statistic moves 1.5%. The FIRST point is sharper
and is what this measures: Indus texts are short and the data are sparse.

Section 5 of the paper already uses bigram coverage as the criterion that fixes
rongorongo's usable catalogue range (coverage collapses beyond about 100-125
signs). Section 9 then calls the instrument "safe" on Indus without applying
that same criterion to Indus. That is an asymmetric comparison, and this script
removes the asymmetry by measuring both scripts the same way.

HELD THE SAME - stated before the numbers were read:
  statistic     distinct bigram types / L*L, the definition in horley.stats
  merge rule    frequency fold: keep the L-1 commonest signs, rest -> OTHER.
                This is exactly indus_published_range.fold_freq and exactly
                the "freq" column of sweep.py. No other rule is used here.
  grid          the same L values for both corpora
  segmentation  each corpus keeps its own text/run boundaries; bigrams are
                never formed across a boundary

NOT the same, and reported rather than adjusted:
  N             rongorongo 14 812 coded glyphs, Indus 13 372 signs (-10%)
  bigram tokens differ more than N does, because Indus texts are short: every
                text boundary costs one bigram. This is Sproat's point, so the
                ceiling N_bigrams/L*L is printed next to every coverage figure.
                Coverage cannot exceed it however rich the script is.
"""
import io
import os
import sys
from collections import Counter

sys.path.insert(0, ".")
sys.path.insert(0, "indus")
from horley import read_lines, tokens_plain                       # noqa: E402

GRID = [50, 75, 100, 125, 150, 200, 250, 300, 350, 386, 400, 417, 500, 633]

# Julkaistut katalogit, kummallekin kirjoitukselle.
MERKINNAT = {
    "rongorongo": {125: "Horley, the field's own catalogue",
                   633: "numeric Barthel, full inventory"},
    "Indus": {386: "Parpola", 417: "Mahadevan, full inventory",
              702: "Wells / ICIT (not reachable by merging down)"},
}


def fold_freq(runs, L):
    """Keep the L-1 commonest signs, everything else into one class."""
    c = Counter(t for r in runs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in runs]


def peitto(runs, L):
    """Coverage and its ceiling at catalogue size L."""
    folded = fold_freq(runs, L)
    uni = Counter(t for r in folded for t in r)
    bi = Counter()
    for r in folded:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    toteutunut_L = len(uni)
    solut = toteutunut_L * toteutunut_L
    return {
        "L": toteutunut_L,
        "tokeneita": sum(uni.values()),
        "bi_tokeneita": sum(bi.values()),
        "bi_tyyppeja": len(bi),
        "peitto": len(bi) / solut if solut else 0.0,
        "katto": min(1.0, sum(bi.values()) / solut) if solut else 0.0,
    }


def lataa_rongorongo():
    lines = read_lines()
    return [r for seq in lines for r in tokens_plain(seq, True)]


def lataa_indus():
    src = io.open(os.path.join("indus", "indus.py"), encoding="utf-8").read()
    src = src.replace('if __name__ == "__main__":\n    main()', "")
    ns = {"__name__": "indusmod",
          "__file__": os.path.abspath(os.path.join("indus", "indus.py"))}
    exec(src, ns)
    return ns["read_m77"](False)


def taulukko(nimi, runs, ulos):
    p = ulos.append
    kaikki = Counter(t for r in runs for t in r)
    p("")
    p("%s: %d runs, %d tokens, %d sign types"
      % (nimi, len(runs), sum(kaikki.values()), len(kaikki)))
    p("%-6s %10s %10s %9s %9s   %s"
      % ("L", "bi.tokens", "bi.types", "coverage", "ceiling", "published"))
    rivit = {}
    for L in GRID:
        if L > len(kaikki):
            continue
        r = peitto(runs, L)
        rivit[L] = r
        p("%-6d %10d %10d %8.2f%% %8.2f%%   %s"
          % (L, r["bi_tokeneita"], r["bi_tyyppeja"], 100 * r["peitto"],
             100 * r["katto"], MERKINNAT.get(nimi, {}).get(L, "")))
    return rivit


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ulos = []
    p = ulos.append
    p("=" * 78)
    p("BIGRAM COVERAGE, ONE GRID, ONE RULE (frequency fold)")
    p("=" * 78)
    p(__doc__.strip().split("HELD THE SAME")[0].strip())

    rr = taulukko("rongorongo", lataa_rongorongo(), ulos)
    ind = taulukko("Indus", lataa_indus(), ulos)

    p("")
    p("MATCHED L: Indus coverage as a fraction of rongorongo's")
    p("%-6s %11s %11s %9s" % ("L", "rongorongo", "Indus", "ratio"))
    for L in GRID:
        if L in rr and L in ind:
            a, b = rr[L]["peitto"], ind[L]["peitto"]
            p("%-6d %10.2f%% %10.2f%% %8.2f" % (L, 100 * a, 100 * b,
                                                b / a if a else float("nan")))

    # Section 5's own thresholds, applied to both.
    p("")
    p("SECTION 5's OWN CRITERION APPLIED TO BOTH")
    for raja in (0.25, 0.10):
        for nimi, rivit in (("rongorongo", rr), ("Indus", ind)):
            kelpaa = [L for L in sorted(rivit) if rivit[L]["peitto"] >= raja]
            p("  coverage >= %2d%%: %-11s L <= %s"
              % (100 * raja, nimi, max(kelpaa) if kelpaa else "none on grid"))

    teksti = "\n".join(ulos)
    print(teksti)
    io.open("coverage_symmetry_results.txt", "w",
            encoding="utf-8", newline="\n").write(teksti + "\n")


if __name__ == "__main__":
    main()
