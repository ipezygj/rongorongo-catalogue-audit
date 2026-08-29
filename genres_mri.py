"""Four genres, one language. Does the shape of the curve separate them?

Within Maori, so the language is held fixed and only the genre varies:
  chant      Grey 1853, Ko nga moteatea me nga hakirara - traditional sung poetry
  teaching   James + the Sermon on the Mount (Matthew 5-7) - aphoristic instruction
  narrative  the gospels and Acts, minus the teaching and genealogy chapters
  genealogy  Matthew 1 and Luke 3 - the name-list formula

The user's point: newspapers are news prose and nothing anyone would carve. The
genres worth testing are the ones worth the labour of inscription - song, and
teaching or wisdom. rongorongo peaks at L=90 with a word-level shape; the
question is which genre does that.
"""
import io, os, re, sys, random, glob
from collections import Counter
sys.path.insert(0, ".")
from horley import stats

rng = random.Random(20260822)
LS = [20, 30, 55, 90, 150, 250]
MRI = set("aeiouhkmnprtwg")
o = []; p = o.append


def sig_of(runs, shuffles=40):
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
        if len(ws) < 2:
            continue
        ok = sum(1 for w in ws if all((not c.isalpha()) or c in MRI for c in w)) / len(ws)
        if ok >= thresh:
            out.append(ws)
    return out


def read(pat):
    return "\n".join(io.open(f, encoding="utf-8-sig", errors="replace").read()
                     for f in sorted(glob.glob(pat)))


chant = mri_words(io.open("ref/maori_old/moteatea.txt", encoding="utf-8", errors="replace").read())
teaching = mri_words(read("ref/mri/mri_*_JAS_*_read.txt")
                     + read("ref/mri/mri_*_MAT_0[567]_read.txt"))
genealogy = mri_words(read("ref/mri/mri_*_MAT_01_read.txt")
                      + read("ref/mri/mri_*_LUK_03_read.txt"))
skip = ("MAT_01", "MAT_05", "MAT_06", "MAT_07", "LUK_03", "JAS")
narr_files = [f for f in sorted(glob.glob("ref/mri/mri_*_read.txt"))
              if any(b in f for b in ("MAT", "MRK", "LUK", "JHN", "ACT"))
              and not any(s in f for s in skip)]
narrative = mri_words("\n".join(io.open(f, encoding="utf-8-sig", errors="replace").read()
                                for f in narr_files))

full = {"chant": chant, "teaching": teaching, "narrative": narrative, "genealogy": genealogy}
for k, v in full.items():
    p("  raw %-10s %6d words" % (k, sum(len(r) for r in v)))
# genealogy alone is too small to carry the others down with it; match the rest
series = {k: v for k, v in full.items() if k != "genealogy"}
N = min(sum(len(r) for r in v) for v in series.values())
p("=" * 92)
p("FOUR MAORI GENRES, word level, all cut to N = %d words" % N)
p("=" * 92)


def cut(runs, n):
    acc, out = 0, []
    for r in runs:
        out.append(r); acc += len(r)
        if acc >= n:
            break
    return out


p("%-11s %6s %6s  %s" % ("genre", "words", "types", "  ".join("L=%-4d" % L for L in LS)))
peaks = {}
for name, runs in series.items():
    rs = cut(runs, N)
    types = len(Counter(w for r in rs for w in r))
    row = [sig_of(fold_to(rs, L)) if L <= types else float("nan") for L in LS]
    best = min((v for v in row if v == v), default=float("nan"))
    peaks[name] = LS[row.index(best)]
    p("%-11s %6d %6d  %s   peak L=%d"
      % (name, sum(len(r) for r in rs), types,
         "  ".join("%+7.4f" % v if v == v else "      -" for v in row), peaks[name]))
p("")
p("genealogy is reported separately, at its own size against a size-matched")
p("narrative control, because Maori genealogy is only %d words." % sum(len(r) for r in full["genealogy"]))
g = full["genealogy"]; ng = sum(len(r) for r in g)
ctrl = cut(full["narrative"], ng)
for name, rs in (("genealogy", g), ("narrative(matched)", ctrl)):
    types = len(Counter(w for r in rs for w in r))
    row = [sig_of(fold_to(rs, L)) if L <= types else float("nan") for L in LS]
    best = min((v for v in row if v == v), default=float("nan"))
    p("%-19s %6d %6d  %s   peak L=%d" % (name, sum(len(r) for r in rs), types,
      "  ".join("%+7.4f" % v if v == v else "      -" for v in row), LS[row.index(best)]))
p("")
p("rongorongo peaks at L=90 (climbing.py, -0.0490).")
txt = "\n".join(o)
io.open("genres_mri_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
