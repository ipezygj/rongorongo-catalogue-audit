"""Which catalogue does the corpus's own spelling variation actually support?

parallels.py established that Horley's reduction absorbs far more of the
observed substitutions than chance. That leaves the sharper question: is it his
particular grouping that does the work, or would any defensible rule of the same
size do as well? The entropy experiment found composition worth only 1 per cent
of the length effect, so if composition matters anywhere it should show here,
where the evidence is the scribes' own interchanges rather than a summary
statistic.

The comparison holds the size at 125 throughout: Horley's published catalogue
against the three mechanical rules from composition2.py and against random
groupings, all scored on the same substitution events.
"""
import io
import math
import os
import random
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

_src = io.open(os.path.join(HERE, "parallels.py"), encoding="utf-8").read()
_src = _src.replace('if __name__ == "__main__":\n    main()', "")
P = {"__file__": os.path.join(HERE, "parallels.py"), "__name__": "par"}
exec(_src, P)

CORE = 50
TARGET_L = 125
N_RANDOM = 300
SEED = 20260815


def cut(order, n_classes):
    m, size = {}, len(order) / n_classes
    for i, s in enumerate(order):
        m[s] = f"C{min(int(i / size), n_classes - 1)}"
    return m


def main():
    lines = P["read_lines"]()
    _pairs, _aligned, subs = P["find_substitutions"](lines)
    freqs = Counter(t for _o, toks in lines for t in toks)
    ranked = [s for s, _c in freqs.most_common()]
    core, tail = ranked[:CORE], ranked[CORE:]
    n_classes = TARGET_L - CORE

    events = sum(subs.values())
    print(f"substitution events: {events} over {len(subs)} distinct pairs")

    # Horley first, on the events he can classify.
    h_hit, h_tot = P["absorbed"](subs, P["horley_class"])
    print()
    print("=" * 74)
    print(f"ABSORPTION AT L = {TARGET_L}, SAME EVENTS THROUGHOUT")
    print("=" * 74)
    print(f"{'catalogue':<22}{'absorbed':>12}{'of events':>12}{'rate':>9}")
    print(f"{'Horley (published)':<22}{h_hit:>12}{h_tot:>12}"
          f"{h_hit / h_tot * 100:>8.1f}%")

    orders = {
        "numeric": sorted(tail, key=int),
        "frequency": sorted(tail, key=lambda s: (-freqs[s], int(s))),
        "family": sorted(tail, key=lambda s: (int(s) // 100, -freqs[s])),
    }
    rates = {}
    for label, order in orders.items():
        mapping = dict(cut(order, n_classes))
        mapping.update({s: s for s in core})
        hit, tot = P["absorbed"](subs, lambda s: mapping.get(s))
        rates[label] = hit / tot if tot else 0.0
        print(f"{label:<22}{hit:>12}{tot:>12}{rates[label] * 100:>8.1f}%")

    all_signs = sorted({t for _o, toks in lines for t in toks})
    rng = random.Random(SEED)
    vals = []
    for _ in range(N_RANDOM):
        assign = {s: rng.randrange(TARGET_L) for s in all_signs}
        hit, tot = P["absorbed"](subs, lambda s: assign.get(s))
        vals.append(hit / tot if tot else 0.0)
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - m) ** 2 for x in vals) / (len(vals) - 1))
    print(f"{'random':<22}{'':>12}{'':>12}{m * 100:>8.1f}%   +- {sd * 100:.1f}")

    print()
    print("=" * 74)
    print("VERDICT")
    print("=" * 74)
    hz = (h_hit / h_tot - m) / sd
    print(f"  Horley            {h_hit / h_tot * 100:>5.1f} %   z = {hz:>6.1f}")
    for label, r in rates.items():
        print(f"  {label:<16}  {r * 100:>5.1f} %   z = {(r - m) / sd:>6.1f}")
    best_mech = max(rates.values())
    print()
    print(f"  Horley / best mechanical rule = "
          f"{(h_hit / h_tot) / best_mech:.1f}x")
    print()
    print("  Composition moved conditional entropy by 1 % of the length effect.")
    print("  Against the scribes' own substitutions it is the whole effect:")
    print("  size alone buys nothing, and the published grouping is doing the work.")


if __name__ == "__main__":
    main()
