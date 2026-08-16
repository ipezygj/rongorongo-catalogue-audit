"""Let the corpus vote on the catalogue, using its own repeated passages.

The same text recurs on different objects in slightly different spellings. Where
two versions of a passage differ at a single position, the two signs standing in
that slot are candidates for being the same sign written differently. That is
the one place in an undeciphered corpus where the artefacts themselves say which
glyphs are interchangeable, and it is how Pozdniakov reduced Barthel's six
hundred by hand in 1996.

Method is seed-and-extend, as in sequence search. Exact k-mers shared between
lines on DIFFERENT objects are the seeds -- same-object repeats are excluded
because a scribe repeating himself on one tablet is not independent evidence.
Seeded line pairs are then aligned with difflib and every one-for-one mismatch
is recorded as a substitution.

A catalogue is then scored on how many of those substitutions it absorbs, i.e.
how often it puts the two signs in one class. Absorption alone proves nothing:
a catalogue that merges everything absorbs everything. The comparison is against
random catalogues of the same size, so what counts is absorption above chance.
"""
import difflib
import glob
import io
import math
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
XMLDIR = os.path.join(HERE, "ceipp", "xml")
IS_GLYPH = re.compile(r"^\d")
K = 5              # seed length; a chance 5-run over 633 types is negligible
MIN_RUN = 4        # ignore alignments whose matched blocks are trivially short
N_RANDOM = 300
SEED = 20260815

_ns = {}
exec(io.open(os.path.join(HERE, "rongopy", "horley_encoding.py"),
             encoding="utf-8").read(), _ns)
HORLEY = _ns["horley_encoding"]


def read_lines():
    """(object, [base-numeric tokens]) per inscribed line."""
    out = []
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        obj = os.path.splitext(os.path.basename(path))[0]
        root = ET.parse(path).getroot()
        for line in root.iter("line"):
            toks = []
            for g in line.iter("glyph"):
                code = (g.findtext("code/ceipp") or "").strip()
                if IS_GLYPH.match(code):
                    toks.append(re.match(r"^(\d+)",
                                         code.replace("!", "")).group(1))
            if len(toks) >= K:
                out.append((obj, toks))
    return out


def find_substitutions(lines):
    """Seed on shared k-mers across objects, align, collect 1-1 mismatches."""
    index = defaultdict(set)
    for i, (_obj, toks) in enumerate(lines):
        for p in range(len(toks) - K + 1):
            index[tuple(toks[p:p + K])].add(i)

    pairs = set()
    for _kmer, hits in index.items():
        if len(hits) < 2:
            continue
        hits = sorted(hits)
        for a in range(len(hits)):
            for b in range(a + 1, len(hits)):
                i, j = hits[a], hits[b]
                if lines[i][0] != lines[j][0]:      # different objects only
                    pairs.add((i, j))

    subs = Counter()
    aligned = 0
    for i, j in sorted(pairs):
        A, B = lines[i][1], lines[j][1]
        sm = difflib.SequenceMatcher(a=A, b=B, autojunk=False)
        blocks = [bl for bl in sm.get_matching_blocks() if bl.size >= MIN_RUN]
        if not blocks:
            continue
        aligned += 1
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "replace" and (i2 - i1) == 1 and (j2 - j1) == 1:
                x, y = A[i1], B[j1]
                if x != y:
                    subs[tuple(sorted((x, y)))] += 1
    return pairs, aligned, subs


def horley_class(code):
    if code in HORLEY:
        parts = str(HORLEY[code]).split()
        return None if any(p == "?" for p in parts) else " ".join(parts)
    return None


def absorbed(subs, classify):
    """Share of substitution EVENTS the mapping puts into one class."""
    hit = tot = 0
    for (x, y), n in subs.items():
        cx, cy = classify(x), classify(y)
        if cx is None or cy is None:
            continue
        tot += n
        if cx == cy:
            hit += n
    return hit, tot


def main():
    lines = read_lines()
    objs = len({o for o, _ in lines})
    print(f"{len(lines)} lines over {objs} objects, k = {K}")

    pairs, aligned, subs = find_substitutions(lines)
    print(f"cross-object seeded line pairs : {len(pairs)}")
    print(f"  with a real matched block    : {aligned}")
    print(f"  distinct substitution pairs  : {len(subs)}")
    print(f"  substitution events          : {sum(subs.values())}")
    print(f"  most frequent                : {subs.most_common(8)}")

    if not subs:
        print("no substitutions found; nothing to score")
        return

    signs = sorted({s for pair in subs for s in pair})
    print(f"  signs involved               : {len(signs)}")

    print()
    print("=" * 74)
    print("DOES A CATALOGUE ABSORB WHAT THE CORPUS SUBSTITUTES?")
    print("=" * 74)

    hit, tot = absorbed(subs, horley_class)
    print(f"  Horley (L=125)   absorbs {hit}/{tot} events = "
          f"{hit / tot * 100:.1f} %   (of events it can classify)")

    # Random catalogues of the same size, over the same sign inventory.
    all_signs = sorted({t for _o, toks in lines for t in toks})
    rng = random.Random(SEED)
    vals = []
    for _ in range(N_RANDOM):
        assign = {s: rng.randrange(125) for s in all_signs}
        h, t = absorbed(subs, lambda s: assign.get(s))
        vals.append(h / t if t else 0.0)
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
    print(f"  random L=125     absorbs {m*100:.1f} % +- {sd*100:.1f}    "
          f"(range {min(vals)*100:.1f} .. {max(vals)*100:.1f})")

    z = (hit / tot - m) / sd if sd else float("nan")
    print()
    print(f"  Horley is {z:.1f} sd above chance")
    print()
    if z > 3:
        print("  => the corpus's own spelling variation supports the published")
        print("     reduction: signs the scribes interchanged do land together.")
    else:
        print("  => the published reduction absorbs no more of the corpus's own")
        print("     spelling variation than an arbitrary grouping of the same size.")


if __name__ == "__main__":
    main()
