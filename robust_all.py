"""Reconstructs the four tab:robust (Table 9) numbers that had no saved
script/results file anywhere in the repo or git history: the ladder ratio
under codes-removed + object-preserving null (paper: 4.42), Horley against
the best mechanical rule with the unidentified-glyph code excluded from the
parallel-passage search (paper: 2.5), the syllabary gap at rongorongo's best
catalogue under the same object-null (paper: 2.4-3.5), and the fraction of
Indus's structural signal retained under a within-text null instead of a
pooled-corpus null (paper: 72%).

Every other number in the paper has a named *.py + *_results.txt pair; these
four did not (checked: no hit for "4.42" or "object null" anywhere in the
repo's git history). Written to close that gap, reusing the same corpus
readers, merge rules and statistic as the scripts that produced every other
verified table, so a mismatch here is evidence about the CLAIM, not about a
different measurement.

Object-preserving null (the rongorongo side): instead of shuffling tokens
across the whole pooled corpus, shuffle each of the 25 objects' own tokens
among themselves only, and never mix tokens between objects -- this is how a
single-text reference (Rapa Nui, Maori, Linear B) is necessarily measured,
so it is the fair comparison. Within-text null (the Indus side): Indus
"texts" are already close to single runs (mean 3.7 signs), so this is a
within-run shuffle, exactly as robustness.py already uses for run-length
checks elsewhere in the paper.
"""
import glob, io, math, os, random, re, sys
from collections import Counter

sys.path.insert(0, ".")
from horley import (read_lines, tokens_plain, tokens_horley, horley_lookup,
                     stats, reshuffle, XMLDIR)
import sweep as SW
import parallels as PAR
import syllabary_ref as SYL

rng = random.Random(20260825)
NOT_SIGNS = {"000", "999"}
out = []
p = out.append


def strip_pseudo(runs):
    """Treat 000/999 as breaks, exactly as pseudoglyph_audit.py does."""
    res = []
    for r in runs:
        cur = []
        for t in r:
            if re.match(r"^(\d+)", t).group(1) in NOT_SIGNS:
                if cur:
                    res.append(cur); cur = []
            else:
                cur.append(t)
        if cur:
            res.append(cur)
    return res


def read_by_object():
    """{object: [(code, link), ...] per line} -- same XML walk as horley.py's
    read_lines(), but keeping file identity instead of flattening it away."""
    objs = {}
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        import xml.etree.ElementTree as ET
        obj = os.path.splitext(os.path.basename(path))[0]
        root = ET.parse(path).getroot()
        seqs = []
        for line in root.iter("line"):
            seq = [((g.findtext("code/ceipp") or "").strip(),
                    (g.findtext("link") or "").strip())
                   for g in line.iter("glyph")]
            if seq:
                seqs.append(seq)
        objs[obj] = seqs
    return objs


OBJS = read_by_object()
p("objects read: %d (%s)" % (len(OBJS), ", ".join(sorted(OBJS))))

# Per-object runs for the three readings, pseudoglyphs removed.
RUNS_FULL = {o: strip_pseudo([r for seq in seqs for r in tokens_plain(seq, False)]) for o, seqs in OBJS.items()}
RUNS_BASE = {o: strip_pseudo([r for seq in seqs for r in tokens_plain(seq, True)]) for o, seqs in OBJS.items()}
RUNS_HORL = {o: strip_pseudo([r for seq in seqs for r in tokens_horley(seq)]) for o, seqs in OBJS.items()}

n_full = sum(len(t) for rs in RUNS_FULL.values() for t in rs)
n_base = sum(len(t) for rs in RUNS_BASE.values() for t in rs)
n_horl = sum(len(t) for rs in RUNS_HORL.values() for t in rs)
p("tokens after pseudoglyph removal: full %d, base %d, horley %d" % (n_full, n_base, n_horl))


def stats_pooled(by_obj):
    return stats([r for rs in by_obj.values() for r in rs])


def null_pooled(by_obj, draws, seedrng):
    allruns = [r for rs in by_obj.values() for r in rs]
    return [stats(reshuffle(allruns, seedrng))["hcn"] for _ in range(draws)]


def reshuffle_within_object(by_obj, seedrng):
    """Shuffle each object's own tokens among themselves only; never let a
    token cross an object boundary. Returns a new {object: runs} dict."""
    out_by_obj = {}
    for o, rs in by_obj.items():
        out_by_obj[o] = reshuffle(rs, seedrng)
    return out_by_obj


def null_object(by_obj, draws, seedrng):
    vals = []
    for _ in range(draws):
        shuffled = reshuffle_within_object(by_obj, seedrng)
        vals.append(stats_pooled(shuffled)["hcn"])
    return vals


def signal_from_nulls(real_hcn, nullvals):
    mu = sum(nullvals) / len(nullvals)
    sd = math.sqrt(sum((x - mu) ** 2 for x in nullvals) / (len(nullvals) - 1))
    sig = real_hcn - mu
    z = sig / sd if sd else float("nan")
    return sig, z, mu, sd


p("")
p("=" * 96)
p("PART 1: LADDER RATIO, PSEUDOGLYPHS REMOVED, OBJECT-PRESERVING NULL")
p("=" * 96)
SHUF = 200
readings = [("full", RUNS_FULL), ("base", RUNS_BASE), ("horley", RUNS_HORL)]

p("-- sanity check: pooled null, codes removed (should reproduce 4.28x) --")
pooled_sig = {}
for name, by_obj in readings:
    real = stats_pooled(by_obj)
    nv = null_pooled(by_obj, SHUF, rng)
    sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
    pooled_sig[name] = sig
    p("  %-7s L=%-5d n=%-6d Hcn=%.3f sig=%+.3f z=%.1f" % (name, real["L"], real["n"], real["hcn"], sig, z))
hcns = [stats_pooled(by_obj)["hcn"] for _, by_obj in readings]
spread = max(hcns) - min(hcns)
best = max(abs(v) for v in pooled_sig.values())
p("  spread %.3f | best signal %.3f | ratio %.2fx  (paper's pseudoglyph_audit.py: 4.28x)" % (spread, best, spread / best))

p("")
p("-- object-preserving null, codes removed (the new number, target ~4.42) --")
obj_sig = {}
for name, by_obj in readings:
    real = stats_pooled(by_obj)
    nv = null_object(by_obj, SHUF, rng)
    sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
    obj_sig[name] = sig
    p("  %-7s L=%-5d n=%-6d Hcn=%.3f sig=%+.3f z=%.1f" % (name, real["L"], real["n"], real["hcn"], sig, z))
best_obj = max(abs(v) for v in obj_sig.values())
p("  spread %.3f | best signal %.3f | ratio %.2fx" % (spread, best_obj, spread / best_obj))

p("")
p("=" * 96)
p("PART 2: COMPOSITION -- HORLEY VS BEST MECHANICAL RULE, 000 EXCLUDED FROM THE SEARCH")
p("=" * 96)

CORE = 50
TARGET_L = 125
N_RANDOM = 300


def read_lines_no000():
    """Same as parallels.read_lines, but '000' is a BREAK in the chain (as
    everywhere else in the paper), not a splice: a line containing 000 is
    split into the sub-runs on either side of it, each kept only if it still
    reaches the k-mer seed length. Splicing across 000 instead would invent
    an adjacency between two tokens that were never actually adjacent."""
    lines = PAR.read_lines()
    out = []
    for obj, toks in lines:
        cur = []
        for t in toks:
            if t == "000":
                if len(cur) >= PAR.K:
                    out.append((obj, cur))
                cur = []
            else:
                cur.append(t)
        if len(cur) >= PAR.K:
            out.append((obj, cur))
    return out


def cut(order, n_classes):
    m, size = {}, len(order) / n_classes
    for i, s in enumerate(order):
        m[s] = "C%d" % min(int(i / size), n_classes - 1)
    return m


p("-- sanity check: original read_lines (000 kept), should reproduce 2.2x --")
lines0 = PAR.read_lines()
_pairs0, _aligned0, subs0 = PAR.find_substitutions(lines0)
subs0f = {k: n for k, n in subs0.items() if PAR.horley_class(k[0]) is not None and PAR.horley_class(k[1]) is not None}
h_hit0, h_tot0 = PAR.absorbed(subs0f, PAR.horley_class)
freqs0 = Counter(t for _o, toks in lines0 for t in toks)
ranked0 = [s for s, _c in freqs0.most_common()]
core0, tail0 = ranked0[:CORE], ranked0[CORE:]
n_classes0 = TARGET_L - CORE
rates0 = {}
for label, order in (("numeric", sorted(tail0, key=int)),
                      ("frequency", sorted(tail0, key=lambda s: (-freqs0[s], int(s)))),
                      ("family", sorted(tail0, key=lambda s: (int(s) // 100, -freqs0[s])))):
    mp = dict(cut(order, n_classes0)); mp.update({s: s for s in core0})
    hit, tot = PAR.absorbed(subs0f, lambda s: mp.get(s))
    rates0[label] = hit / tot if tot else 0.0
best_mech0 = max(rates0.values())
p("  events=%d fair-set=%d  Horley=%.1f%%  best mechanical=%.1f%%  ratio=%.2fx  (paper's parallels3.py: 2.2x)"
  % (sum(subs0.values()), sum(subs0f.values()), h_hit0 / h_tot0 * 100, best_mech0 * 100, (h_hit0 / h_tot0) / best_mech0))

p("")
p("-- 000 excluded from the parallel-passage search (the new number, target ~2.5) --")
lines1 = read_lines_no000()
_pairs1, _aligned1, subs1 = PAR.find_substitutions(lines1)
subs1f = {k: n for k, n in subs1.items() if PAR.horley_class(k[0]) is not None and PAR.horley_class(k[1]) is not None}
h_hit1, h_tot1 = PAR.absorbed(subs1f, PAR.horley_class)
freqs1 = Counter(t for _o, toks in lines1 for t in toks)
ranked1 = [s for s, _c in freqs1.most_common()]
core1, tail1 = ranked1[:CORE], ranked1[CORE:]
n_classes1 = TARGET_L - CORE
rates1 = {}
for label, order in (("numeric", sorted(tail1, key=int)),
                      ("frequency", sorted(tail1, key=lambda s: (-freqs1[s], int(s)))),
                      ("family", sorted(tail1, key=lambda s: (int(s) // 100, -freqs1[s])))):
    mp = dict(cut(order, n_classes1)); mp.update({s: s for s in core1})
    hit, tot = PAR.absorbed(subs1f, lambda s: mp.get(s))
    rates1[label] = hit / tot if tot else 0.0
    p("  %-10s absorbed %d/%d = %.1f%%" % (label, hit, tot, rates1[label] * 100))
best_mech1 = max(rates1.values())
p("  events=%d fair-set=%d  Horley=%.1f%%  best mechanical=%.1f%%  ratio=%.2fx"
  % (sum(subs1.values()), sum(subs1f.values()), h_hit1 / h_tot1 * 100, best_mech1 * 100, (h_hit1 / h_tot1) / best_mech1))

p("")
p("=" * 96)
p("PART 3: SYLLABARY GAP AT RONGORONGO'S BEST CATALOGUE, OBJECT-NULL, CODES REMOVED")
p("=" * 96)

# Reference signals are unaffected (single continuous text each; already the
# correctly-measured "one shuffle per text" case) -- taken directly from the
# already-verified syllabary_ref_results.txt / paper prose (Sec 7):
REF_SIG = {
    "Linear B (L=95)":        0.152,
    "Rapa Nui, length (L=105)": 0.187,
    "Maori, folded (L=52)":     0.151,
    "Rapa Nui, folded (L=55)":  0.170,
}
REF_L = {"Linear B (L=95)": 95, "Rapa Nui, length (L=105)": 105,
         "Maori, folded (L=52)": 52, "Rapa Nui, folded (L=55)": 55}
PAPER_RATIO = {"Linear B (L=95)": 2.4, "Rapa Nui, length (L=105)": 2.8,
               "Maori, folded (L=52)": 3.3, "Rapa Nui, folded (L=55)": 3.6}


def num_key2(code):
    m = re.match(r"^0*(\d+)", code)
    return (int(m.group(1)) if m else 10**9, code)


def freq_fold(base_types, base_freq, L):
    keep = set(base_freq[:L - 1])
    return {t: (t if t in keep else "OTHER") for t in base_types}


def random_fold(base_types, L, seedrng):
    perm = base_types[:]
    seedrng.shuffle(perm)
    return SW.bin_map(perm, L)


def best_signal_at_L(by_obj_base, by_obj_horl, L, seedrng, draws=150, random_draws=8):
    """Best |signal| over numeric/horley/freq/random merge rules at size L
    (all four rules of Sec. 5 -- an earlier version of this function omitted
    horley, which is almost always the strongest rule, and so understated
    "best" and overstated every ratio below; caught by a pooled-null sanity
    check against the already-verified 2.4/2.8/3.3/3.6 baseline, which only
    reproduced once horley was added back), on the pseudoglyph-removed,
    per-object readings, under an object-preserving null."""
    base_types = sorted({t for rs in by_obj_base.values() for r in rs for t in r}, key=num_key2)
    base_freq = [t for t, _c in Counter(t for rs in by_obj_base.values() for r in rs for t in r).most_common()]
    horl_types = sorted({t for rs in by_obj_horl.values() for r in rs for t in r}, key=num_key2)
    sigs = {}
    # numeric
    m = SW.bin_map(base_types, L)
    mapped = {o: SW.apply(rs, m) for o, rs in by_obj_base.items()}
    real = stats_pooled(mapped)
    nv = null_object(mapped, draws, seedrng)
    sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
    sigs["numeric"] = sig
    # horley (merged down, when L reaches that far)
    if L <= len(horl_types):
        m = SW.bin_map(horl_types, L)
        mapped = {o: SW.apply(rs, m) for o, rs in by_obj_horl.items()}
        real = stats_pooled(mapped)
        nv = null_object(mapped, draws, seedrng)
        sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
        sigs["horley"] = sig
    # freq
    m = freq_fold(base_types, base_freq, L)
    mapped = {o: SW.apply(rs, m) for o, rs in by_obj_base.items()}
    real = stats_pooled(mapped)
    nv = null_object(mapped, draws, seedrng)
    sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
    sigs["freq"] = sig
    # random (fewer draws, averaged)
    rvals = []
    for _ in range(random_draws):
        m = random_fold(base_types, L, seedrng)
        mapped = {o: SW.apply(rs, m) for o, rs in by_obj_base.items()}
        real = stats_pooled(mapped)
        nv = null_object(mapped, draws // 3, seedrng)
        sig, z, mu, sd = signal_from_nulls(real["hcn"], nv)
        rvals.append(sig)
    sigs["random"] = sum(rvals) / len(rvals)
    return sigs


for label in REF_SIG:
    L = REF_L[label]
    sigs = best_signal_at_L(RUNS_BASE, RUNS_HORL, L, rng)
    best = max(abs(v) for v in sigs.values())
    ratio = REF_SIG[label] / best
    p("  %-26s rongorongo sigs=%s  best=%.4f  ratio=%.2fx  (paper's pooled-null figure: %.1fx)"
      % (label, {k: round(v, 4) for k, v in sigs.items()}, best, ratio, PAPER_RATIO[label]))

p("")
p("=" * 96)
p("PART 4: INDUS SIGNAL RETAINED UNDER A WITHIN-TEXT (WITHIN-RUN) NULL")
p("=" * 96)

HERE_ABS = os.path.dirname(os.path.abspath(__file__))


def read_m77(keep_star):
    """Copied from indus/indus.py rather than imported: that module has a
    chain of side-effect imports (robustness.py, fingerprint.py) that print
    and write their own results files on import. This is the same function,
    unchanged."""
    runs = []
    path = os.path.join(HERE_ABS, "indus", "data", "indus_script_IM77_concordance.txt")
    for line in open(path, encoding="utf-8", errors="replace"):
        cols = [c.strip() for c in line.rstrip("\n").split("\t")]
        if not cols or cols[0] == "IM77":
            continue
        cur = []
        for c in cols[1:]:
            if not c:
                continue
            if c == "000":
                if cur:
                    runs.append(cur)
                    cur = []
                continue
            tok = c if keep_star else c.lstrip("*")
            cur.append(tok.zfill(3) if tok.isdigit() else tok)
        if cur:
            runs.append(cur)
    return runs


m77 = read_m77(False)  # Mahadevan base reading, 417 signs -- the paper's headline Indus figure


def reshuffle_within_run(runs, seedrng):
    out = []
    for r in runs:
        q = r[:]
        seedrng.shuffle(q)
        out.append(q)
    return out


real_indus = stats(m77)
nv_pooled = [stats(reshuffle(m77, rng))["hcn"] for _ in range(200)]
sig_pooled, z_pooled, _, _ = signal_from_nulls(real_indus["hcn"], nv_pooled)
p("-- sanity check: pooled null (should reproduce -0.217, z~-169) --")
p("  L=%d n=%d Hcn=%.3f sig=%+.3f z=%.1f" % (real_indus["L"], real_indus["n"], real_indus["hcn"], sig_pooled, z_pooled))

nv_run = [stats(reshuffle_within_run(m77, rng))["hcn"] for _ in range(200)]
sig_run, z_run, _, _ = signal_from_nulls(real_indus["hcn"], nv_run)
p("")
p("-- within-run (within-text) null, the new number, target ~72%% retained --")
p("  L=%d n=%d Hcn=%.3f sig=%+.3f z=%.1f" % (real_indus["L"], real_indus["n"], real_indus["hcn"], sig_run, z_run))
p("  retained = %.1f%% of pooled-null signal  (paper: 72%%)" % (100.0 * abs(sig_run) / abs(sig_pooled)))

txt = "\n".join(out)
io.open("robust_all_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
