"""The ligature question asked of AA and AAA, not only of ABAB.

ABAB was checked because Davletshin asked about an ABAB event (27 Aug 2026).
The sibling patterns are counted by the same pipeline off the same decomposed
stream, so they carry the same exposure and have to be measured rather than
assumed clean. An event is "ligature-free" when its slots sit on that many
distinct physical glyphs: two for AA, three for AAA, four for ABAB. The same
restriction is applied inside every shuffle, so the ratio stays like-for-like.
"""
import io, sys, glob, os, random
sys.path.insert(0, ".")
from davletshin_locate import object_runs_prov, gid

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
rng = random.Random(20260827)
REPS = 12


def counts(runs, strict):
    aa = aaa = abab = 0
    for r in runs:
        n = len(r)
        for i in range(n - 1):
            if r[i][0] == r[i + 1][0]:
                if not (strict and r[i][1] == r[i + 1][1]):
                    aa += 1
                if i + 2 < n and r[i + 2][0] == r[i][0]:
                    if not (strict and len(set(d[1] for d in r[i:i + 3])) < 3):
                        aaa += 1
            if i + 3 < n and r[i][0] == r[i + 2][0] and r[i + 1][0] == r[i + 3][0] \
                    and r[i][0] != r[i + 1][0]:
                if not (strict and len(set(d[1] for d in r[i:i + 4])) < 4):
                    abab += 1
    return aa, aaa, abab


for floor in (100, 300):
    objs = {}
    for path in sorted(glob.glob("ceipp/xml/*.xml")):
        r = [[(d["t"], gid(d)) for d in run] for run in object_runs_prov(path)]
        if sum(len(x) for x in r) >= floor:
            objs[os.path.basename(path)[:-4]] = r
    obs = [0, 0, 0]
    obs_s = [0, 0, 0]
    exp = [0.0, 0.0, 0.0]
    exp_s = [0.0, 0.0, 0.0]
    for runs in objs.values():
        c = counts(runs, False)
        cs = counts(runs, True)
        for j in range(3):
            obs[j] += c[j]
            obs_s[j] += cs[j]
        for _ in range(REPS):
            flat = [t for r in runs for t in r]
            rng.shuffle(flat)
            sh, i = [], 0
            for r in runs:
                sh.append(flat[i:i + len(r)])
                i += len(r)
            e = counts(sh, False)
            es = counts(sh, True)
            for j in range(3):
                exp[j] += e[j] / REPS
                exp_s[j] += es[j] / REPS
    print("\nobjects >= %d tokens: %d" % (floor, len(objs)), file=out)
    print("  %-6s %7s %8s %6s | %7s %8s %6s | ligature share of observed"
          % ("", "obs", "exp", "ratio", "obs*", "exp*", "ratio*"), file=out)
    for j, lab in enumerate(("AA", "AAA", "ABAB")):
        print("  %-6s %7d %8.2f %6.2f | %7d %8.2f %6.2f | %.1f%%"
              % (lab, obs[j], exp[j], obs[j] / exp[j],
                 obs_s[j], exp_s[j], obs_s[j] / exp_s[j],
                 100.0 * (obs[j] - obs_s[j]) / obs[j] if obs[j] else 0.0), file=out)
out.flush()
