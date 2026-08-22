"""Redo the syllabary comparison on real Rapa Nui prose.

Korovina (22 Aug 2026) sent four Rapa Nui text collections after saying the
Bible translation "seems not the most suitable, after all":

  Campbell   Campbell's oral-tradition collection
  Englert    Sebastian Englert's texts (Spanish framing sentences interleaved)
  Isla6      carefully edited, macrons and glottals marked
  ManuE      Manuscript E (older orthography, no glottal marking)

Section 7 of the paper rested on the Wycliffe NT. This asks whether the
2.4-3.6x gap between rongorongo and real syllabaries survives on native prose.

Spanish and editorial material is removed at word level: any whitespace-token
containing a letter outside the Rapa Nui inventory is replaced by a break, so
removed material cuts the chain rather than leaking vowels into it.
"""
import io, math, re, sys
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_plain, tokens_horley
from sweep import bin_map, apply, num_key, measure
from syllabary_ref import syllabify, sample_runs, N_RR, SAMPLES, rng

RAP_C = ["ng", "ŋ", "p", "t", "k", "'", "m", "n", "v", "r", "h"]
RAP_OK = set("aeiouāēīōūhkmngprtvʔ'’")
FILES = ["Campbell", "Englert", "Isla6", "ManuE"]


def clean(text):
    text = text.replace("(-) ", "").replace("(-)", "")
    text = re.sub(r"\d+", " . ", text)
    kept = dropped = 0
    out = []
    for w in re.split(r"(\s+)", text):
        if not w.strip():
            out.append(" ")
            continue
        core = w.strip(".,;:!?«»()[]¿¡…\"-–—")
        letters = [c for c in core.lower() if c.isalpha()]
        if letters and all(c in RAP_OK for c in letters):
            out.append(w); kept += 1
        else:
            out.append(" . "); dropped += 1
    return "".join(out), kept, dropped


def summarize(runs):
    full = measure(runs, rng, shuffles=30)
    ss = [measure(sample_runs(runs, N_RR, rng), rng, shuffles=30) for _ in range(SAMPLES)]
    def ms(k):
        xs = [s[k] for s in ss]
        mu = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
        return mu, sd
    return full, {k: ms(k) for k in ("L", "hcn", "sig", "z", "cov")}


def main():
    o = []
    p = o.append
    p("=" * 104)
    p("RAPA NUI PROSE FROM KOROVINA (2026-08-22) vs the Bible-based reference in section 7")
    p("=" * 104)

    texts, refs = {}, {}
    for name in FILES:
        raw = io.open("korovina_files/%s.txt" % name, encoding="utf-8-sig").read()
        c, kept, dropped = clean(raw)
        texts[name] = c
        p("%-10s %7d chars -> %6d words kept, %5d dropped (%.1f%% removed as non-Rapa Nui)"
          % (name, len(raw), kept, dropped, 100.0 * dropped / max(1, kept + dropped)))
    combined = " . ".join(texts[n] for n in FILES)

    for name in FILES:
        refs[name + "_long"] = syllabify(texts[name], RAP_C, False)
        refs[name + "_fold"] = syllabify(texts[name], RAP_C, True)
    refs["ALL_long"] = syllabify(combined, RAP_C, False)
    refs["ALL_fold"] = syllabify(combined, RAP_C, True)

    p("")
    p("%-13s %7s %5s | %-32s | %s" % ("ref", "tokens", "L",
      "full text: Hcn  sig     z   cov", "N=14812 samples (mean+-sd): L Hcn sig z cov"))
    p("-" * 104)
    res = {}
    for name, runs in refs.items():
        n_tok = sum(len(r) for r in runs)
        if n_tok < 3000:
            p("%-13s %7d  SKIPPED (too few tokens)" % (name, n_tok)); continue
        full, ms = summarize(runs)
        res[name] = (full, ms)
        p("%-13s %7d %5d | %.3f %+.3f %7.1f %5.1f%% | %5.1f %.3f+-%.3f %+.3f+-%.3f %7.1f %5.1f%%"
          % (name, full["n"], full["L"], full["hcn"], full["sig"], full["z"], full["cov"] * 100,
             ms["L"][0], ms["hcn"][0], ms["hcn"][1], ms["sig"][0], ms["sig"][1], ms["z"][0],
             ms["cov"][0] * 100))

    # rongorongo merged to each reference L, N is 14812 by nature
    lines = read_lines()
    base = [r for s in lines for r in tokens_plain(s, True)]
    horl = [r for s in lines for r in tokens_horley(s)]
    base_types = sorted(Counter(t for r in base for t in r), key=num_key)
    horl_types = sorted(Counter(t for r in horl for t in r), key=num_key)
    base_freq = [t for t, _ in Counter(t for r in base for t in r).most_common()]

    p("")
    p("=" * 104)
    p("RONGORONGO MERGED TO THE SAME L, and the gap in |sig|")
    p("=" * 104)
    for L in sorted(set(res[k][0]["L"] for k in res)):
        rr = {}
        rr["numeric"] = measure(apply(base, bin_map(base_types, L)), rng, 50)
        if L <= len(horl_types):
            rr["horley"] = measure(apply(horl, bin_map(horl_types, L)), rng, 50)
        keep = set(base_freq[:L - 1])
        rr["freq"] = measure(apply(base, {t: (t if t in keep else "OTHER") for t in base_types}), rng, 50)
        best = max(rr.items(), key=lambda kv: abs(kv[1]["sig"]))
        p("L=%-4d  rongorongo best = %-8s Hcn %.3f sig %+.3f cov %4.1f%%"
          % (L, best[0], best[1]["hcn"], best[1]["sig"], best[1]["cov"] * 100))
        for k in sorted(res, key=lambda k: -abs(res[k][1]["sig"][0])):
            if res[k][0]["L"] != L:
                continue
            rs = res[k][1]
            ratio = abs(rs["sig"][0]) / max(1e-9, abs(best[1]["sig"]))
            p("        %-13s Hcn %.3f sig %+.3f  ->  gap %.2fx" % (k, rs["hcn"][0], rs["sig"][0], ratio))
    txt = "\n".join(o)
    io.open("korovina_ref_results.txt", "w", encoding="utf-8").write(txt + "\n")
    sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))


if __name__ == "__main__":
    main()
