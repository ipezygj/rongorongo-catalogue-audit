"""Mixed logographic + syllabic decipherment, calibrated.

Units. Each glyph maps to one UNIT: a syllable (55) or a word from a Rapa Nui
lexicon (the W most frequent multi-syllable words of the NT text, plus the
moon/night candidates po, mahina, marama, hina). A word unit expands to its
syllable string.

Score. Syllable-bigram LM over the expanded stream, but every LM term is
measured RELATIVE to the LM's mean per-syllable log-prob on held-out Rapa Nui
(mu). Without that, a k-syllable logogram would lose by construction (k
negative terms instead of one) or win by construction (internal predictability
of a fixed word); with it, a logogram wins only where its syllables AND its
context are more Rapa-Nui-like than average text. Plus the channel term of
decipher.py (charges homophony). Search: Metropolis over unit reassignments,
annealing, restarts.

Calibration.
  control M  held-out Rapa Nui where the 30 most frequent multi-syllable words
             are each replaced by a private logogram symbol and every remaining
             syllable by a private syllable symbol (~85 cipher symbols, mixed
             like the hypothesis). Recovery = share of glyph tokens whose unit
             is exactly right. And its shuffle.
  then       rongorongo (Horley 125), its shuffles, Linear B (95).
  report     gaps; what glyph 040 (crescent) and the frequent glyphs choose;
             share of glyph tokens read as logograms.
"""
import math, random, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
import decipher as D
from horley import read_lines, tokens_horley, reshuffle, horley_lookup

rng = random.Random(20260816)
W_WORDS = 200
STEPS = 300000
RESTARTS = 4
RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
MOON = ["po", "mahina", "marama", "hina"]


def words_and_lexicon(rap_txt, held_frac=0.2):
    """Return (train_runs, held_runs) as syllable runs, held_words as list of
    per-verse word lists (each word = list of syllables), and lexicon."""
    txt = re.sub(r"Currently Selected:.*?\d", " ", rap_txt)
    verses = re.split(r"[.;:!?]", txt)
    verse_words = []
    for v in verses:
        ws = []
        for w in re.findall(r"[^\s\d«»¿¡()\"“”—\-,]+", v):
            s = D.S.syllabify(w, RAP_C, True)
            s = [t for r in s for t in r]
            if s:
                ws.append(s)
        if ws:
            verse_words.append(ws)
    cut = int(len(verse_words) * (1 - held_frac))
    train_vw, held_vw = verse_words[:cut], verse_words[cut:]
    train_runs = [[t for w in vw for t in w] for vw in train_vw]
    held_runs = [[t for w in vw for t in w] for vw in held_vw]
    wc = Counter(tuple(w) for vw in train_vw for w in vw if len(w) >= 2)
    lex = [list(w) for w, _ in wc.most_common(W_WORDS)]
    for m in MOON:
        s = [t for r in D.S.syllabify(m, RAP_C, True) for t in r]
        if len(s) >= 2 and s not in lex:
            lex.append(s)
    return train_runs, held_runs, train_vw, held_vw, lex


class Units:
    def __init__(self, syl, idx, lex, logbi, logstart, mu, lam=0.0):
        self.lam = lam
        self.names = list(syl) + ["".join(w) for w in lex]
        self.first, self.last, self.internal, self.length = [], [], [], []
        for s in syl:
            i = idx[s]
            self.first.append(i)
            self.last.append(i)
            self.internal.append(0.0)
            self.length.append(1)
        for w in lex:
            ids = [idx[t] for t in w]
            self.first.append(ids[0])
            self.last.append(ids[-1])
            self.internal.append(sum(logbi[a][b] - mu for a, b in zip(ids, ids[1:])))
            self.length.append(len(ids))
        self.U = len(self.names)
        self.nsyl = len(syl)
        self.logbi, self.logstart, self.mu = logbi, logstart, mu

    def trans(self, u, v):
        return self.logbi[self.last[u]][self.first[v]] - self.mu

    def start(self, u):
        return self.logstart[self.first[u]] - self.mu


def total(m, st, un):
    types, cidx, G, out, inn, selfc, startc, unic = st
    N = [0] * un.U
    for g, u in enumerate(m):
        N[u] += unic[g]
    s = sum(unic[g] * math.log(unic[g]) for g in range(G) if unic[g] > 0) + sum(D.chan_class(x) for x in N)
    for g in range(G):
        u = m[g]
        s += unic[g] * (un.internal[u] - (un.lam if u >= un.nsyl else 0.0)) + startc[g] * un.start(u) + selfc[g] * un.trans(u, u)
        for h, n in out[g]:
            s += n * un.trans(u, m[h])
    return s, N


def delta(m, g, new, st, un, N):
    types, cidx, G, out, inn, selfc, startc, unic = st
    old = m[g]
    n = unic[g]
    d = (D.chan_class(N[old] - n) - D.chan_class(N[old])) + (D.chan_class(N[new] + n) - D.chan_class(N[new]))
    d += n * ((un.internal[new] - (un.lam if new >= un.nsyl else 0.0)) - (un.internal[old] - (un.lam if old >= un.nsyl else 0.0)))
    d += startc[g] * (un.start(new) - un.start(old))
    d += selfc[g] * (un.trans(new, new) - un.trans(old, old))
    for h, k in out[g]:
        d += k * (un.trans(new, m[h]) - un.trans(old, m[h]))
    for h, k in inn[g]:
        d += k * (un.trans(m[h], new) - un.trans(m[h], old))
    return d


def search(st, un, rng, steps=STEPS, clamp=None):
    types, cidx, G, out, inn, selfc, startc, unic = st
    m = [rng.randrange(un.U) for _ in range(G)]
    if clamp:
        m[clamp[0]] = clamp[1]
    cur, N = total(m, st, un)
    best, bestm = cur, m[:]
    T0, T1 = 5.0, 0.05
    for t in range(steps):
        T = T0 * (T1 / T0) ** (t / steps)
        g = rng.randrange(G)
        if clamp and g == clamp[0]:
            continue
        new = rng.randrange(un.U)
        if new == m[g]:
            continue
        d = delta(m, g, new, st, un, N)
        if d >= 0 or rng.random() < math.exp(d / T):
            N[m[g]] -= unic[g]
            N[new] += unic[g]
            m[g] = new
            cur += d
            if cur > best:
                best, bestm = cur, m[:]
    return best, bestm


def experiment(name, runs, un, rng, truth=None, p=print):
    st = D.cipher_stats(runs)
    types, cidx, G, out, inn, selfc, startc, unic = st
    ntok = sum(unic)
    res = [search(st, un, rng) for _ in range(RESTARTS)]
    res.sort(key=lambda x: -x[0])
    best, bm = res[0]
    logo_tok = sum(unic[g] for g in range(G) if bm[g] >= un.nsyl) / ntok
    votes = {g: Counter(m[g] for _b, m in res) for g in range(G)}
    agree = sum(unic[g] * votes[g].most_common(1)[0][1] / RESTARTS for g in range(G)) / ntok
    line = "%-26s score/tok %+.4f  restarts %s  logogram share %.0f%%  agreement %.2f" % (
        name, best / ntok, " ".join("%+.4f" % (b / ntok) for b, _m in res), logo_tok * 100, agree)
    if truth is not None:
        ok = sum(unic[g] for g in range(G) if un.names[bm[g]] == truth[types[g]])
        okl = sum(unic[g] for g in range(G) if un.names[bm[g]] == truth[types[g]] and bm[g] >= un.nsyl)
        line += "  UNIT ACCURACY %.1f%% (logograms right %.1f%% of tokens)" % (ok / ntok * 100, okl / ntok * 100)
    p(line)
    return best / ntok, bm, st, votes


def main():
    out = []
    p = out.append
    rap_txt, _ = D.S.load_rap()
    train_runs, held_runs, train_vw, held_vw, lex = words_and_lexicon(rap_txt)
    syl, idx, logbi, logstart = D.build_lm(train_runs)
    V = len(syl)
    # mu = mean per-syllable LL on held-out
    tot = n = 0.0
    for r in held_runs:
        ids = [idx[t] for t in r if t in idx]
        if not ids:
            continue
        tot += logstart[ids[0]]
        n += 1
        for a, b in zip(ids, ids[1:]):
            tot += logbi[a][b]
            n += 1
    mu = tot / n
    un = Units(syl, idx, lex, logbi, logstart, mu)
    p("LM: %d syllables, train %d syl; held-out %d syl; mu = %.4f; lexicon %d words (+syllables = %d units)"
      % (V, sum(map(len, train_runs)), int(n), mu, len(lex), un.U))
    p("  lexicon head: %s" % " ".join(un.names[V:V + 25]))

    lines = read_lines()
    horl = [r for s in lines for r in tokens_horley(s)]
    rr_lengths = [len(r) for r in horl]
    n_rr = sum(rr_lengths)

    def recut(runs, lengths, rng):
        flat = [t for r in runs for t in r]
        lens = lengths[:]
        rng.shuffle(lens)
        o, i = [], 0
        for L_ in lens:
            if i >= len(flat):
                break
            o.append(flat[i:i + L_])
            i += L_
        return o

    p("")
    p("=" * 100)
    p("CALIBRATION: control M = held-out Rapa Nui, 30 frequent words as logogram symbols, rest syllable symbols")
    p("=" * 100)
    # build mixed cipher from held-out verse words
    logo_words = [tuple(w) for w in lex[:30]]
    logo_sym = {w: "L%d" % i for i, w in enumerate(logo_words)}
    syl_sym = {s: "S%d" % i for i, s in enumerate(syl)}
    truth = {}
    stream = []
    for vw in held_vw:
        run = []
        for w in vw:
            tw = tuple(w)
            if tw in logo_sym:
                run.append(logo_sym[tw])
                truth[logo_sym[tw]] = "".join(w)
            else:
                for s in w:
                    run.append(syl_sym[s])
                    truth[syl_sym[s]] = s
        if run:
            stream.append(run)
    # window to rongorongo size (in glyph tokens), then recut to rongorongo run lengths
    win = D.S.sample_runs(stream, n_rr, rng)
    ctrlM = recut(win, rr_lengths, rng)
    ntokM = sum(map(len, ctrlM))
    logo_share_true = sum(1 for r in ctrlM for t in r if t.startswith("L")) / ntokM
    p("  control M: %d glyph tokens, %d symbols, true logogram share %.0f%%" % (ntokM, len(set(t for r in ctrlM for t in r)), logo_share_true * 100))
    p("  lambda calibration on control M (2 restarts x 150k each):")
    global STEPS, RESTARTS
    S0, R0 = STEPS, RESTARTS
    STEPS, RESTARTS = 150000, 2
    best_lam, best_acc = None, -1
    for lam in [0.0, 1.0, 2.0, 3.0, 4.0, 6.0]:
        un.lam = lam
        _ll, _m, _st, _v = experiment("    lambda=%.1f" % lam, ctrlM, un, rng, truth=truth, p=p)
        types_, cidx_, G_, o_, i_, sc_, stc_, unic_ = _st
        acc = sum(unic_[g] for g in range(G_) if un.names[_m[g]] == truth[types_[g]]) / sum(unic_)
        if acc > best_acc:
            best_acc, best_lam = acc, lam
    STEPS, RESTARTS = S0, R0
    un.lam = best_lam
    p("  chosen lambda = %.1f (unit accuracy %.1f%%); used unchanged for everything below" % (best_lam, best_acc * 100))
    llM, mM, stM, _ = experiment("control M (mixed cipher)", ctrlM, un, rng, truth=truth, p=p)
    llMs, _, _, _ = experiment("control M shuffled", reshuffle(ctrlM, rng), un, rng, p=p)
    p("  gap = %+.4f" % (llM - llMs))

    p("")
    p("=" * 100)
    p("RONGORONGO (Horley 125) UNDER THE MIXED MODEL")
    p("=" * 100)
    llR, mR, stR, votesR = experiment("rongorongo real", horl, un, rng, p=p)
    nulls = [experiment("rongorongo shuffled #%d" % (i + 1), reshuffle(horl, rng), un, rng, p=p)[0] for i in range(2)]
    linb = D.S.load_linb()
    wl = recut(D.S.sample_runs(linb, n_rr, rng), rr_lengths, rng)
    llL, _, _, _ = experiment("Linear B", wl, un, rng, p=p)
    llLs, _, _, _ = experiment("Linear B shuffled", reshuffle(wl, rng), un, rng, p=p)
    p("")
    p("  gaps: control M %+.4f | rongorongo %+.4f | Linear B %+.4f" % (llM - llMs, llR - sum(nulls) / len(nulls), llL - llLs))

    p("")
    p("=" * 100)
    p("WHAT THE FREQUENT GLYPHS AND THE CRESCENT CHOOSE (best mapping; votes over %d restarts)" % RESTARTS)
    p("=" * 100)
    types, cidx, G, outg, inn, selfc, startc, unic = stR
    order = sorted(range(G), key=lambda g: -unic[g])[:20]
    h40 = horley_lookup("040")[0]
    if cidx[h40] not in order:
        order.append(cidx[h40])
    for g in order:
        top = votesR[g].most_common(3)
        p("  glyph %-5s n=%-5d best: %-8s  votes: %s" % (types[g], unic[g], un.names[mR[g]],
          ", ".join("%s(%d)" % (un.names[u], c) for u, c in top)))
    # crescent clamp: force 040 to each moon word / po and compare
    p("")
    p("  crescent 040 clamped:")
    base = llR
    for cand in ["po", "mahina", "marama", "hina", "te", "ka"]:
        if cand in un.names:
            u = un.names.index(cand)
            b = max(search(stR, un, rng, steps=150000, clamp=(cidx[h40], u))[0] for _ in range(2))
            p("    040 = %-7s score/tok %+.4f (unclamped best %+.4f)" % (cand, b / n_rr, base))
    txt = "\n".join(out)
    print(txt)
    open("mixed_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
