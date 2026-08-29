"""How stable is the ABAB observed/expected ratio the paper reports?

Table 2 gives ABAB 20.7 under the per-object null, from twelve shuffles. The
expectation behind it is of the order of ten events, so twelve shuffles put a
small, noisy number in the denominator. Before the ligature correction is
quoted as a change in that ratio, the ratio's own error has to be known: the
spread of twelve-shuffle estimates over independent seeds, against one estimate
made with enough shuffles to be stable.
"""
import io, sys, glob, os, random, statistics
sys.path.insert(0, ".")
from davletshin_locate import object_runs_prov, gid

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def abab(runs, strict):
    n = 0
    for r in runs:
        for i in range(len(r) - 3):
            if r[i][0] == r[i + 2][0] and r[i + 1][0] == r[i + 3][0] and r[i][0] != r[i + 1][0]:
                if strict and len(set(d[1] for d in r[i:i + 4])) < 4:
                    continue
                n += 1
    return n


def expected(objs, strict, reps, seed):
    rng = random.Random(seed)
    tot = 0.0
    for runs in objs.values():
        for _ in range(reps):
            flat = [t for r in runs for t in r]
            rng.shuffle(flat)
            sh, i = [], 0
            for r in runs:
                sh.append(flat[i:i + len(r)])
                i += len(r)
            tot += abab(sh, strict) / reps
    return tot


for floor in (300,):
    objs = {}
    for path in sorted(glob.glob("ceipp/xml/*.xml")):
        r = [[(d["t"], gid(d)) for d in run] for run in object_runs_prov(path)]
        if sum(len(x) for x in r) >= floor:
            objs[os.path.basename(path)[:-4]] = r
    o_all = sum(abab(runs, False) for runs in objs.values())
    o_str = sum(abab(runs, True) for runs in objs.values())
    print("\nobjects >= %d tokens: %d | observed ABAB %d, ligature-free %d"
          % (floor, len(objs), o_all, o_str), file=out)

    twelve = [o_all / expected(objs, False, 12, s) for s in range(20260901, 20260921)]
    print("  twelve-shuffle ratio over 20 seeds: min %.1f  median %.1f  max %.1f  sd %.1f"
          % (min(twelve), statistics.median(twelve), max(twelve), statistics.stdev(twelve)), file=out)

    e_all = expected(objs, False, 400, 20260827)
    e_str = expected(objs, True, 400, 20260827)
    print("  400 shuffles: all events   observed %4d  expected %6.2f  ratio %5.1f"
          % (o_all, e_all, o_all / e_all), file=out)
    print("  400 shuffles: ligature-free observed %4d  expected %6.2f  ratio %5.1f"
          % (o_str, e_str, o_str / e_str), file=out)
    print("  fall in the ratio: %.1f%%   fall in the observed count: %.1f%%"
          % (100 * (1 - (o_str / e_str) / (o_all / e_all)), 100 * (1 - o_str / o_all)), file=out)
out.flush()
