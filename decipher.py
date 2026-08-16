"""A calibrated Bayesian decipherment attempt: glyph -> Rapa Nui syllable.

Model. A many-to-one mapping m: glyph -> syllable (125 Horley glyphs -> 55
Rapa Nui syllables, several glyphs may share one syllable). Score of the
corpus under m = sum over attested bigrams of log P_LM(m(a) -> m(b)) plus
unigram log-prob at run starts, where P_LM is an add-k bigram model of
syllabified Rapa Nui (Wycliffe NT, 323k syllables). Search: Metropolis over
single-glyph reassignments with annealing, R independent restarts. Posterior
uncertainty per glyph = how often restarts agree on its syllable.

Calibration BEFORE reading anything into rongorongo:
  control  real Rapa Nui syllable text, same token count and run lengths as
           rongorongo, enciphered by a random substitution (with homophones:
           each syllable split into 1-3 cipher symbols so the cipher has ~125
           symbols like Horley). Does the search recover it? (token accuracy)
  null     rongorongo shuffled (unigram-matched). Same search. If real
           rongorongo does not score better than its own shuffle, no mapping
           makes it Rapa Nui more than chance does.
"""
import math, random, sys
from collections import Counter, defaultdict
sys.path.insert(0, ".")
from horley import read_lines, tokens_horley, tokens_plain, reshuffle
import syllabary_ref as S

SEED = 20260816
rng = random.Random(SEED)
RESTARTS = 6
STEPS = 300000
K_SMOOTH = 0.5


# ---------------- language model ----------------
def build_lm(runs):
    syl = sorted(set(t for r in runs for t in r))
    idx = {s: i for i, s in enumerate(syl)}
    V = len(syl)
    uni = [0.0] * V
    bi = [[0.0] * V for _ in range(V)]
    starts = [0.0] * V
    for r in runs:
        ids = [idx[t] for t in r]
        starts[ids[0]] += 1
        for a in ids:
            uni[a] += 1
        for a, b in zip(ids, ids[1:]):
            bi[a][b] += 1
    logbi = [[0.0] * V for _ in range(V)]
    for a in range(V):
        tot = sum(bi[a]) + K_SMOOTH * V
        for b in range(V):
            logbi[a][b] = math.log((bi[a][b] + K_SMOOTH) / tot)
    tot = sum(starts) + K_SMOOTH * V
    logstart = [math.log((s + K_SMOOTH) / tot) for s in starts]
    return syl, idx, logbi, logstart


# ---------------- cipher-side statistics ----------------
def cipher_stats(runs):
    types = sorted(set(t for r in runs for t in r))
    cidx = {t: i for i, t in enumerate(types)}
    G = len(types)
    bic = Counter()
    startc = [0] * G
    unic = [0] * G
    for r in runs:
        ids = [cidx[t] for t in r]
        startc[ids[0]] += 1
        for a in ids:
            unic[a] += 1
        for a, b in zip(ids, ids[1:]):
            bic[(a, b)] += 1
    # adjacency lists for fast delta
    out = defaultdict(list)  # g -> [(h, n)] for bigram (g,h)
    inn = defaultdict(list)  # g -> [(h, n)] for bigram (h,g)
    selfc = [0] * G
    for (a, b), n in bic.items():
        if a == b:
            selfc[a] += n
        else:
            out[a].append((b, n))
            inn[b].append((a, n))
    return types, cidx, G, out, inn, selfc, startc, unic


def class_totals(m, st, V):
    unic = st[7]
    N = [0] * V
    for g, mg in enumerate(m):
        N[mg] += unic[g]
    return N


def chan_class(Ns):
    return -Ns * math.log(Ns) if Ns > 0 else 0.0


def total_score(m, st, logbi, logstart):
    """LM term + channel term. Channel: sum_g n_g log(n_g / N_{m(g)}), i.e. the
    MLE probability of emitting glyph g given its syllable class; the constant
    sum n_g log n_g is included so the score is comparable across mappings."""
    types, cidx, G, out, inn, selfc, startc, unic = st
    V = len(logstart)
    N = class_totals(m, st, V)
    s = sum(unic[g] * math.log(unic[g]) for g in range(G) if unic[g] > 0)
    s += sum(chan_class(x) for x in N)
    for g in range(G):
        mg = m[g]
        s += startc[g] * logstart[mg]
        s += selfc[g] * logbi[mg][mg]
        for h, n in out[g]:
            s += n * logbi[mg][m[h]]
    return s


def delta_score(m, g, new, st, logbi, logstart, N):
    types, cidx, G, out, inn, selfc, startc, unic = st
    old = m[g]
    n = unic[g]
    d = (chan_class(N[old] - n) - chan_class(N[old])) + (chan_class(N[new] + n) - chan_class(N[new]))
    d += startc[g] * (logstart[new] - logstart[old])
    d += selfc[g] * (logbi[new][new] - logbi[old][old])
    for h, n in out[g]:
        mh = m[h]
        d += n * (logbi[new][mh] - logbi[old][mh])
    for h, n in inn[g]:
        mh = m[h]
        d += n * (logbi[mh][new] - logbi[mh][old])
    return d


def search(st, V, logbi, logstart, rng, steps=STEPS, init=None):
    types, cidx, G, out, inn, selfc, startc, unic = st
    m = list(init) if init else [rng.randrange(V) for _ in range(G)]
    cur = total_score(m, st, logbi, logstart)
    N = class_totals(m, st, V)
    best, bestm = cur, m[:]
    T0, T1 = 5.0, 0.05
    for t in range(steps):
        T = T0 * (T1 / T0) ** (t / steps)
        g = rng.randrange(G)
        new = rng.randrange(V)
        if new == m[g]:
            continue
        d = delta_score(m, g, new, st, logbi, logstart, N)
        if d >= 0 or rng.random() < math.exp(d / T):
            N[m[g]] -= unic[g]
            N[new] += unic[g]
            m[g] = new
            cur += d
            if cur > best:
                best, bestm = cur, m[:]
    return best, bestm


def freq_init(st, V, uni_lm_order, rng):
    """Frequency-rank initialisation: most frequent glyph -> most frequent syllable, with noise."""
    types, cidx, G, out, inn, selfc, startc, unic = st
    order = sorted(range(G), key=lambda g: -unic[g])
    m = [0] * G
    for r, g in enumerate(order):
        m[g] = uni_lm_order[min(r, V - 1)] if r < V else uni_lm_order[rng.randrange(V)]
    return m


def run_experiment(name, runs, syl, idx, logbi, logstart, lm_uni_order, rng, truth=None):
    st = cipher_stats(runs)
    types = st[0]
    V = len(syl)
    ntok = sum(len(r) for r in runs)
    results = []
    for r in range(RESTARTS):
        init = freq_init(st, V, lm_uni_order, rng) if r % 2 == 0 else None
        best, m = search(st, V, logbi, logstart, rng, init=init)
        results.append((best, m))
    results.sort(key=lambda x: -x[0])
    best, bm = results[0]
    # agreement across restarts (posterior-width proxy), weighted by glyph frequency
    G = st[2]
    unic = st[7]
    agree_tok = 0
    for g in range(G):
        votes = Counter(m[g] for _b, m in results)
        top = votes.most_common(1)[0][1]
        agree_tok += unic[g] * (top / RESTARTS)
    agree = agree_tok / ntok
    line = "%-22s LL/token %.4f  restarts %s  agreement(token-weighted) %.2f" % (
        name, best / ntok, " ".join("%.4f" % (b / ntok) for b, _m in results), agree)
    acc = None
    if truth is not None:
        correct = sum(unic[g] for g in range(G) if syl[bm[g]] == truth[types[g]])
        acc = correct / ntok
        line += "  TOKEN ACCURACY %.1f%%" % (acc * 100)
    return line, best / ntok, bm, st, agree, acc


def main():
    out = []
    p = out.append
    rap_txt, _ = S.load_rap()
    RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
    rap = S.syllabify(rap_txt, RAP_C, True)
    # hold out a slice for the control so the LM never sees the control text
    cut = int(len(rap) * 0.8)
    lm_runs, held = rap[:cut], rap[cut:]
    syl, idx, logbi, logstart = build_lm(lm_runs)
    V = len(syl)
    lm_uni = Counter(t for r in lm_runs for t in r)
    lm_uni_order = [idx[s] for s, _ in lm_uni.most_common()]
    p("Rapa Nui LM: %d syllables, %d train tokens; held-out %d tokens" % (V, sum(len(r) for r in lm_runs), sum(len(r) for r in held)))

    lines = read_lines()
    horl = [r for s in lines for r in tokens_horley(s)]
    rr_lengths = [len(r) for r in horl]
    n_rr = sum(rr_lengths)
    p("rongorongo (Horley): %d tokens, %d glyph types, %d runs" % (n_rr, len(set(t for r in horl for t in r)), len(horl)))

    # true Rapa Nui held-out at same N and run lengths: LL/token ceiling under identity mapping
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
    win = S.sample_runs(held, n_rr, rng)
    ctrl_plain = recut(win, rr_lengths, rng)
    st_plain = cipher_stats(ctrl_plain)
    ident = [idx[t] for t in st_plain[0]]
    ceiling = total_score(ident, st_plain, logbi, logstart) / sum(len(r) for r in ctrl_plain)
    p("ceiling: held-out Rapa Nui under the TRUE mapping: LL/token %.4f" % ceiling)

    p("")
    p("=" * 100)
    p("CALIBRATION")
    p("=" * 100)
    # control A: simple substitution, 55 symbols
    subst = {s: "c%d" % i for i, s in enumerate(rng.sample(syl, len(syl)))}
    ctrlA = [[subst[t] for t in r] for r in ctrl_plain]
    truthA = {v: k for k, v in subst.items()}
    line, llA, mA, stA, agA, accA = run_experiment("control A (1:1, 55)", ctrlA, syl, idx, logbi, logstart, lm_uni_order, rng, truth=truthA)
    p(line)
    # control B: homophonic, ~125 symbols (each syllable 1-3 cipher symbols, chosen by frequency)
    homo = {}
    k = 0
    for s in syl:
        nh = 1 + (2 if lm_uni[s] > 8000 else 1 if lm_uni[s] > 2000 else 0)
        homo[s] = ["h%d" % (k + j) for j in range(nh)]
        k += nh
    ctrlB = [[rng.choice(homo[t]) for t in r] for r in ctrl_plain]
    truthB = {c: s for s, cs in homo.items() for c in cs}
    line, llB, mB, stB, agB, accB = run_experiment("control B (homoph., %d)" % k, ctrlB, syl, idx, logbi, logstart, lm_uni_order, rng, truth=truthB)
    p(line)
    # control C: control B text but shuffled -> what does the search reach on structureless input?
    ctrlC = reshuffle(ctrlB, rng)
    line, llC, _m, _s, agC, _a = run_experiment("control C (B shuffled)", ctrlC, syl, idx, logbi, logstart, lm_uni_order, rng)
    p(line)

    p("")
    p("=" * 100)
    p("RONGORONGO (Horley 125 glyphs -> 55 Rapa Nui syllables)")
    p("=" * 100)
    line, llR, mR, stR, agR, _ = run_experiment("rongorongo real", horl, syl, idx, logbi, logstart, lm_uni_order, rng)
    p(line)
    nulls = []
    for i in range(3):
        line, llN, _m, _s, agN, _a = run_experiment("rongorongo shuffled #%d" % (i + 1), reshuffle(horl, rng), syl, idx, logbi, logstart, lm_uni_order, rng)
        p(line)
        nulls.append(llN)
    mu = sum(nulls) / len(nulls)
    sd = math.sqrt(sum((x - mu) ** 2 for x in nulls) / (len(nulls) - 1))
    p("")
    p("real - shuffled(mean) = %+.4f LL/token  (null sd %.4f, z = %.1f)" % (llR - mu, sd, (llR - mu) / sd if sd else float("nan")))

    p("")
    p("=" * 100)
    p("STRUCTURED NON-RAPA-NUI CONTROLS THROUGH THE SAME PIPE (N and run lengths matched)")
    p("=" * 100)
    linb = S.load_linb()
    mri_txt = S.load_mri()
    mri = S.syllabify(mri_txt, ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"], True)
    for nm, src in (("Linear B (95 signs)", linb), ("Maori syllables (52)", mri)):
        w = recut(S.sample_runs(src, n_rr, rng), rr_lengths, rng)
        line, llX, _m, _s, agX, _a = run_experiment(nm, w, syl, idx, logbi, logstart, lm_uni_order, rng)
        p(line)
        line, llXs, _m, _s, _ag, _a = run_experiment("  its shuffle", reshuffle(w, rng), syl, idx, logbi, logstart, lm_uni_order, rng)
        p(line)
        p("  gap real - shuffle = %+.4f" % (llX - llXs))
    p("  rongorongo gap      = %+.4f ; control B (true homophonic Rapa Nui) gap = %+.4f" % (llR - mu, llB - llC))
    p("for scale: control B recovered %.0f%% of tokens with LL/token %.4f vs its shuffle %.4f (gap %+.4f); ceiling %.4f"
      % ((accB or 0) * 100, llB, llC, llB - llC, ceiling))

    # the best mapping, most frequent glyphs, with agreement
    types, cidx, G, outg, inn, selfc, startc, unic = stR
    p("")
    p("=" * 100)
    p("BEST MAPPING, 25 MOST FREQUENT GLYPHS (agreement = share of restarts giving this syllable)")
    p("=" * 100)
    # recompute votes for rongorongo
    stR2 = stR
    votes = defaultdict(Counter)
    for r in range(RESTARTS):
        init = freq_init(stR2, V, lm_uni_order, rng) if r % 2 == 0 else None
        b, m = search(stR2, V, logbi, logstart, rng, init=init)
        for g in range(G):
            votes[g][m[g]] += 1
    order = sorted(range(G), key=lambda g: -unic[g])[:25]
    for g in order:
        top, cnt = votes[g].most_common(1)[0]
        alt = ", ".join("%s(%d)" % (syl[s], c) for s, c in votes[g].most_common(3)[1:])
        p("  glyph %-6s n=%-5d -> %-4s  %d/%d   alternatives: %s" % (types[g], unic[g], syl[top], cnt, RESTARTS, alt))

    txt = "\n".join(out)
    print(txt)
    open("decipher_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
