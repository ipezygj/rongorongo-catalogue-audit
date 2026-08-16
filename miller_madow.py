"""Rerun the ladder with Miller-Madow bias correction on every entropy.

The plug-in estimator underestimates entropy whenever the table is sparse, and
these tables are 0.25%-24% full. Miller-Madow adds back a first-order estimate
of that bias:

    H_MM = H_plugin + (m - 1) / (2 N ln 2)      [bits]

with m the number of bins actually observed and N the sample size. It is
applied separately to the unigram and bigram tables before subtracting, and to
the shuffle null as well, so real and null are compared on equal footing.

The size of the correction is reported alongside the estimate. Miller-Madow is
itself only first-order: where the correction is a large fraction of the value
it repairs, it signals that no plug-in-family estimator is trustworthy there,
rather than that the corrected number can be quoted.
"""
import glob
import io
import math
import os
import random
import re
import xml.etree.ElementTree as ET
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
XMLDIR = os.path.join(HERE, "ceipp", "xml")
SHUFFLES = 200
SEED = 20260815
IS_GLYPH = re.compile(r"^\d")
LN2 = math.log(2)

_ns = {}
exec(io.open(os.path.join(HERE, "rongopy", "horley_encoding.py"),
             encoding="utf-8").read(), _ns)
HORLEY = _ns["horley_encoding"]


def horley_lookup(code):
    c = code.replace("!", "")
    m = re.match(r"^0*(\d+)([a-zA-Z]*)$", c)
    if not m:
        return None
    num, suf = m.group(1), m.group(2)
    for i in range(len(suf), -1, -1):
        k = num + suf[:i]
        if k in HORLEY:
            parts = str(HORLEY[k]).split()
            return None if any(p == "?" for p in parts) else parts
    return None


def read_lines():
    out = []
    for path in sorted(glob.glob(os.path.join(XMLDIR, "*.xml"))):
        root = ET.parse(path).getroot()
        for line in root.iter("line"):
            seq = [((g.findtext("code/ceipp") or "").strip(),
                    (g.findtext("link") or "").strip())
                   for g in line.iter("glyph")]
            if seq:
                out.append(seq)
    return out


def tokens(seq, mode):
    runs, cur = [], []
    for code, link in seq:
        if not IS_GLYPH.match(code):
            if cur:
                runs.append(cur); cur = []
            continue
        if mode == "horley":
            parts = horley_lookup(code)
            if parts is None:
                if cur:
                    runs.append(cur); cur = []
                continue
            cur.extend(parts)
        else:
            s = code.replace("!", "")
            cur.append(re.match(r"^(\d+)", s).group(1) if mode == "base" else s)
        if link in ("*", "…"):
            if cur:
                runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    return runs


def h_plugin(counter):
    n = sum(counter.values())
    if n == 0:
        return 0.0, 0, 0
    h = -sum((c / n) * math.log2(c / n) for c in counter.values())
    return h, len(counter), n


def mm(h, m, n):
    """Miller-Madow corrected entropy in bits, plus the correction size."""
    if n == 0:
        return h, 0.0
    corr = (m - 1) / (2 * n * LN2)
    return h + corr, corr


def analyse(runs):
    uni = Counter(t for r in runs for t in r)
    bi = Counter()
    for r in runs:
        for a, b in zip(r, r[1:]):
            bi[(a, b)] += 1
    h1, m1, n1 = h_plugin(uni)
    h2, m2, n2 = h_plugin(bi)
    h1c, c1 = mm(h1, m1, n1)
    h2c, c2 = mm(h2, m2, n2)
    L = len(uni)
    den = math.log2(L) if L > 1 else 1.0
    return {
        "L": L, "n": n1,
        "hc_plug": h2 - h1, "hc_mm": h2c - h1c,
        "hcn_plug": (h2 - h1) / den, "hcn_mm": (h2c - h1c) / den,
        "corr": (c2 - c1), "corr_n": (c2 - c1) / den,
        "cov": m2 / (L * L) if L else 0.0,
    }


def reshuffle(runs, rng):
    flat = [t for r in runs for t in r]
    rng.shuffle(flat)
    out, i = [], 0
    for r in runs:
        out.append(flat[i:i + len(r)]); i += len(r)
    return out


def main():
    rng = random.Random(SEED)
    lines = read_lines()
    rows = []
    for mode in ("full", "base", "horley"):
        runs = [r for seq in lines for r in tokens(seq, mode)]
        s = analyse(runs)
        nulls = [analyse(reshuffle(runs, rng))["hcn_mm"] for _ in range(SHUFFLES)]
        s["null_mm"] = sum(nulls) / len(nulls)
        s["sig_mm"] = s["hcn_mm"] - s["null_mm"]
        rows.append((mode, s))

    print("=" * 78)
    print("MILLER-MADOW -KORJAUS")
    print("=" * 78)
    print(f"{'luenta':<9}{'peitto':>9}{'Hc plug':>10}{'korjaus':>10}"
          f"{'Hc MM':>9}{'korj-%':>9}")
    for m_, s in rows:
        pct = s["corr"] / s["hc_mm"] * 100 if s["hc_mm"] else float("nan")
        print(f"{m_:<9}{s['cov']*100:>8.2f}%{s['hc_plug']:>10.3f}"
              f"{s['corr']:>+10.3f}{s['hc_mm']:>9.3f}{pct:>8.1f}%")

    print()
    print("=" * 78)
    print("NORMALISOITU, KORJATTU — vs sekoitusnolla (myos korjattu)")
    print("=" * 78)
    print(f"{'luenta':<9}{'Hcn plug':>11}{'Hcn MM':>10}{'nolla MM':>11}"
          f"{'signaali':>11}")
    for m_, s in rows:
        print(f"{m_:<9}{s['hcn_plug']:>11.3f}{s['hcn_mm']:>10.3f}"
              f"{s['null_mm']:>11.3f}{s['sig_mm']:>+11.3f}")

    print()
    print("=" * 78)
    print("RATKAISU KORJATTUNA")
    print("=" * 78)
    for label, key, sigkey in (("plug-in", "hcn_plug", None),
                               ("Miller-Madow", "hcn_mm", "sig_mm")):
        vals = [s[key] for _m, s in rows]
        span = max(vals) - min(vals)
        if sigkey:
            sig = max(abs(s[sigkey]) for _m, s in rows)
            print(f"  {label:<14} hajonta {span:.3f}   signaali {sig:.3f}"
                  f"   suhde {span/sig:.1f}x")
        else:
            print(f"  {label:<14} hajonta {span:.3f}")


if __name__ == "__main__":
    main()
