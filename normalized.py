"""Redo the transcription-sensitivity measurement in the literature's own units.

Rao et al. (2010), replying to Sproat, state the normalisation explicitly:

    "To compare sequences over different alphabet sizes L, the logarithm in the
     entropy calculation was taken to base L (417 for Indus, 4 for DNA, etc.).
     The resulting normalized block entropy is plotted as a function of block
     size."

Taking the log to base L puts every symbol system on a common [0, 1] axis whose
endpoints are the two references they plot: Min Ent (rigidly ordered) at 0 and
Max Ent (unordered) at 1. Every distinction the debate draws -- languages versus
DNA, protein, Fortran, music -- lives inside that unit interval.

Raw bits would have made transcription look damaging for free, since changing
the sign inventory changes L directly and the normalisation is what divides that
out. The question is whether the movement survives it.
"""
import json
import math
import os
import random
from collections import Counter

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "rongopy", "ga_lstm", "tablets")
ENCODINGS = [("barthel", "tablets.json"),
             ("clean", "tablets_clean.json"),
             ("simple", "tablets_simple.json")]
SHUFFLES = 200
SEED = 20260815


def load_lines(fn):
    d = json.load(open(os.path.join(BASE, fn), encoding="utf-8"))
    out = []
    for _obj, lines in d.items():
        for _lid, text in lines.items():
            toks = [t for t in str(text).split("-") if t]
            if toks:
                out.append(toks)
    return out


def entropy_bits(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


def stats(lines):
    uni = Counter(t for line in lines for t in line)
    bi = Counter()
    for line in lines:
        for a, b in zip(line, line[1:]):
            bi[(a, b)] += 1
    L = len(uni)
    h1 = entropy_bits(uni)
    hcond = entropy_bits(bi) - h1
    # log base L is division by log2(L); L is the alphabet actually observed.
    denom = math.log2(L) if L > 1 else 1.0
    return {"L": L, "h1": h1, "hcond": hcond,
            "h1_n": h1 / denom, "hcond_n": hcond / denom}


def reshuffle(lines, rng):
    flat = [t for line in lines for t in line]
    rng.shuffle(flat)
    out, i = [], 0
    for line in lines:
        out.append(flat[i:i + len(line)])
        i += len(line)
    return out


def main():
    rng = random.Random(SEED)
    rows = []
    for key, fn in ENCODINGS:
        lines = load_lines(fn)
        s = stats(lines)
        nulls = [stats(reshuffle(lines, rng))["hcond_n"] for _ in range(SHUFFLES)]
        m = sum(nulls) / len(nulls)
        sd = math.sqrt(sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1))
        s["null_mean"] = m
        s["null_sd"] = sd
        s["signal"] = s["hcond_n"] - m
        rows.append((key, s))

    print("=" * 78)
    print("NORMALISOITU (log kanta L) — sama asteikko jolla Rao vertaa kaikkia")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'L':>7}{'H1 raaka':>10}{'H1 norm':>10}"
          f"{'Hc raaka':>10}{'Hc norm':>10}")
    for k, s in rows:
        print(f"{k:<10}{s['L']:>7}{s['h1']:>10.3f}{s['h1_n']:>10.3f}"
              f"{s['hcond']:>10.3f}{s['hcond_n']:>10.3f}")

    print()
    print("=" * 78)
    print("RAKENNESIGNAALI NORMALISOIDULLA ASTEIKOLLA")
    print("=" * 78)
    print(f"{'enkoodaus':<10}{'oikea':>9}{'nolla':>9}{'ero':>9}{'z':>9}")
    for k, s in rows:
        z = s["signal"] / s["null_sd"] if s["null_sd"] else float("nan")
        print(f"{k:<10}{s['hcond_n']:>9.3f}{s['null_mean']:>9.3f}"
              f"{s['signal']:>9.3f}{z:>9.1f}")

    print()
    print("=" * 78)
    print("RATKAISU")
    print("=" * 78)
    hc = [s["hcond_n"] for _k, s in rows]
    h1 = [s["h1_n"] for _k, s in rows]
    span_hc = max(hc) - min(hc)
    span_h1 = max(h1) - min(h1)
    sig = max(abs(s["signal"]) for _k, s in rows)
    print(f"  Asteikon koko vali (Min Ent .. Max Ent)      : 1.000")
    print(f"  H_cond norm. hajonta pelkasta transkriptiosta: {span_hc:.3f}"
          f"   = {span_hc*100:.1f} % koko asteikosta")
    print(f"  H1 norm. hajonta pelkasta transkriptiosta    : {span_h1:.3f}"
          f"   = {span_h1*100:.1f} % koko asteikosta")
    print(f"  Suurin rakennesignaali samalla asteikolla    : {sig:.3f}")
    print()
    if span_hc > sig:
        print(f"  => transkriptio siirtaa {span_hc/sig:.1f}x enemman kuin rakenne.")
    else:
        print("  => normalisointi kumoaa vaitteen: rakenne > transkriptio.")


if __name__ == "__main__":
    main()
