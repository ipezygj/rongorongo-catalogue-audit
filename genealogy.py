"""Do genealogies climb? The genre the rongorongo tradition actually names.

Tradition names kohau ika, kohau taʼu and genealogies - name lists, not prose or
song. climbing.py showed word-level language rising to an interior maximum like
rongorongo does. A genealogy is a word-level text made almost entirely of rare
proper names, so if anything should climb steeply it is this.

Corpus: the two genealogy chapters of the Rapa Nui and Maori New Testaments -
Matthew 1 ("A X he matuʼa o Y") and Luke 3 ("A X he poki ʼa Y"). Small, and the
sample size is reported rather than hidden.
"""
import io, os, re, sys, random, glob
from collections import Counter
sys.path.insert(0, ".")
from horley import stats
from korovina_ref import clean, RAP_C
from syllabary_ref import syllabify

rng = random.Random(20260822)
LS = [20, 30, 55, 90, 150, 250]
o = []; p = o.append


def sig_of(runs, shuffles=40):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    return s["hcn"] - sum(vals) / len(vals), s["L"], s["n"]


def fold_to(runs, L):
    c = Counter(t for r in runs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in runs]


def words(text):
    text = re.sub(r"\d+", " . ", text)
    text = re.sub(r"[⌊⌋()]", " ", text)
    out = []
    for seg in re.split(r"[.!?;:]", text):
        ws = [w.strip(",\"'“”«»") .lower() for w in seg.split()]
        ws = [w for w in ws if w and any(c.isalpha() for c in w)]
        if len(ws) > 1:
            out.append(ws)
    return out


# Rapa Nui genealogies
t = io.open("ref/rap/rap_nt.txt", encoding="utf-8").read()
def chap(name):
    i = t.find("## " + name)
    j = t.find("## ", i + 3)
    s = t[i:j if j > 0 else len(t)]
    s = re.sub(r"Currently Selected:.*", " ", s, flags=re.S)
    s = re.sub(r"data-testid=\"[^\"]*\"|lang=\"[^\"]*\"|>", " ", s)
    return s
rap_gen = chap("MAT 1") + " " + chap("LUK 3")

# Maori genealogies
mri_gen = ""
for f in glob.glob("ref/mri/mri_*_MAT_01_read.txt") + glob.glob("ref/mri/mri_*_LUK_03_read.txt"):
    mri_gen += io.open(f, encoding="utf-8-sig", errors="replace").read() + "\n"

# prose controls of comparable size, same languages
rap_prose_full = clean(io.open("korovina_files/Isla6.txt", encoding="utf-8-sig").read())[0]

series = {
    "Rapa Nui GENEALOGY": words(rap_gen),
    "Maori GENEALOGY":    words(mri_gen),
    "GENEALOGY pooled":   words(rap_gen) + words(mri_gen),
}
# size-matched prose control
gen_tok = sum(len(r) for r in series["GENEALOGY pooled"])
pr = words(rap_prose_full)
acc, cut = 0, []
for r in pr:
    cut.append(r); acc += len(r)
    if acc >= gen_tok: break
series["Rapa Nui PROSE (matched)"] = cut

p("=" * 88)
p("GENEALOGY vs PROSE at word level: signal by catalogue size")
p("=" * 88)
for name, runs in series.items():
    n = sum(len(r) for r in runs)
    types = len(Counter(w for r in runs for w in r))
    row = []
    for L in LS:
        row.append(sig_of(fold_to(runs, L))[0] if L <= types else float("nan"))
    p("%-26s n=%5d types=%4d  %s"
      % (name, n, types, "  ".join("%+7.4f" % v if v == v else "      -" for v in row)))
p("")
p("%-26s %s" % ("", "  ".join("L=%-4d" % L for L in LS)))
p("")
p("for comparison (climbing.py, N=15115): rongorongo peaks at L=90 (-0.0490);")
p("Rapa Nui words peak at L=150 (-0.1410); Hawaiian song words at L=90 (-0.0913).")

txt = "\n".join(o)
io.open("genealogy_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
