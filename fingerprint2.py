"""Per-object repetition, and what the Santiago Staff actually is.

Prior work, which this does not repeat and must not be confused with:
  Fischer (1995) read the Staff as ~113 procreation triads X-76-Y-Z and stated
    himself that 76 "is attached to the first glyph in each section".
  Guy, Pozdniakov & Pozdniakov, and Robinson refuted the triads qualitatively
    (only 63 of 113 sequences obey the structure; 76 occurs isolated, doubled,
    and in the wrong part of the triplet).
  Sproat (ror pages) removed 76 from the corpus and recomputed approximate
    string matches ACROSS objects, to test Fischer's "phallus omission": the
    Staff remained an isolate. He also notes the vertical divider 999.

What is measured here is a different quantity: repetition WITHIN each object
against that object's own shuffle, and what is left of the Staff's anomaly once
the divider and the unidentified-glyph code are treated as what they are.

000 (written 000! in 380 of 390 cases) marks a glyph present but unidentified;
999 is the Staff's vertical divider. Both are breaks here, in every reading.
"""
import io, re, sys, glob, os, random
from collections import Counter
import xml.etree.ElementTree as ET
sys.path.insert(0, ".")
from horley import horley_lookup

rng = random.Random(20260822)
NOT_SIGNS = {"000", "999"}
MAXLAG = 6
o = []
p = o.append


def object_runs(path, reading):
    """Runs of tokens for one object; 000/999/lacunae/unmapped break the chain."""
    root = ET.parse(path).getroot()
    runs, cur = [], []
    for line in root.iter("line"):
        for g in line.iter("glyph"):
            code = (g.findtext("code/ceipp") or "").strip()
            link = (g.findtext("link") or "").strip()
            m = re.match(r"^0*(\d+)", code.replace("!", ""))
            if not m or re.match(r"^(\d+)", code.replace("!", "")).group(1) in NOT_SIGNS:
                if cur: runs.append(cur); cur = []
                continue
            if reading == "horley":
                parts = horley_lookup(code)
                if not parts:
                    if cur: runs.append(cur); cur = []
                    continue
                cur.extend(parts)
            else:
                cur.append(m.group(1))
            if link in ("*", "…"):
                if cur: runs.append(cur); cur = []
        if cur: runs.append(cur); cur = []
    return [r for r in runs if r]


def lag_ratio(runs, maxlag=MAXLAG, reps=12):
    """Observed / shuffled rate of x[i]==x[i+k], for k=1..maxlag."""
    def counts(rs):
        hit = [0] * (maxlag + 1); tot = [0] * (maxlag + 1)
        for r in rs:
            for k in range(1, maxlag + 1):
                for i in range(len(r) - k):
                    tot[k] += 1
                    if r[i] == r[i + k]: hit[k] += 1
        return hit, tot
    h, t = counts(runs)
    eh = [0.0] * (maxlag + 1)
    for _ in range(reps):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        hh, _ = counts(sh)
        for k in range(1, maxlag + 1): eh[k] += hh[k] / reps
    return [(h[k] / eh[k]) if eh[k] > 0.5 else float("nan") for k in range(1, maxlag + 1)], sum(len(r) for r in runs)


p("=" * 100)
p("PER-OBJECT REPETITION, observed / own-shuffle, lags 1-%d  (000 and 999 treated as non-signs)" % MAXLAG)
p("=" * 100)
p("%-4s %-22s %6s  %s" % ("obj", "name", "tokens", "  ".join("lag%d" % k for k in range(1, MAXLAG + 1))))
staff = None
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    obj = os.path.basename(path)[:-4]
    name = (ET.parse(path).getroot().findtext(".//tablet-name") or "").strip()[:22]
    runs = object_runs(path, "horley")
    if sum(len(r) for r in runs) < 300:
        continue
    rat, n = lag_ratio(runs)
    if obj == "I": staff = runs
    p("%-4s %-22s %6d  %s" % (obj, name, n, "  ".join("%5.2f" % x for x in rat)))

p("")
p("=" * 100)
p("THE SANTIAGO STAFF (I): what 76 is doing")
p("=" * 100)
raw = object_runs("ceipp/xml/I.xml", "numeric")
flat = [t for r in raw for t in r]
c = Counter(flat)
p("  tokens after removing 000/999: %d;  76 = %d (%.1f%%), next commonest %s"
  % (len(flat), c["076"] if "076" in c else c["76"], 100.0 * (c["076"] if "076" in c else c["76"]) / len(flat),
     [(k, v) for k, v in c.most_common(4) if k not in ("076", "76")][:3]))

# segment lengths between successive 76s
seglen = Counter()
for r in raw:
    cur = 0
    for t in r:
        if t == "076": seglen[cur] += 1; cur = 0
        else: cur += 1
p("  segment lengths between successive 76: " +
  ", ".join("%d:%d" % (k, seglen[k]) for k in sorted(seglen) if k <= 6) +
  "   (>6: %d)" % sum(v for k, v in seglen.items() if k > 6))

for label, runs in (("Staff as encoded", staff),
                    ("Staff with 76 removed", [[t for t in r if t not in ("76", "076")] for r in staff])):
    runs = [r for r in runs if len(r) > 1]
    rat, n = lag_ratio(runs)
    p("  %-24s n=%5d  %s" % (label, n, "  ".join("lag%d %5.2f" % (k + 1, x) for k, x in enumerate(rat))))
p("")
p("  Fischer's triads predict a period-3 excess. lag3 above is the test.")

txt = "\n".join(o)
io.open("fingerprint2_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
