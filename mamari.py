"""Mamari lunar calendar (tablet C, side a, lines 6-9; Guy 1990) as an anchor.

What the calendar gives: crescent glyph 040 repeated in groups (the nights),
a heralding sequence 390.041-378-041-670-008.078.711 repeated eight times, and
the full-moon glyph 152 near the middle. It does NOT give thirty distinct
night-name spellings: most nights are bare crescents. So the anchor is weak,
and this script measures exactly how weak.

Tests
 1. Structure check: count crescents, heralds, full moon in Ca6-Ca9.
 2. Clamp test: fix glyph 040 to each of the 55 syllables in turn, run the
    global decipherer (decipher.py) with the clamp, rank syllables by the
    corpus likelihood. If the calendar's obvious meaning ('night' = po,
    'moon' = mahina/marama) has any syllabic footprint, po/ma/hi should rank
    high; if 040 is a logogram, the ranking should look like noise and the
    LL spread across clamps should be small.
 3. Herald reading: what the eight-times sequence reads as under the best
    unconstrained mapping, and how the LM scores it against random
    8-syllable strings drawn from the same mapping.
"""
import math, random, sys
import xml.etree.ElementTree as ET
from collections import Counter
sys.path.insert(0, ".")
import decipher as D
from horley import read_lines, tokens_horley, horley_lookup

rng = random.Random(20260816)
STEPS = 120000
RESTARTS = 3


def calendar_seq():
    root = ET.parse("ceipp/xml/C.xml").getroot()
    seq = []
    for side in root.iter("side"):
        if side.findtext("side-code") != "a":
            continue
        for line in side.iter("line"):
            if line.findtext("line-code") not in ("06", "07", "08", "09"):
                continue
            for g in line.iter("glyph"):
                c = (g.findtext("code/ceipp") or "").strip()
                if c:
                    seq.append(c)
    return seq


def search_clamped(st, V, logbi, logstart, rng, clamp, steps):
    """decipher.search with one glyph index fixed."""
    types, cidx, G, out, inn, selfc, startc, unic = st
    gfix, sfix = clamp
    m = [rng.randrange(V) for _ in range(G)]
    m[gfix] = sfix
    cur = D.total_score(m, st, logbi, logstart)
    N = D.class_totals(m, st, V)
    best, bestm = cur, m[:]
    T0, T1 = 5.0, 0.05
    for t in range(steps):
        T = T0 * (T1 / T0) ** (t / steps)
        g = rng.randrange(G)
        if g == gfix:
            continue
        new = rng.randrange(V)
        if new == m[g]:
            continue
        d = D.delta_score(m, g, new, st, logbi, logstart, N)
        if d >= 0 or rng.random() < math.exp(d / T):
            N[m[g]] -= unic[g]
            N[new] += unic[g]
            m[g] = new
            cur += d
            if cur > best:
                best, bestm = cur, m[:]
    return best, bestm


def main():
    out = []
    p = out.append
    seq = calendar_seq()
    c = Counter(seq)
    p("Ca6-Ca9: %d coded glyphs, %d types" % (len(seq), len(c)))
    p("  crescents 040: %d   041: %d   full moon 152: %d   heralds (390): %d   fish 711: %d   700: %d"
      % (c["040"], c["041"], c["152"], c["390"], c["711"], c["700"]))
    # crescent groups between heralds
    groups, cur = [], 0
    for x in seq:
        if x == "390":
            groups.append(cur)
            cur = 0
        elif x.startswith("040"):
            cur += 1
    groups.append(cur)
    p("  crescents per segment (split at herald 390): %s  sum %d" % (groups, sum(groups)))
    # glyphs that sit next to crescents other than heralds
    extra = Counter()
    for i, x in enumerate(seq):
        if x.startswith("040"):
            for j in (i - 1, i + 1):
                if 0 <= j < len(seq) and not seq[j].startswith("040") and seq[j] not in ("390", "041", "378", "378y", "670", "670y", "008", "078", "711"):
                    extra[seq[j]] += 1
    p("  non-herald glyphs adjacent to crescents: %s" % dict(extra.most_common(12)))

    # ---- global model
    rap_txt, _ = D.S.load_rap()
    rap = D.S.syllabify(rap_txt, ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"], True)
    cut = int(len(rap) * 0.8)
    syl, idx, logbi, logstart = D.build_lm(rap[:cut])
    V = len(syl)
    lines = read_lines()
    horl = [r for s in lines for r in tokens_horley(s)]
    st = D.cipher_stats(horl)
    types, cidx, G, outg, inn, selfc, startc, unic = st
    ntok = sum(unic)
    h40 = horley_lookup("040")
    p("  Horley class of 040: %s ; corpus count %d ; of 041: %s ; of 152: %s" % (h40, unic[cidx[h40[0]]] if h40 else -1, horley_lookup("041"), horley_lookup("152")))
    g40 = cidx[h40[0]]

    p("")
    p("=" * 90)
    p("CLAMP TEST: glyph 040 fixed to each syllable, best corpus LL/token (%d restarts x %dk steps)" % (RESTARTS, STEPS // 1000))
    p("=" * 90)
    scores = []
    for s_i in range(V):
        best = max(search_clamped(st, V, logbi, logstart, rng, (g40, s_i), STEPS)[0] for _ in range(RESTARTS))
        scores.append((best / ntok, syl[s_i]))
        print("clamp %-4s %.4f" % (syl[s_i], best / ntok), flush=True)
    scores.sort(reverse=True)
    top = scores[0][0]
    bot = scores[-1][0]
    p("  spread top-bottom: %.4f LL/token (%.1f nats over the whole corpus)" % (top - bot, (top - bot) * ntok))
    for i, (v, s_) in enumerate(scores):
        mark = "  <-- po (night)" if s_ == "po" else "  <-- ma (mahina/marama)" if s_ == "ma" else "  <-- hi (hina)" if s_ == "hi" else ""
        p("  %2d. %-4s %.4f%s" % (i + 1, s_, v, mark))

    p("")
    p("=" * 90)
    p("HERALD READING under best unconstrained mapping (3 restarts)")
    p("=" * 90)
    bestm = None
    bestv = -1e18
    for _ in range(3):
        b, m = D.search(st, V, logbi, logstart, rng, steps=300000)
        if b > bestv:
            bestv, bestm = b, m
    herald = ["390", "041", "378", "041", "670", "008", "078", "711"]
    hs = []
    for code in herald:
        parts = horley_lookup(code) or ["?"]
        hs.extend(parts)
    reading = [syl[bestm[cidx[x]]] if x in cidx else "?" for x in hs]
    p("  herald glyphs (Horley): %s" % " ".join(hs))
    p("  reads as             : %s" % " ".join(reading))
    # LM score of that string vs random strings of same length from the mapping's syllable marginal
    def lm_score(ids):
        s = logstart[ids[0]]
        for a, b in zip(ids, ids[1:]):
            s += logbi[a][b]
        return s
    ids = [idx[x] for x in reading if x in idx]
    real = lm_score(ids)
    marg = [bestm[g] for g in range(G) for _ in range(unic[g])]
    rs = [lm_score([rng.choice(marg) for _ in ids]) for _ in range(2000)]
    mu = sum(rs) / len(rs)
    sd = math.sqrt(sum((x - mu) ** 2 for x in rs) / (len(rs) - 1))
    p("  LM log-prob of herald reading %.2f vs random same-length strings %.2f +- %.2f  (z = %.1f)" % (real, mu, sd, (real - mu) / sd))
    txt = "\n".join(out)
    print(txt)
    open("mamari_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
