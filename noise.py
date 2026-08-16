"""Transliteration-error noise: how much does a dirty reading move the numbers?

Korovina (15 Aug): all existing transliterations are "dirty" (contain errors),
"although the error rate is not very high". Model: a fraction p of glyph
tokens is misread as some other sign, drawn from the corpus unigram
distribution (frequent signs are misread-into more often). Report the shift
in Hcond_n and in the structural signal, next to the two yardsticks already
measured: catalogue-length effect 0.318 and structural signal 0.077.
"""
import math, random, sys
from collections import Counter
sys.path.insert(0, ".")
from horley import read_lines, tokens_plain, tokens_horley, stats, reshuffle

RATES = [0.01, 0.03, 0.05, 0.10]
DRAWS = 20
SHUF = 40
SEED = 20260816

def corrupt(runs, p, rng, pool):
    out = []
    for r in runs:
        out.append([rng.choice(pool) if rng.random() < p else t for t in r])
    return out

def measure(runs, rng, shuf=SHUF):
    s = stats(runs)
    nulls = [stats(reshuffle(runs, rng))["hcn"] for _ in range(shuf)]
    mu = sum(nulls)/len(nulls)
    s["sig"] = s["hcn"] - mu
    return s

def main():
    rng = random.Random(SEED)
    lines = read_lines()
    sets = {"base633": [r for s in lines for r in tokens_plain(s, True)],
            "horley125": [r for s in lines for r in tokens_horley(s)]}
    out = []
    p_ = out.append
    p_("=" * 80)
    p_("TRANSLITERAATIOVIRHEIDEN VAIKUTUS (p = osuus vaarin luettuja glyfeja)")
    p_("vertailu: luennan pituusvaikutus 0.318, rakennesignaali 0.077")
    p_("=" * 80)
    for name, runs in sets.items():
        pool = [t for r in runs for t in r]
        clean = measure(runs, rng, shuf=100)
        p_("%s  puhdas: Hcn %.3f  sig %+.3f  L=%d" % (name, clean["hcn"], clean["sig"], clean["L"]))
        p_("  %6s %10s %10s %10s %10s" % ("p", "dHcn", "sd", "dsig", "sd"))
        for p in RATES:
            dh, ds = [], []
            for _ in range(DRAWS):
                m = measure(corrupt(runs, p, rng, pool), rng)
                dh.append(m["hcn"] - clean["hcn"]); ds.append(m["sig"] - clean["sig"])
            def ms(xs):
                mu = sum(xs)/len(xs); sd = math.sqrt(sum((x-mu)**2 for x in xs)/(len(xs)-1)); return mu, sd
            a, b = ms(dh); c, d = ms(ds)
            p_("  %6.0f%% %+10.4f %10.4f %+10.4f %10.4f" % (p*100, a, b, c, d))
    txt = "\n".join(out); print(txt)
    open("noise_results.txt", "w", encoding="utf-8").write(txt + "\n")

main()
