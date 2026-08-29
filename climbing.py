"""Does anything climb? Signal vs catalogue size for language at two granularities.

The L-matched table shows Polynesian syllable text saturating by L=40 while
rongorongo keeps climbing to L=90. That contrast is only diagnostic if no
language behaves the way rongorongo does. Syllables are a poor test: there are
only about 40 of them, so nothing is left to merge above that.

Words are the fair test. There are thousands, and rare words carry sequential
information that merging destroys - which is exactly the shape rongorongo shows.
If word-level language climbs, then rongorongo's climb is consistent with its
signs being word-like rather than syllable-like, which is Korovina's
logosyllabic hypothesis stated as a measurement.

Series: Rapa Nui words, Hawaiian prose words, Hawaiian song words, Linear B
(already word-like), against rongorongo under its own rules.
"""
import io, os, re, sys, random, glob
from collections import Counter
sys.path.insert(0, ".")
from horley import stats, read_lines, tokens_plain, tokens_horley
from sweep import bin_map, apply, num_key
from syllabary_ref import load_rap, load_mri, load_linb, syllabify
from korovina_ref import clean, RAP_C
from fingerprint2 import object_runs

rng = random.Random(20260822)
LS = [30, 55, 90, 150, 300, 633]
o = []; p = o.append


def fold_to(runs, L):
    c = Counter(t for r in runs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in runs]


def recut(runs, lengths, cap):
    flat = [t for r in runs for t in r]
    out, i, j = [], 0, 0
    while i < len(flat) and i < cap and j < 200000:
        Ln = lengths[j % len(lengths)]
        out.append(flat[i:i + Ln]); i += Ln; j += 1
    return [r for r in out if len(r) > 1]


def sig_of(runs, shuffles=25):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    return s["hcn"] - sum(vals) / len(vals)


def words(text_lines):
    return [[w for w in line.split() if w] for line in text_lines if len(line.split()) > 1]


HAWSET = set("aeiouhklmnpw")
def haw_lines(text):
    out = []
    for line in text.splitlines():
        for a, b in [("ʻ",""),("ʼ",""),("‘",""),("’",""),("`",""),
                     ("ā","a"),("ē","e"),("ī","i"),("ō","o"),("ū","u")]:
            line = line.replace(a, b)
        line = line.lower()
        ws = [w.strip(".,;:!?()[]\"'-–—…") for w in line.split()]
        ws = [w for w in ws if w and any(c.isalpha() for c in w)]
        if len(ws) < 3: continue
        if sum(1 for w in ws if all((not c.isalpha()) or c in HAWSET for c in w)) / len(ws) >= 0.8:
            out.append(" ".join(ws))
    return out


hd = os.path.expanduser("~/script-audit/ref/hawaiian")
prose_txt = "\n".join(io.open(os.path.join(hd, f), encoding="utf-8", errors="replace").read()
                      for f in ["fornander_72686.txt", "fornander_73166.txt"])
song_html = re.sub(r"<[^>]+>", "\n",
                   re.sub(r"<script.*?</script>|<style.*?</style>", " ",
                          io.open(os.path.join(hd, "songs_raw.txt"), encoding="utf-8", errors="replace").read(),
                          flags=re.S))
rap_txt = clean(io.open("korovina_files/Isla6.txt", encoding="utf-8-sig").read())[0]

series = {
    "Rapa Nui WORDS":   words([l for l in rap_txt.replace(".", " . ").split(" . ") if l.strip()]),
    "Hawaiian prose WORDS": words(haw_lines(prose_txt)),
    "Hawaiian song WORDS":  words(haw_lines(song_html)),
    "Rapa Nui SYLLABLES":   syllabify(rap_txt, RAP_C, True),
    "Linear B":             load_linb(),
}

objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    r = object_runs(path, "horley")
    if sum(len(x) for x in r) >= 100:
        objs[os.path.basename(path)[:-4]] = r
rr_runs = [r for runs in objs.values() for r in runs]
rr_lengths = sorted(len(r) for r in rr_runs)
N_RR = sum(len(r) for r in rr_runs)

p("=" * 96)
p("SIGNAL vs CATALOGUE SIZE, matched N=%d and rongorongo run lengths" % N_RR)
p("does anything climb the way rongorongo does?")
p("=" * 96)
p("%-22s %8s %s" % ("series", "types", "  ".join("L=%-4d" % L for L in LS)))
for name, runs in series.items():
    types = len(Counter(t for r in runs for t in r))
    row = []
    for L in LS:
        if L > types:
            row.append(float("nan")); continue
        row.append(sig_of(recut(fold_to(runs, L), rr_lengths, N_RR)))
    p("%-22s %8d %s" % (name, types, "  ".join("%+7.4f" % v if v == v else "     -" for v in row)))

lines = read_lines()
base = [r for s in lines for r in tokens_plain(s, True)]
horl = [r for s in lines for r in tokens_horley(s)]
bt = sorted(Counter(t for r in base for t in r), key=num_key)
ht = sorted(Counter(t for r in horl for t in r), key=num_key)
bf = [t for t, _ in Counter(t for r in base for t in r).most_common()]
row = []
for L in LS:
    c = [sig_of(apply(base, bin_map(bt, L)))]
    if L <= len(ht): c.append(sig_of(apply(horl, bin_map(ht, L))))
    keep = set(bf[:L - 1])
    c.append(sig_of(apply(base, {t: (t if t in keep else "OTHER") for t in bt})))
    row.append(max(c, key=abs))
p("%-22s %8d %s" % ("rongorongo (best)", len(bt), "  ".join("%+7.4f" % v for v in row)))

txt = "\n".join(o)
io.open("climbing_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
