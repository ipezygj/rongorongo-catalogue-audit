"""Davletshin 2022's deciphered signs against the ABAB/AAA ranking.

He names 11 signs with cross-read values: three syllabic readings (ki, ka, pa) and
six logographic (MEA RED, TOKI ADZE, TURTLE, SHELL, SMALL SHELL, URCHIN). He uses
nicknames, not Barthel numbers. Two syllabic signs are identifiable without guessing:
  "*Staff" = ki   -- Barthel 001. Corrected 2026-09-02: this script, and the paper
                     that quoted it, read *Staff as Barthel 200. Rafal Wieczorek
                     (p.c., 2 Sep 2026) gave the right code, and three checks agree
                     with him: Barthel 001 is drawn as a plain notched vertical bar
                     (rongopy/img/1.png) where 200 is an anthropomorph with limbs
                     (rongopy/img/200.png); Davletshin calls *Staff "the most
                     frequent sign in the corpus (775 examples)" and code 1 carries
                     787 tokens on the numeric reading against 313 for 200; and 200
                     looked commonest here only because Horley folds 201-207, 210,
                     300, 462 and 548 into it, while nothing at all folds into 1.
  "Sitting Man" = ka -- Barthel 380-389; Horley folds 380-387 into 381.
Prediction: if his reading is right, 1 and 381 should rank HIGH as ABAB carriers
(reduplication of syllables) and his logographs should carry little or no ABAB.
"""
import io, sys, re, glob, os
from collections import Counter
sys.path.insert(0, ".")
from fingerprint2 import object_runs

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def events(runs):
    abab = Counter(); aaa = Counter(); tok = Counter(); iso = Counter()
    for r in runs:
        n = len(r)
        for t in r:
            tok[t] += 1
        if n == 1:
            iso[r[0]] += 1
        for i in range(n - 3):
            if r[i] == r[i + 2] and r[i + 1] == r[i + 3] and r[i] != r[i + 1]:
                abab[r[i]] += 1; abab[r[i + 1]] += 1
        for i in range(n - 2):
            if r[i] == r[i + 1] == r[i + 2]:
                aaa[r[i]] += 1
    return abab, aaa, tok, iso


objs = {}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    r = object_runs(path, "horley")
    if sum(len(x) for x in r) >= 100:
        objs[os.path.basename(path)[:-4]] = r
rr = [r for runs in objs.values() for r in runs]
abab, aaa, tok, iso = events(rr)
ranked = sorted(tok, key=lambda t: (-abab.get(t, 0), -tok[t]))
rank = {t: i + 1 for i, t in enumerate(ranked)}
L = len(tok)

print("Horley types:", L, "| ABAB events:", sum(abab.values()) // 2, file=out)
print("\nDAVLETSHIN'S SYLLABIC SIGNS:", file=out)
for lab, code in [("*Staff = ki", "1"), ("Sitting Man = ka", "381")]:
    print("  %-18s Horley %-4s tokens %5d  ABAB %3d  rank %3d/%d  AAA %d  iso %d"
          % (lab, code, tok[code], abab.get(code, 0), rank[code], L, aaa.get(code, 0), iso.get(code, 0)), file=out)

# ABAB rate per token, so frequency is controlled: events per 100 tokens
print("\nABAB per 100 tokens, his two syllabic signs vs the corpus:", file=out)
for code in ["1", "381"]:
    print("  %-4s %.2f" % (code, 100.0 * abab.get(code, 0) / tok[code]), file=out)
allrate = 100.0 * sum(abab.values()) / sum(tok.values())
print("  corpus mean %.2f   | median over types with >=50 tokens: %.2f"
      % (allrate, sorted(100.0 * abab.get(t, 0) / tok[t] for t in tok if tok[t] >= 50)[len([t for t in tok if tok[t] >= 50]) // 2]), file=out)

print("\nTOP 15 ABAB CARRIERS:", file=out)
for t in ranked[:15]:
    print("  %-5s tokens %5d  ABAB %3d  per100 %.2f" % (t, tok[t], abab[t], 100.0 * abab[t] / tok[t]), file=out)

print("\nFREQUENT SIGNS WITH ZERO ABAB (>=80 tokens) -- where his logographs should sit:", file=out)
for t in sorted((t for t in tok if abab.get(t, 0) == 0 and tok[t] >= 80), key=lambda t: -tok[t]):
    print("  %-5s tokens %5d  AAA %d  iso %d" % (t, tok[t], aaa.get(t, 0), iso.get(t, 0)), file=out)

# Davletshin (p.c., 25 Aug 2026) supplied Horley codes for his six named
# logographic readings, in reply to being asked. Checked against the same
# ABAB counts as above.
print("\nDAVLETSHIN'S SIX LOGOGRAPHS (p.c., 25 Aug 2026, Horley codes as given):", file=out)
LOGOGRAPHS = [
    ("11", "MEA RED (tentative -- he suspects this class may conflate two signs)"),
    ("63", "TOKI ADZE"),
    ("280", "TURTLE"),
    ("70", "SHELL"),
    ("17", "SMALL SHELL"),
    ("102", "URCHIN"),
]
ZERO_ABAB = set(t for t in tok if abab.get(t, 0) == 0 and tok[t] >= 80)
for code, label in LOGOGRAPHS:
    t = tok.get(code, 0)
    a = abab.get(code, 0)
    r = rank.get(code)
    zero = code in ZERO_ABAB
    print("  %-4s %-55s tokens %4d  ABAB %2d  rank %3s/%d  %s"
          % (code, label, t, a, r if r else "-", L, "ZERO-ABAB match" if zero else "not a match"), file=out)
n_hit = sum(1 for code, _ in LOGOGRAPHS if code in ZERO_ABAB)
print("  -> %d of 6 fall among the seven zero-ABAB signs" % n_hit, file=out)
out.flush()
