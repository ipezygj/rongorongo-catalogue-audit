"""Mapping-free fingerprints: repetition profile.

For any mapping glyph->syllable, an immediate repeat AA in the syllable stream
is an immediate repeat in the glyph stream (and vice versa under 1:1), and
ABAB likewise. So the repetition profile of the corpus is inherited by any
syllabic reading regardless of the key. Rapa Nui has heavy reduplication
(kokore, haka-, rangirangi, tapume): a syllabary of it must show it.

Rates per token, N-matched windows, run lengths matched to rongorongo:
  AA    x_i == x_{i+1}
  ABA   x_i == x_{i+2} != x_{i+1}
  ABAB  x_i == x_{i+2} and x_{i+1} == x_{i+3}, x_i != x_{i+1}
  AAA   three in a row
against each text's own unigram-matched shuffle (expected repetition from
frequency alone).
"""
import math, random, sys
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_horley, tokens_plain, reshuffle
import syllabary_ref as S
from robustness import recut, ms

rng = random.Random(20260816)
DRAWS = 15


def rates(runs):
    n = aa = aba = abab = aaa = 0
    for r in runs:
        n += len(r)
        for i in range(len(r) - 1):
            if r[i] == r[i + 1]:
                aa += 1
                if i + 2 < len(r) and r[i + 2] == r[i]:
                    aaa += 1
        for i in range(len(r) - 2):
            if r[i] == r[i + 2] and r[i] != r[i + 1]:
                aba += 1
                if i + 3 < len(r) and r[i + 1] == r[i + 3]:
                    abab += 1
    return {"AA": aa / n * 100, "ABA": aba / n * 100, "ABAB": abab / n * 100, "AAA": aaa / n * 100}


def main():
    out = []
    p = out.append
    lines = read_lines()
    horl = [r for s in lines for r in tokens_horley(s)]
    base = [r for s in lines for r in tokens_plain(s, True)]
    rr_lengths = [len(r) for r in base]
    n_rr = sum(rr_lengths)
    rap_txt, _ = S.load_rap()
    RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
    refs = {
        "Rapa Nui syllables (55)": S.syllabify(rap_txt, RAP_C, True),
        "Maori syllables (52)": S.syllabify(S.load_mri(), ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"], True),
        "Linear B (95)": S.load_linb(),
    }
    p("=" * 96)
    p("TOISTOPROFIILI, % tokeneista (N=14812, jaksopituudet rr:n mukaan; suluissa oma unigrammisekoitus)")
    p("=" * 96)
    p("%-28s %14s %14s %14s %14s" % ("teksti", "AA", "AAA", "ABA", "ABAB"))

    def line(name, real, null):
        p("%-28s" % name + "".join(" %5.2f (%5.2f)  " % (real[k], null[k]) for k in ("AA", "AAA", "ABA", "ABAB")))

    for name, runs in (("rongorongo Horley 125", horl), ("rongorongo numeric 633", base)):
        real = rates(runs)
        nulls = [rates(reshuffle(runs, rng)) for _ in range(DRAWS)]
        null = {k: sum(x[k] for x in nulls) / DRAWS for k in real}
        line(name, real, null)
    for name, runs in refs.items():
        rs, ns = [], []
        for _ in range(DRAWS):
            w = recut(S.sample_runs(runs, n_rr, rng), rr_lengths, rng)
            rs.append(rates(w))
            ns.append(rates(reshuffle(w, rng)))
        real = {k: sum(x[k] for x in rs) / DRAWS for k in rs[0]}
        null = {k: sum(x[k] for x in ns) / DRAWS for k in ns[0]}
        line(name, real, null)
    # which rongorongo glyphs carry the AA repeats
    c = Counter()
    for r in horl:
        for i in range(len(r) - 1):
            if r[i] == r[i + 1]:
                c[r[i]] += 1
    tot = sum(c.values())
    p("")
    p("rongorongo AA-toistot glyfeittain (Horley), yht %d: %s" % (tot, ", ".join("%s:%d" % kv for kv in c.most_common(12))))
    p("  osuus 5 yleisimman varassa: %.0f%%" % (sum(v for _k, v in c.most_common(5)) / tot * 100))
    # same for Rapa Nui: which syllables repeat
    c2 = Counter()
    for r in refs["Rapa Nui syllables (55)"]:
        for i in range(len(r) - 1):
            if r[i] == r[i + 1]:
                c2[r[i]] += 1
    t2 = sum(c2.values())
    p("Rapa Nui AA-toistot tavuittain, yht %d (koko teksti): %s" % (t2, ", ".join("%s:%d" % kv for kv in c2.most_common(12))))
    p("  osuus 5 yleisimman varassa: %.0f%%" % (sum(v for _k, v in c2.most_common(5)) / t2 * 100))
    txt = "\n".join(out)
    print(txt)
    open("fingerprint_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
