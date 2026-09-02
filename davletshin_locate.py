"""Where the ABAB events for Davletshin's logographs actually sit in the CEIPP XML.

He asked (27 Aug 2026) for the surrounding lines / object image references rather
than my Horley numbers, because he abstains from transliterations and wants to
check the real texts. This rebuilds the token stream of fingerprint2.object_runs
exactly, but carries provenance for every emitted token: tablet, side, line, the
CEIPP glyph code as written, the glyph number in the line, and CEIPP's own image
filename for that glyph.
"""
import io, os, re, sys, glob
import xml.etree.ElementTree as ET
sys.path.insert(0, ".")
from horley import horley_lookup

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
NOT_SIGNS = {"000", "999"}

TARGETS = {"63": "TOKI ADZE", "70": "SHELL", "17": "SMALL SHELL",
           "280": "TURTLE", "11": "MEA RED", "102": "URCHIN",
           # Added 2026-09-02. His two syllabic signs were never located, only
           # counted, and the count was on the wrong sign: *Staff is Barthel 001,
           # not 200 (Wieczorek, p.c., 2 Sep 2026). A sign whose ABAB rate is the
           # paper's evidence has to survive the same ligature audit as the rest.
           "1": "*Staff = ki", "381": "Sitting Man = ka"}


def object_runs_prov(path):
    """Same walk as fingerprint2.object_runs(reading='horley'), with provenance."""
    root = ET.parse(path).getroot()
    tab = (root.findtext(".//tablet-code") or "").strip()
    runs, cur = [], []
    for side in root.iter("side"):
        sc = (side.findtext("side-code") or "").strip()
        for line in side.iter("line"):
            lc = (line.findtext("line-code") or "").strip()
            for g in line.iter("glyph"):
                code = (g.findtext("code/ceipp") or "").strip()
                link = (g.findtext("link") or "").strip()
                gn = (g.findtext("loc/glyph-num") or "").strip()
                sg = (g.findtext("loc/seg-num") or "").strip()
                img = (g.findtext("image/image_file") or "").strip()
                bare = code.replace("!", "")
                m = re.match(r"^0*(\d+)", bare)
                if not m or re.match(r"^(\d+)", bare).group(1) in NOT_SIGNS:
                    if cur: runs.append(cur); cur = []
                    continue
                parts = horley_lookup(code)
                if not parts:
                    if cur: runs.append(cur); cur = []
                    continue
                for k, ptok in enumerate(parts):
                    cur.append({"t": ptok, "tab": tab, "side": sc, "line": lc,
                                "seg": sg, "gnum": gn, "ceipp": code, "img": img,
                                "part": (k + 1, len(parts))})
                if link in ("*", "…"):
                    if cur: runs.append(cur); cur = []
            if cur: runs.append(cur); cur = []
    return [r for r in runs if r]


def ref(d):
    """CEIPP's own glyph id: tablet+side+line+seg-glyph, i.e. the image basename.

    glyph-num restarts inside each segment, so line+glyph alone is NOT unique
    (278 lines have repeated glyph-nums). seg-num must be carried.
    """
    s = d["img"][:-4] if d["img"].endswith(".png") else         "%s%s%s%s-%s" % (d["tab"], d["side"], d["line"], d["seg"], d["gnum"])
    if d["part"][1] > 1:
        s += "/%d.%d" % d["part"]
    return s


def gid(d):
    return (d["tab"], d["side"], d["line"], d["seg"], d["gnum"])


allruns = []
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    r = object_runs_prov(path)
    if sum(len(x) for x in r) >= 100:
        allruns.extend(r)

print("objects kept:", len(set(r[0]["tab"] for r in allruns)),
      "| runs:", len(allruns),
      "| tokens:", sum(len(r) for r in allruns), file=out)

for code in ["1", "381", "63", "70", "17", "280", "11", "102"]:
    print("\n" + "=" * 92, file=out)
    print("%s  (Horley %s)" % (TARGETS[code], code), file=out)
    print("=" * 92, file=out)
    n = 0
    for r in allruns:
        for i in range(len(r) - 3):
            a, b = r[i], r[i + 1]
            if r[i]["t"] == r[i + 2]["t"] and b["t"] == r[i + 3]["t"] and a["t"] != b["t"]:
                if code not in (a["t"], b["t"]):
                    continue
                n += 1
                lo, hi = max(0, i - 3), min(len(r), i + 7)
                print("\n  event %d  --  %s ... %s" % (n, ref(r[lo]), ref(r[hi - 1])), file=out)
                print("    %-16s %-10s %-8s %s" % ("CEIPP glyph id", "code", "Horley", "in ABAB window"), file=out)
                for j in range(lo, hi):
                    d = r[j]
                    mark = "  <ABAB>" if i <= j <= i + 3 else ""
                    print("    %-16s %-10s %-8s %s" % (ref(d), d["ceipp"], d["t"], mark.strip()), file=out)
    if n == 0:
        print("  no ABAB events", file=out)
    else:
        print("\n  total window hits: %d" % n, file=out)
out.flush()


# --- Corpus-wide: how many ABAB events exist only because Horley's map splits
# --- one physical glyph into two tokens? (Davletshin, 27 Aug: "transliteration
# --- issues or something else". Applying the paper's own question to my own count.)
print("\n\n" + "=" * 92, file=out)
print("ABAB EVENTS THAT DEPEND ON LIGATURE DECOMPOSITION (whole corpus)", file=out)
print("=" * 92, file=out)
tot = 0; art = 0; partial = 0
from collections import Counter
by_glyphs = Counter()
examples = []
for r in allruns:
    for i in range(len(r) - 3):
        a, b = r[i], r[i + 1]
        if a["t"] == r[i + 2]["t"] and b["t"] == r[i + 3]["t"] and a["t"] != b["t"]:
            tot += 1
            ids = set(gid(d) for d in r[i:i + 4])
            by_glyphs[len(ids)] += 1
            if len(ids) <= 2:
                art += 1
                if len(examples) < 8:
                    examples.append((ref(r[i]), [(d["ceipp"], d["t"]) for d in r[i:i + 4]]))
            elif len(ids) == 3:
                partial += 1
print("  total ABAB events: %d" % tot, file=out)
for k in sorted(by_glyphs):
    print("    spanning %d physical glyph(s): %5d  (%.1f%%)" % (k, by_glyphs[k], 100.0 * by_glyphs[k] / tot), file=out)
print("  events from <=2 physical glyphs (pure decomposition artefact): %d (%.1f%%)"
      % (art, 100.0 * art / tot), file=out)
print("  events from 3 physical glyphs (one member split): %d (%.1f%%)"
      % (partial, 100.0 * partial / tot), file=out)
print("\n  first examples of the <=2-glyph kind:", file=out)
for rf, toks in examples:
    print("    %-20s %s" % (rf, " ".join("%s->%s" % (c, t) for c, t in toks)), file=out)
out.flush()


# --- Per-sign version of the same audit. The corpus-wide 17 % above says nothing
# --- about whether any ONE sign's rate survives, and the two syllabic signs are
# --- the ones the argument rests on. An event is counted as real for a sign only
# --- when its four slots are four distinct physical glyphs on the object.
print("\n\n" + "=" * 92, file=out)
print("PER-SIGN ABAB, RAW vs LIGATURE-CORRECTED", file=out)
print("=" * 92, file=out)
raw = Counter(); real = Counter(); toks = Counter()
for r in allruns:
    for d in r:
        toks[d["t"]] += 1
    for i in range(len(r) - 3):
        a, b = r[i], r[i + 1]
        if a["t"] == r[i + 2]["t"] and b["t"] == r[i + 3]["t"] and a["t"] != b["t"]:
            four = len(set(gid(d) for d in r[i:i + 4])) == 4
            for t in (a["t"], b["t"]):
                raw[t] += 1
                if four:
                    real[t] += 1

# The corrected observation gets a corrected median, not the raw one: comparing a
# cleaned numerator against a dirty reference is the asymmetric comparison this
# paper is about.
elig = [t for t in toks if toks[t] >= 50]
med_raw = sorted(100.0 * raw.get(t, 0) / toks[t] for t in elig)[len(elig) // 2]
med_real = sorted(100.0 * real.get(t, 0) / toks[t] for t in elig)[len(elig) // 2]
print("  types with >=50 tokens: %d | median per100  raw %.2f  corrected %.2f"
      % (len(elig), med_raw, med_real), file=out)

order_raw = sorted(toks, key=lambda t: (-raw.get(t, 0), -toks[t]))
order_real = sorted(toks, key=lambda t: (-real.get(t, 0), -toks[t]))
rk_raw = {t: i + 1 for i, t in enumerate(order_raw)}
rk_real = {t: i + 1 for i, t in enumerate(order_real)}

print("\n  %-6s %7s | %5s %7s %6s | %5s %7s %6s" %
      ("sign", "tokens", "raw", "per100", "rank", "corr", "per100", "rank"), file=out)
shown = order_real[:15]
for t in shown + [x for x in ("1", "381", "200") if x not in shown]:
    print("  %-6s %7d | %5d %7.2f %6s | %5d %7.2f %6s" %
          (t, toks[t], raw.get(t, 0), 100.0 * raw.get(t, 0) / toks[t], rk_raw[t],
           real.get(t, 0), 100.0 * real.get(t, 0) / toks[t], rk_real[t]), file=out)

print("\n  Davletshin's two syllabic signs against the corrected median:", file=out)
for t, lab in (("1", "*Staff = ki"), ("381", "Sitting Man = ka")):
    r = 100.0 * real.get(t, 0) / toks[t]
    print("    %-6s %-18s corrected %.2f per 100 = %.2fx the corrected median (%.2f)"
          % (t, lab, r, r / med_real, med_real), file=out)
r200 = 100.0 * real.get("200", 0) / toks["200"]
print("    %-6s %-18s corrected %.2f per 100 = %.2fx  <- the code the paper used"
      % ("200", "(not *Staff)", r200, r200 / med_real), file=out)
out.flush()
