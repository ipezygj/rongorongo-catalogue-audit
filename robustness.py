"""Two referee checks on the syllabary comparison (syllabary_ref.py).

A. RUN-LENGTH MATCHING. The rongorongo chain is cut by lacunae, line ends and
   unreadable glyphs into 1 182 runs (mean ~12.5 tokens). The references were
   cut at verse/inscription boundaries and are longer. Both signal and coverage
   depend on how the stream is chopped, so here each reference window is
   re-cut into runs with EXACTLY the rongorongo run-length multiset (order
   shuffled) before measuring. Everything else as before: same L (rongorongo
   merged to the reference's L), same N (14 812).

B. SAMPLE-SIZE SCALING. Is the gap stable in N, or would more tablets close it?
   Rongorongo (horley merged to L=55 and L=95, and the published 125) and each
   reference measured at N = 25 / 50 / 75 / 100 % of the rongorongo token
   count, run-length matched at each N. Random contiguous sub-windows, 15
   draws each.
"""
import math, random, sys
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_plain, tokens_horley, stats, reshuffle
from sweep import bin_map, apply, num_key, measure
import syllabary_ref as S

SEED = 20260816
rng = random.Random(SEED)
DRAWS = 15


def recut(runs, lengths, rng):
    """Concatenate runs (order kept) and re-cut into the given run lengths."""
    flat = [t for r in runs for t in r]
    lens = lengths[:]
    rng.shuffle(lens)
    out, i = [], 0
    for L_ in lens:
        if i >= len(flat):
            break
        out.append(flat[i:i + L_])
        i += L_
    return out


def window(runs, n_tok, rng):
    return S.sample_runs(runs, n_tok, rng)


def sub_runs(runs, frac, rng):
    """Random contiguous block of runs holding ~frac of the tokens."""
    total = sum(len(r) for r in runs)
    want = int(total * frac)
    if want >= total:
        return runs
    start = rng.randrange(len(runs))
    out, k, i = [], 0, start
    while k < want:
        r = runs[i % len(runs)]
        out.append(r)
        k += len(r)
        i += 1
    return out


def ms(xs):
    mu = sum(xs) / len(xs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
    return mu, sd


def main():
    out = []
    p = out.append
    lines = read_lines()
    base = [r for s in lines for r in tokens_plain(s, True)]
    horl = [r for s in lines for r in tokens_horley(s)]
    rr_lengths = [len(r) for r in base]
    n_rr = sum(rr_lengths)
    p("rongorongo (base): %d runs, %d tokens, mean run %.1f, median %d, max %d"
      % (len(rr_lengths), n_rr, n_rr / len(rr_lengths), sorted(rr_lengths)[len(rr_lengths) // 2], max(rr_lengths)))

    rap_txt, _ = S.load_rap()
    mri_txt = S.load_mri()
    RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
    MRI_C = ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"]
    refs = {
        "rap_fold": S.syllabify(rap_txt, RAP_C, True),
        "mri_fold": S.syllabify(mri_txt, MRI_C, True),
        "linb": S.load_linb(),
        "rap_long": S.syllabify(rap_txt, RAP_C, False),
    }
    for k, v in refs.items():
        ls = [len(r) for r in v]
        p("  %-9s %d runs, mean run %.1f, median %d" % (k, len(ls), sum(ls) / len(ls), sorted(ls)[len(ls) // 2]))

    # ---------- A. run-length matched ----------
    p("")
    p("=" * 96)
    p("A. REFERENSSIT LEIKATTUNA RONGORONGON JAKSOPITUUKSIIN (N=14812, 15 ikkunaa)   Hcn  sig  z  cov")
    p("=" * 96)
    horl_types = sorted(Counter(t for r in horl for t in r), key=num_key)
    base_types = sorted(Counter(t for r in base for t in r), key=num_key)
    base_freq = [t for t, _ in Counter(t for r in base for t in r).most_common()]
    resA = {}
    for name, runs in refs.items():
        plain, cut = [], []
        for _ in range(DRAWS):
            w = window(runs, n_rr, rng)
            plain.append(measure(w, rng, 20))
            cut.append(measure(recut(w, rr_lengths, rng), rng, 20))
        Lref = int(round(ms([m["L"] for m in cut])[0]))
        resA[name] = (plain, cut, Lref)
        p("%-9s L~%-3d verse-cut : Hcn %.3f  sig %+.3f+-%.3f  z %6.1f  cov %4.1f%%"
          % (name, Lref, ms([m["hcn"] for m in plain])[0], *ms([m["sig"] for m in plain]),
             ms([m["z"] for m in plain])[0], ms([m["cov"] for m in plain])[0] * 100))
        p("%-9s        rr-cut    : Hcn %.3f  sig %+.3f+-%.3f  z %6.1f  cov %4.1f%%"
          % ("", ms([m["hcn"] for m in cut])[0], *ms([m["sig"] for m in cut]),
             ms([m["z"] for m in cut])[0], ms([m["cov"] for m in cut])[0] * 100))
        # rongorongo at the same L (best = horley merge, and freq)
        L = Lref
        rr = {}
        if L <= len(horl_types):
            rr["horley"] = measure(apply(horl, bin_map(horl_types, L)), rng, 50)
        keep = set(base_freq[:L - 1])
        rr["freq"] = measure(apply(base, {t: (t if t in keep else "OTHER") for t in base_types}), rng, 50)
        p("%-9s        rongorongo: " % "" + "  ".join("%s sig %+.3f cov %.1f%%" % (k, v["sig"], v["cov"] * 100) for k, v in rr.items()))
        gap = ms([m["sig"] for m in cut])[0]
        best = min(v["sig"] for v in rr.values())
        p("%-9s        ratio ref/rr (best rr) = %.1fx" % ("", gap / best if best else float("nan")))

    # ---------- B. sample-size scaling ----------
    p("")
    p("=" * 96)
    p("B. SIGNAALI OTOSKOON FUNKTIONA (osuus rongorongon 14812 tokenista; jaksopituudet rr:n mukaan; 15 vetoa)")
    p("=" * 96)
    fracs = [0.25, 0.5, 0.75, 1.0]
    p("%-22s" % "sarja" + "".join("%14s" % ("%d%%" % int(f * 100)) for f in fracs))
    series = {}
    series["rr horley L=125"] = horl
    series["rr horley->55"] = apply(horl, bin_map(horl_types, 55))
    series["rr horley->95"] = apply(horl, bin_map(horl_types, 95))
    keep = set(base_freq[:54])
    series["rr freq->55"] = apply(base, {t: (t if t in keep else "OTHER") for t in base_types})
    for name, runs in series.items():
        vals = []
        for f in fracs:
            xs = [measure(sub_runs(runs, f, rng), rng, 20)["sig"] for _ in range(DRAWS)] if f < 1 else [measure(runs, rng, 50)["sig"]]
            vals.append(ms(xs))
        p("%-22s" % name + "".join("%+8.3f+-%.3f" % v for v in vals))
    for name, runs in refs.items():
        vals = []
        for f in fracs:
            xs = []
            for _ in range(DRAWS):
                w = window(runs, int(n_rr * f), rng)
                lens = sub_runs(base, f, rng)
                xs.append(measure(recut(w, [len(r) for r in lens], rng), rng, 20)["sig"])
            vals.append(ms(xs))
        p("%-22s" % ("ref " + name) + "".join("%+8.3f+-%.3f" % v for v in vals))

    txt = "\n".join(out)
    print(txt)
    open("robustness_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
