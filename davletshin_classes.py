"""Davletshin's combinatorial-class claim, measured.

Davletshin 2017 (JPS 126:1), on the Horley/Barthel signs:
  "Some signs form sequences of the kind ABAB, BABA, AAAA and AAA in combinations
   with other signs ... Other signs do not form such sequences, tend to be used in
   isolation ... Probably signs of the first type are phonetic signs (spelling
   syllables) and signs of the second type are word-signs."
Davletshin 2022 (JPS 131:2): ABAB resembles Polynesian full reduplication
  (nui-nui); AAA/AAAA cannot be word repetition in any language.

That is a claim at the level of individual signs, not of the corpus. It predicts:
  P1  the ABAB / AAA events are CONCENTRATED on a minority of sign types
  P2  the signs that carry them are NOT the ones that occur in isolation
      (isolation = the sign's neighbours on both sides are breaks or the sign
       stands as a one-token run)
  P3  (ours, not his) syllabified Rapa Nui should show the SAME concentration if
      ABAB there is reduplication - because reduplication applies to roots, which
      are a minority of syllables. If language concentrates too, P1 is not a
      discriminator; if language spreads ABAB evenly and rongorongo does not,
      that is a genuine contrast.

All against the within-object null, the one Appendix A settled on.
"""
import io, os, sys, glob, random, math
from collections import Counter, defaultdict
sys.path.insert(0, ".")
from fingerprint2 import object_runs
from syllabary_ref import syllabify, load_rap
from korovina_ref import clean, RAP_C

rng = random.Random(20260823)
o = []; p = o.append


def events(runs):
    """Per sign type: #ABAB events it takes part in (as A or B), #AAA events, #tokens,
    #isolated tokens. ABAB counted once per (i) with r[i]==r[i+2], r[i+1]==r[i+3], A!=B."""
    abab = Counter(); aaa = Counter(); tok = Counter(); iso = Counter()
    for r in runs:
        n = len(r)
        for i, t in enumerate(r):
            tok[t] += 1
            if n == 1:
                iso[t] += 1
        for i in range(n - 3):
            if r[i] == r[i + 2] and r[i + 1] == r[i + 3] and r[i] != r[i + 1]:
                abab[r[i]] += 1; abab[r[i + 1]] += 1
        for i in range(n - 2):
            if r[i] == r[i + 1] == r[i + 2]:
                aaa[r[i]] += 1
    return abab, aaa, tok, iso


def gini(xs):
    xs = sorted(x for x in xs if x >= 0)
    n = len(xs); s = sum(xs)
    if n == 0 or s == 0: return float("nan")
    cum = 0.0
    for i, x in enumerate(xs, 1):
        cum += i * x
    return (2 * cum) / (n * s) - (n + 1) / n


def report(name, runs, topk=12):
    abab, aaa, tok, iso = events(runs)
    types = len(tok); N = sum(tok.values())
    n_abab = sum(abab.values()) // 2; n_aaa = sum(aaa.values())
    carriers = [t for t in abab if abab[t] > 0]
    p("=" * 96)
    p("%s  |  %d types, %d tokens  |  ABAB events %d on %d sign types (%.0f%% of types)  |  AAA %d"
      % (name, types, N, n_abab, len(carriers), 100.0 * len(carriers) / types, n_aaa))
    # P1 concentration: share of ABAB participation carried by the top 10% of types
    ranked = sorted(abab.items(), key=lambda kv: -kv[1])
    tot = sum(abab.values())
    top10 = max(1, types // 10)
    share10 = sum(v for _, v in ranked[:top10]) / tot if tot else float("nan")
    # expected under frequency alone: weight types by token count
    p("  P1 concentration: top 10%% of types carry %.0f%% of ABAB participation (Gini %.2f over all types)"
      % (100 * share10, gini([abab.get(t, 0) for t in tok])))
    # token-frequency-matched expectation: same ABAB count, assigned proportional to tok^2 (pairs)
    w = {t: tok[t] ** 2 for t in tok}; W = sum(w.values())
    exp_share = sum(sorted((w[t] / W for t in tok), reverse=True)[:top10])
    p("  if ABAB simply followed frequency (weight tok^2), top 10%% would carry %.0f%%" % (100 * exp_share))
    # P2 isolation vs ABAB: do ABAB carriers appear as 1-token runs less than others?
    iso_rate_car = sum(iso[t] for t in carriers) / max(1, sum(tok[t] for t in carriers))
    non = [t for t in tok if t not in abab]
    iso_rate_non = sum(iso[t] for t in non) / max(1, sum(tok[t] for t in non))
    p("  P2 isolation rate (share of a sign's tokens standing as a 1-token run):")
    p("     ABAB carriers %.2f%%   non-carriers %.2f%%" % (100 * iso_rate_car, 100 * iso_rate_non))
    p("  top ABAB carriers: " + ", ".join("%s(%d/%d)" % (t, abab[t] // 1, tok[t]) for t, _ in ranked[:topk]))
    if n_aaa:
        p("  AAA carriers: " + ", ".join("%s(%d)" % kv for kv in sorted(aaa.items(), key=lambda kv: -kv[1])[:topk]))
    return abab, tok


# rongorongo, Horley reading, per-object runs (000/999 already breaks)
objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    r = object_runs(path, "horley")
    if sum(len(x) for x in r) >= 100:
        objs[os.path.basename(path)[:-4]] = r
rr = [r for runs in objs.values() for r in runs]
ab_rr, tok_rr = report("RONGORONGO (Horley 125, per-object runs)", rr)

# Rapa Nui syllables (Isla6, native prose), cut to the rongorongo run lengths
lens = sorted(len(r) for r in rr)
rap = syllabify(clean(io.open("korovina_files/Isla6.txt", encoding="utf-8-sig").read())[0], RAP_C, True)
flat = [t for r in rap for t in r]
cut, i, j = [], 0, 0
N_RR = sum(len(r) for r in rr)
while i < len(flat) and i < N_RR:
    L = lens[j % len(lens)]; cut.append(flat[i:i + L]); i += L; j += 1
ab_rap, tok_rap = report("RAPA NUI syllables (Isla6), rongorongo run lengths, matched N", cut)

# Rapa Nui WORDS - reduplication lives at the root/word level
words = [[w for w in line.split() if w] for line in
         clean(io.open("korovina_files/Isla6.txt", encoding="utf-8-sig").read())[0].replace(".", " . ").split(" . ")]
words = [r for r in words if len(r) > 1]
flat = [t for r in words for t in r]
cut, i, j = [], 0, 0
while i < len(flat) and i < N_RR:
    L = lens[j % len(lens)]; cut.append(flat[i:i + L]); i += L; j += 1
report("RAPA NUI words (Isla6), rongorongo run lengths, matched N", cut)

# Linear B - a syllabary that is NOT Polynesian and has no reduplication to speak of.
# If it spreads ABAB like Rapa Nui does, the spread is a property of syllabic text;
# if it concentrates or lacks ABAB, the Rapa Nui/rongorongo match is about the language.
from syllabary_ref import load_linb
linb = load_linb()
flat = [t for r in linb for t in r]
cut, i, j = [], 0, 0
while i < len(flat) and i < N_RR:
    L = lens[j % len(lens)]; cut.append(flat[i:i + L]); i += L; j += 1
report("LINEAR B syllabograms, rongorongo run lengths, matched N", cut)

# Maori syllables - a second Polynesian language, to see whether Rapa Nui is typical
from syllabary_ref import load_mri
MRI_C = ["ng","wh","h","k","m","n","p","r","t","w"]
mri = syllabify(load_mri(), MRI_C, True)
flat = [t for r in mri for t in r]
cut, i, j = [], 0, 0
while i < len(flat) and i < N_RR:
    L = lens[j % len(lens)]; cut.append(flat[i:i + L]); i += L; j += 1
report("MAORI syllables (NT), rongorongo run lengths, matched N", cut)

p("")
p("Reading: Davletshin predicts P1 (concentration) and P2 (carriers not isolated) for")
p("rongorongo. P3 asks whether Rapa Nui shows the same concentration - if it does, P1")
p("is a property of reduplicating languages in general and not a discriminator.")
txt = "\n".join(o)
io.open("davletshin_classes_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
