"""Syllabary references for the L=50 question.

Korovina (16 Aug 2026): reducing the catalogue to ~50 "will inevitably get more
similarity to syllables than to anything else". To test that we need what a
syllabary actually looks like on the same instrument. Three references:

  rap   Rapa Nui itself (Wycliffe NT, gospels+Acts, bible.com), syllabified
        (C)V with C in {p t k ' m n ng v r h}, V in {a e i o u} (+ long).
        This is the language rongorongo is presumed to encode.
  mri   Maori (Paipera Tapu NT, ebible.org), same procedure, C in
        {h k m n ng p r t w wh}. Same family, same syllable canon.
  linb  Linear B (linearb.xyz corpus, 5889 inscriptions), syllabograms only,
        word dividers dropped (rongorongo has none), ideograms/numerals/breaks
        cut the chain like lacunae.

Two variants for the languages: long vowels distinct (L ~ 100-110) and folded
(L ~ 55). Everything is measured (i) on the full text and (ii) on 20 random
contiguous samples matched to the rongorongo token count (14 812), because
coverage and null distance both depend on N. Then rongorongo is merged to
exactly each reference's L under all four rules of sweep.py so the comparison
is at identical L and identical N.
"""
import json, math, random, re, sys
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_plain, tokens_horley, stats, reshuffle
from sweep import bin_map, apply, num_key, measure

N_RR = 14812
SAMPLES = 20
SEED = 20260816
rng = random.Random(SEED)

VOW = "aeiou"
LONG = {"ā": "aː", "ē": "eː", "ī": "iː", "ō": "oː", "ū": "uː"}
GLOTTALS = ["ꞌ", "ʼ", "’", "‘", "`"]


def syllabify(text, consonants, fold_long):
    """(C)V syllables; digraphs first. Returns list of runs (one per verse)."""
    text = text.lower()
    for k, v in LONG.items():
        text = text.replace(k, v if not fold_long else v[0])
    for g in GLOTTALS:
        text = text.replace(g, "'")
    cons = sorted(consonants, key=len, reverse=True)
    out, cur, i, n = [], [], 0, len(text)
    while i < n:
        c = ""
        for cc in cons:
            if text.startswith(cc, i):
                c = cc
                i += len(cc)
                break
        if i < n and text[i] in VOW:
            v = text[i]
            i += 1
            if i < n and text[i] == "ː":
                v += "ː"
                i += 1
            cur.append(c + v)
        else:
            if c:
                # consonant with no following vowel (foreign name) -> drop it
                continue
            ch = text[i]
            i += 1
            if ch in ".;:!?\n" and cur:
                out.append(cur)
                cur = []
    if cur:
        out.append(cur)
    return out


def load_rap():
    txt = open("ref/rap/rap_nt.txt", encoding="utf-8").read()
    seen, body = set(), []
    for block in txt.split("## ")[1:]:
        hdr, _, rest = block.partition("\n")
        if hdr in seen:
            continue
        seen.add(hdr)
        rest = re.sub(r"Currently Selected:.*?\d", " ", rest)
        rest = re.sub(r"\([^)]*\)", " ", rest)  # cross refs
        rest = re.sub(r"\d+", " . ", rest)  # verse numbers -> breaks
        body.append(rest)
    return " . ".join(body), len(seen)


def load_mri():
    import glob
    parts = []
    for f in sorted(glob.glob("ref/mri/mri_*_read.txt")):
        s = open(f, encoding="utf-8-sig").read()
        s = re.sub(r"^\d+\.\s*$", " . ", s, flags=re.M)
        parts.append(s)
    return "\n".join(parts)


LINB_SKIP = {"mut", "vac", "inf", "sup", "vest", "lat", "v", "s", "d", "dex", "sin"}


def load_linb():
    s = open("ref/LinearBInscriptions.js", encoding="utf-8").read()
    s = s[s.find("["):s.rfind("]") + 1]
    d = json.loads(s)
    syl = re.compile(r"^(?:[a-z]{1,3}[0-9]?|\*[0-9]{2}[a-z]?)$")  # a, ko, pu2, ra3, *56
    runs = []
    for _name, ins in d:
        cur = []
        for w in ins.get("transliteratedWords", []):
            w = w.strip()
            if not w:
                continue
            for t in re.split(r"[-\s]+", w):
                if syl.match(t) and t not in LINB_SKIP:
                    cur.append(t)
                else:
                    if cur:
                        runs.append(cur)
                        cur = []
        if cur:
            runs.append(cur)
    return runs


def sample_runs(runs, n_tok, rng):
    """Random contiguous window of runs with ~n_tok tokens."""
    total = sum(len(r) for r in runs)
    if total <= n_tok:
        return runs
    start = rng.randrange(len(runs))
    out, k, i = [], 0, start
    while k < n_tok:
        r = runs[i % len(runs)]
        out.append(r)
        k += len(r)
        i += 1
    return out


def summarize(runs):
    full = measure(runs, rng, shuffles=30)
    ss = [measure(sample_runs(runs, N_RR, rng), rng, shuffles=30) for _ in range(SAMPLES)]

    def ms(k):
        xs = [s[k] for s in ss]
        mu = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0
        return mu, sd
    return full, {k: ms(k) for k in ("L", "hcn", "sig", "z", "cov")}


def fmt4(s):
    return "%.3f %+.3f %5.1f %4.1f%%" % (s["hcn"], s["sig"], s["z"], s["cov"] * 100)


def main():
    out = []
    p = out.append
    rap_txt, nch = load_rap()
    mri_txt = load_mri()
    RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
    MRI_C = ["ng", "wh", "h", "k", "m", "n", "p", "r", "t", "w"]
    refs = {}
    refs["rap_long"] = syllabify(rap_txt, RAP_C, False)
    refs["rap_fold"] = syllabify(rap_txt, RAP_C, True)
    refs["mri_long"] = syllabify(mri_txt, MRI_C, False)
    refs["mri_fold"] = syllabify(mri_txt, MRI_C, True)
    refs["linb"] = load_linb()
    p("=" * 100)
    p("TAVUKIRJOITUSREFERENSSIT (log kanta L; signaali = Hcn - sekoitus; peitto = bigrammitaulusta havaittu)")
    p("Rapa Nui NT: %d lukua" % nch)
    p("=" * 100)
    p("%-9s %7s %5s | %-30s | %-46s" % ("ref", "tokens", "L", "koko teksti: Hcn  sig   z   cov",
                                        "N=14812 otos (ka+-sd): L  Hcn  sig  z  cov"))
    res = {}
    for name, runs in refs.items():
        full, ms = summarize(runs)
        res[name] = (full, ms)
        p("%-9s %7d %5d | %.3f %+.3f %6.1f %5.1f%% | %5.1f  %.3f+-%.3f %+.3f+-%.3f %6.1f %5.1f%%+-%.1f"
          % (name, full["n"], full["L"], full["hcn"], full["sig"], full["z"], full["cov"] * 100,
             ms["L"][0], ms["hcn"][0], ms["hcn"][1], ms["sig"][0], ms["sig"][1], ms["z"][0],
             ms["cov"][0] * 100, ms["cov"][1] * 100))
        top = Counter(t for r in runs for t in r).most_common(12)
        p("          top: " + " ".join("%s:%d" % kv for kv in top))
    # rongorongo at exactly the same L
    lines = read_lines()
    base = [r for s in lines for r in tokens_plain(s, True)]
    horl = [r for s in lines for r in tokens_horley(s)]
    base_types = sorted(Counter(t for r in base for t in r), key=num_key)
    horl_types = sorted(Counter(t for r in horl for t in r), key=num_key)
    base_freq = [t for t, _ in Counter(t for r in base for t in r).most_common()]
    p("")
    p("=" * 100)
    p("RONGORONGO YHDISTETTYNA TASMALLEEN SAMAAN L:AAN (N=14812 luonnostaan)   Hcn  sig  z  cov")
    p("=" * 100)
    Ls = sorted(set(res[k][0]["L"] for k in res))
    for L in Ls:
        row = ["L=%-4d" % L]
        row.append("numeric " + fmt4(measure(apply(base, bin_map(base_types, L)), rng, 50)))
        if L <= len(horl_types):
            row.append("horley " + fmt4(measure(apply(horl, bin_map(horl_types, L)), rng, 50)))
        keep = set(base_freq[:L - 1])
        m = {t: (t if t in keep else "OTHER") for t in base_types}
        row.append("freq " + fmt4(measure(apply(base, m), rng, 50)))
        rs = []
        for _ in range(10):
            perm = base_types[:]
            rng.shuffle(perm)
            rs.append(measure(apply(base, bin_map(perm, L)), rng, 20))
        avg = {k: sum(s[k] for s in rs) / len(rs) for k in ("hcn", "sig", "z", "cov")}
        row.append("random " + fmt4(avg))
        p("  ".join(row))
        p("       refs at this L: " + ", ".join(
            "%s Hcn %.3f sig %+.3f cov %.1f%%" % (k, res[k][1]["hcn"][0], res[k][1]["sig"][0], res[k][1]["cov"][0] * 100)
            for k in res if res[k][0]["L"] == L))
    txt = "\n".join(out)
    print(txt)
    open("syllabary_ref_results.txt", "w", encoding="utf-8").write(txt + "\n")


if __name__ == "__main__":
    main()
