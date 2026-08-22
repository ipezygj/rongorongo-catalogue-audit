"""Why is Campbell at 1.80x when the other three Rapa Nui collections are 3.1-3.5x?

Three candidate causes, each tested by degrading Isla6 -- the best-marked
collection -- in that one respect and re-measuring:

  A  orthography: Isla6 marks glottal stops 46 times per 1000 characters,
     Campbell 3.0. Strip glottals (and macrons) from Isla6.
  B  filtering:   10.3% of Campbell's words were dropped as non-Rapa Nui
     against 1.0% of Isla6's, each drop cutting the chain. Inject breaks
     into Isla6 at Campbell's rate.
  C  length:      Campbell has 20 809 tokens against Isla6's 53 508, so the
     14 812-token windows overlap heavily. Truncate Isla6 to Campbell's size.

Plus D: the repetition profile of each collection, because Campbell is
chant and song where the others are narrative prose.
"""
import io, re, sys, random
from collections import Counter
sys.path.insert(0, ".")
from sweep import measure
from syllabary_ref import syllabify, sample_runs, N_RR
from korovina_ref import clean, RAP_C

rng = random.Random(20260822)
out = []
p = out.append


def load(name):
    return clean(io.open("korovina_files/%s.txt" % name, encoding="utf-8-sig").read())[0]


def sig_of(runs, n=None, reps=12):
    if n:
        vals = [measure(sample_runs(runs, n, rng), rng, 30)["sig"] for _ in range(reps)]
        return sum(vals) / len(vals)
    return measure(runs, rng, 30)["sig"]


def rep_profile(runs):
    """AA, AAA, ABAB counts against a within-run shuffle of the same tokens."""
    def counts(rs):
        aa = aaa = abab = 0
        for r in rs:
            for i in range(len(r) - 1):
                if r[i] == r[i + 1]:
                    aa += 1
                    if i + 2 < len(r) and r[i + 2] == r[i]:
                        aaa += 1
                if i + 3 < len(r) and r[i] == r[i + 2] and r[i + 1] == r[i + 3] and r[i] != r[i + 1]:
                    abab += 1
        return aa, aaa, abab
    obs = counts(runs)
    exp = [0.0, 0.0, 0.0]
    for _ in range(10):
        sh = []
        for r in runs:
            q = r[:]
            rng.shuffle(q)
            sh.append(q)
        c = counts(sh)
        for j in range(3):
            exp[j] += c[j] / 10.0
    return [(obs[j], exp[j], (obs[j] / exp[j] if exp[j] > 0.5 else float("nan"))) for j in range(3)]


isla_raw = load("Isla6")
camp_raw = load("Campbell")
isla = syllabify(isla_raw, RAP_C, True)
camp = syllabify(camp_raw, RAP_C, True)
n_camp = sum(len(r) for r in camp)

p("=" * 92)
p("WHY IS CAMPBELL LOW?  baseline signals at matched N=14812 windows")
p("=" * 92)
b_isla = sig_of(isla, N_RR)
b_camp = sig_of(camp, N_RR)
p("  Isla6    %+.4f" % b_isla)
p("  Campbell %+.4f      (ratio Campbell/Isla6 = %.2f)" % (b_camp, b_camp / b_isla))

p("")
p("A  ORTHOGRAPHY: strip glottals and macrons from Isla6 (imitating Campbell's marking)")
deg = isla_raw
for g in ["'", "’", "ʼ", "ꞌ"]:
    deg = deg.replace(g, "")
for a, b in zip("āēīōū", "aeiou"):
    deg = deg.replace(a, b)
a_sig = sig_of(syllabify(deg, RAP_C, True), N_RR)
p("   Isla6 stripped   %+.4f   (was %+.4f, moved %+.4f = %.0f%% of the way to Campbell)"
  % (a_sig, b_isla, a_sig - b_isla, 100 * (a_sig - b_isla) / (b_camp - b_isla)))

p("")
p("B  FILTERING: cut Isla6's chain at Campbell's drop rate (10.3%% of words -> breaks)")
words = isla_raw.split()
kept = [(" . " if rng.random() < 0.093 else w) for w in words]   # 10.3% - 1.0% already dropped
b_sig = sig_of(syllabify(" ".join(kept), RAP_C, True), N_RR)
p("   Isla6 chopped    %+.4f   (moved %+.4f = %.0f%% of the way)"
  % (b_sig, b_sig - b_isla, 100 * (b_sig - b_isla) / (b_camp - b_isla)))

p("")
p("C  LENGTH: truncate Isla6 to Campbell's token count (%d), same window procedure" % n_camp)
acc, trunc = 0, []
for r in isla:
    trunc.append(r); acc += len(r)
    if acc >= n_camp:
        break
c_sig = sig_of(trunc, N_RR)
p("   Isla6 truncated  %+.4f   (moved %+.4f = %.0f%% of the way)"
  % (c_sig, c_sig - b_isla, 100 * (c_sig - b_isla) / (b_camp - b_isla)))

p("")
p("=" * 92)
p("D  REPETITION PROFILE (observed / within-run shuffle expectation)")
p("=" * 92)
p("%-12s %10s %10s %10s" % ("text", "AA", "AAA", "ABAB"))
for nm in ["Campbell", "Englert", "Isla6", "ManuE"]:
    r = syllabify(load(nm), RAP_C, True)
    pr = rep_profile(r)
    p("%-12s %9.2fx %9.2fx %9.2fx" % (nm, pr[0][2], pr[1][2], pr[2][2]))

txt = "\n".join(out)
io.open("campbell_probe_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
