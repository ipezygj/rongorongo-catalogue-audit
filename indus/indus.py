"""The catalogue as instrument, second script: Indus.

Data (data/, fetched from github.com/Hamilchin/indus-cipherable, which digitised
Mahadevan 1977 and the EBUDS set of Yadav/Vahia/Rao):
  indus_script_IM77_concordance.txt  Mahadevan 1977 concordance: text id + signs;
                                     '*NNN' = uncertain reading, '000' = lost sign
  data_EBUDS_UNIQUE.txt              EBUDS, 1 548 unique texts (Rao et al. 2009's
                                     data), signs from column 10; '0' = lost
Readings:
  m77_var   Mahadevan numbers, uncertain readings kept as their own types
  m77_base  '*' stripped (Mahadevan's 417-sign catalogue)
  ebuds     Rao's set, Mahadevan numbers
Lost signs and text/line boundaries break the chain, as lacunae did for rongorongo.

Same instrument as ../: log-base-L conditional entropy, unigram-matched
shuffle null, bigram coverage; catalogue-size sweep with Mahadevan-adjacent
(his numbering follows shape), frequency and random merges; syllabary references
(Rapa Nui, Maori, Linear B) at Indus token count and run lengths; repetition
fingerprint.
"""
import math, os, random, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.chdir(os.path.dirname(HERE))  # so ../ref and ../ceipp paths resolve
from horley import stats, reshuffle
from sweep import bin_map, apply, measure
import syllabary_ref as S
from robustness import recut, ms
from fingerprint import rates

rng = random.Random(20260816)
SIZES = [25, 50, 75, 100, 150, 200, 300, 417]


def read_m77(keep_star):
    runs = []
    for line in open(os.path.join(HERE, "data", "indus_script_IM77_concordance.txt"), encoding="utf-8", errors="replace"):
        cols = [c.strip() for c in line.rstrip("\n").split("\t")]
        if not cols or cols[0] == "IM77":
            continue
        cur = []
        for c in cols[1:]:
            if not c:
                continue
            if c == "000":
                if cur:
                    runs.append(cur)
                    cur = []
                continue
            tok = c if keep_star else c.lstrip("*")
            cur.append(tok.zfill(3) if tok.isdigit() else tok)
        if cur:
            runs.append(cur)
    return runs


def read_ebuds():
    runs = []
    for line in open(os.path.join(HERE, "data", "data_EBUDS_UNIQUE.txt"), encoding="utf-8", errors="replace"):
        cols = [c.strip() for c in line.rstrip("\n").split("\t")]
        if len(cols) < 10:
            continue
        cur = []
        for c in cols[9:]:
            if not c:
                continue
            if c == "0":
                if cur:
                    runs.append(cur)
                    cur = []
                continue
            cur.append(c.zfill(3))
        if cur:
            runs.append(cur)
    return runs


def num_key(t):
    d = "".join(ch for ch in t if ch.isdigit())
    return (int(d) if d else 10 ** 9, t)


def main():
    out = []
    p = out.append
    R = {"m77_var": read_m77(True), "m77_base": read_m77(False), "ebuds": read_ebuds()}
    p("=" * 96)
    p("INDUS: LUENNAT (log kanta L; signaali = Hcn - sekoitus; peitto)")
    p("=" * 96)
    p("%-9s %6s %6s %5s %7s %7s %8s %8s %8s" % ("luenta", "runs", "tokens", "L", "meanrun", "cov", "Hcn", "sig", "z"))
    M = {}
    for k, runs in R.items():
        m = measure(runs, rng, 200)
        M[k] = m
        p("%-9s %6d %6d %5d %7.2f %6.2f%% %8.3f %+8.3f %8.1f" % (k, len(runs), m["n"], m["L"], m["n"] / len(runs), m["cov"] * 100, m["hcn"], m["sig"], m["z"]))
    span = M["m77_var"]["hcn"] - M["m77_base"]["hcn"]
    p("  m77_var vs m77_base (uncertain readings as own types or not): dHcn %+.3f ; signaali %.3f ; suhde %.1fx"
      % (span, abs(M["m77_base"]["sig"]), abs(span) / abs(M["m77_base"]["sig"])))
    p("  Rao 2009 -tarkistus (EBUDS, log kanta 417): Hcn %.3f" % M["ebuds"]["hcn"])

    base = R["m77_base"]
    types = sorted(Counter(t for r in base for t in r), key=num_key)
    freq = [t for t, _ in Counter(t for r in base for t in r).most_common()]
    p("")
    p("=" * 96)
    p("KATALOGIKOKO-SWEEP (m77_base): sig / cov   numeric = Mahadevan-numerojarjestys (muoto), freq, random(20)")
    p("=" * 96)
    p("%-5s | %-16s | %-16s | %-16s" % ("L", "numeric", "freq", "random"))
    for L in SIZES:
        L = min(L, len(types))
        mn = measure(apply(base, bin_map(types, L)), rng, 100)
        keep = set(freq[:L - 1])
        mf = measure(apply(base, {t: (t if t in keep else "OTHER") for t in types}), rng, 100)
        rs = []
        for _ in range(20):
            perm = types[:]
            rng.shuffle(perm)
            rs.append(measure(apply(base, bin_map(perm, L)), rng, 30))
        ra = {k: sum(x[k] for x in rs) / len(rs) for k in ("sig", "cov")}
        rsd = math.sqrt(sum((x["sig"] - ra["sig"]) ** 2 for x in rs) / 19)
        p("%-5d | %+.3f  %5.1f%%   | %+.3f  %5.1f%%   | %+.3f  %5.1f%% (sd %.3f)  numeric-random: %+.1f sd, freq-random: %+.1f sd"
          % (L, mn["sig"], mn["cov"] * 100, mf["sig"], mf["cov"] * 100, ra["sig"], ra["cov"] * 100, rsd,
             (mn["sig"] - ra["sig"]) / rsd, (mf["sig"] - ra["sig"]) / rsd))
        if L == len(types):
            break

    # references at Indus N and run lengths
    n_ind = M["m77_base"]["n"]
    lens = [len(r) for r in base]
    rap_txt, _ = S.load_rap()
    RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
    refs = {"Rapa Nui (55)": S.syllabify(rap_txt, RAP_C, True),
            "Maori (52)": S.syllabify(S.load_mri(), ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"], True),
            "Linear B (95)": S.load_linb()}
    p("")
    p("=" * 96)
    p("REFERENSSIT INDUKSEN N=%d JA JAKSOPITUUKSILLA (ka %.2f); Indus yhdistettyna samaan L:aan" % (n_ind, n_ind / len(base)))
    p("=" * 96)
    for name, runs in refs.items():
        xs = [measure(recut(S.sample_runs(runs, n_ind, rng), lens, rng), rng, 30) for _ in range(15)]
        Lr = int(round(ms([x["L"] for x in xs])[0]))
        p("%-14s L~%-3d Hcn %.3f  sig %+.3f+-%.3f  z %6.1f  cov %4.1f%%" % (name, Lr, ms([x["hcn"] for x in xs])[0], *ms([x["sig"] for x in xs]), ms([x["z"] for x in xs])[0], ms([x["cov"] for x in xs])[0] * 100))
        Lm = min(Lr, len(types))
        mn = measure(apply(base, bin_map(types, Lm)), rng, 60)
        keep = set(freq[:Lm - 1])
        mf = measure(apply(base, {t: (t if t in keep else "OTHER") for t in types}), rng, 60)
        p("%-14s Indus @L=%-3d numeric sig %+.3f cov %.1f%% | freq sig %+.3f cov %.1f%%  -> ratio ref/best %.1fx"
          % ("", Lm, mn["sig"], mn["cov"] * 100, mf["sig"], mf["cov"] * 100, ms([x["sig"] for x in xs])[0] / min(mn["sig"], mf["sig"])))

    p("")
    p("=" * 96)
    p("TOISTOPROFIILI % tokeneista (suluissa oma sekoitus)")
    p("=" * 96)
    for k, runs in R.items():
        real = rates(runs)
        nulls = [rates(reshuffle(runs, rng)) for _ in range(20)]
        null = {kk: sum(x[kk] for x in nulls) / 20 for kk in real}
        p("%-9s " % k + "".join(" %s %.2f (%.2f) " % (kk, real[kk], null[kk]) for kk in ("AA", "AAA", "ABA", "ABAB")))
    for name, runs in refs.items():
        rs_, ns_ = [], []
        for _ in range(10):
            w = recut(S.sample_runs(runs, n_ind, rng), lens, rng)
            rs_.append(rates(w))
            ns_.append(rates(reshuffle(w, rng)))
        real = {kk: sum(x[kk] for x in rs_) / 10 for kk in rs_[0]}
        null = {kk: sum(x[kk] for x in ns_) / 10 for kk in ns_[0]}
        p("%-9s " % name[:9] + "".join(" %s %.2f (%.2f) " % (kk, real[kk], null[kk]) for kk in ("AA", "AAA", "ABA", "ABAB")))
    txt = "\n".join(out)
    print(txt)
    open(os.path.join(HERE, "indus_results.txt"), "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
