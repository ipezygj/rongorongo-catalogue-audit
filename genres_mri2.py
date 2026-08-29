"""Chant vs narrative in Maori, at a sample size large enough to place the peak.

genres_mri.py showed that the peak of the signal/size curve moves left when the
sample is small: at 1 216 words every Maori genre peaks near L=30, where the same
languages at 15 000 words peak near L=150. Peak position is therefore only
comparable at matched N, and Maori teaching (1 216 words) and genealogy (339)
are too small to carry one. Chant and narrative are not.
"""
import io, os, re, sys, random, glob
from collections import Counter
sys.path.insert(0, ".")
from horley import stats
from fingerprint2 import object_runs

rng = random.Random(20260822)
LS = [30, 55, 90, 150, 300, 633]
MRI = set("aeiouhkmnprtwg")
o = []; p = o.append


def sig_of(runs, shuffles=25):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    return s["hcn"] - sum(vals) / len(vals)


def fold_to(runs, L):
    c = Counter(t for r in runs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in runs]


def mri_words(text, thresh=0.85):
    out = []
    text = re.sub(r"\d+", " . ", text)
    for line in re.split(r"[\n.!?;:]", text):
        ws = [w.strip(",\"'“”«»()[]-—…").lower() for w in line.split()]
        ws = [w for w in ws if w and any(c.isalpha() for c in w)]
        if len(ws) < 2: continue
        ok = sum(1 for w in ws if all((not c.isalpha()) or c in MRI for c in w)) / len(ws)
        if ok >= thresh: out.append(ws)
    return out


def cut(runs, n):
    acc, out = 0, []
    for r in runs:
        out.append(r); acc += len(r)
        if acc >= n: break
    return out


chant = mri_words(io.open("ref/maori_old/moteatea.txt", encoding="utf-8", errors="replace").read())
narr_files = [f for f in sorted(glob.glob("ref/mri/mri_*_read.txt"))
              if any(b in f for b in ("MAT", "MRK", "LUK", "JHN", "ACT"))]
narrative = mri_words("\n".join(io.open(f, encoding="utf-8-sig", errors="replace").read() for f in narr_files))

p("=" * 92)
p("MAORI CHANT vs NARRATIVE, word level, peak located at three sample sizes")
p("=" * 92)
p("  chant available %d words, narrative %d" % (sum(len(r) for r in chant), sum(len(r) for r in narrative)))
p("")
p("%-11s %6s %6s %6s  %s" % ("genre", "N", "words", "types", "  ".join("L=%-4d" % L for L in LS)))
for N in (5000, 12000, 25000):
    for name, runs in (("chant", chant), ("narrative", narrative)):
        rs = cut(runs, N)
        n = sum(len(r) for r in rs)
        if n < N * 0.9: continue
        types = len(Counter(w for r in rs for w in r))
        row = [sig_of(fold_to(rs, L)) if L <= types else float("nan") for L in LS]
        vals = [v for v in row if v == v]
        peak = LS[row.index(min(vals))] if vals else 0
        p("%-11s %6d %6d %6d  %s  peak L=%d"
          % (name, N, n, types, "  ".join("%+7.4f" % v if v == v else "      -" for v in row), peak))
    p("")
p("rongorongo at N=15115 peaks at L=90 with -0.0490 (climbing.py).")
txt = "\n".join(o)
io.open("genres_mri2_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
