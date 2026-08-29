"""Davletshin 2022's deciphered signs against the ABAB/AAA ranking.

He names 11 signs with cross-read values: three syllabic readings (ki, ka, pa) and
six logographic (MEA RED, TOKI ADZE, TURTLE, SHELL, SMALL SHELL, URCHIN). He uses
nicknames, not Barthel numbers. Two syllabic signs are identifiable without guessing:
  "*Staff" = ki   -- "the most frequent sign in the corpus (775 examples)"; Barthel
                     200 is the staff and Horley folds 200-207 into 200; 200 is the
                     commonest Horley sign here (1011 tokens).
  "Sitting Man" = ka -- Barthel 380-389; Horley folds 380-387 into 381.
Prediction: if his reading is right, 200 and 381 should rank HIGH as ABAB carriers
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
for lab, code in [("*Staff = ki", "200"), ("Sitting Man = ka", "381")]:
    print("  %-18s Horley %-4s tokens %5d  ABAB %3d  rank %3d/%d  AAA %d  iso %d"
          % (lab, code, tok[code], abab.get(code, 0), rank[code], L, aaa.get(code, 0), iso.get(code, 0)), file=out)

# ABAB rate per token, so frequency is controlled: events per 100 tokens
print("\nABAB per 100 tokens, his two syllabic signs vs the corpus:", file=out)
for code in ["200", "381"]:
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
out.flush()
