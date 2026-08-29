"""Does song differ from prose on this instrument? Hawaiian, one culture, two genres.

Korovina (22 Aug 2026), on being told that Campbell's Rapa Nui collection behaves
differently from the other three: "the syntax of songs differs from ordinary prose,
although I am not sure if anyone has clearly specified exactly how", and pointed at
huapala.org for Hawaiian song and the Fornander collection for Hawaiian prose.

This matters for section 7. The genres the rongorongo tradition names -- kohau ika,
genealogies, litanies -- are chanted. The paper compares rongorongo against prose.

Confound controlled: huapala marks the glottal and vowel length, Fornander (1916-1919)
does not. Measuring them as they stand would compare orthographies, which is exactly
the effect measured in section 7 for Campbell. Both are therefore normalised to the
unmarked form, and the marked/unmarked contrast is reported separately.
"""
import io, os, re, sys, random, math
from collections import Counter
sys.path.insert(0, ".")
from horley import stats

D = os.path.expanduser("~/script-audit/ref/hawaiian")
rng = random.Random(20260822)
HAW = set("aeiouhklmnpw")
MARKS = {"ʻ": "", "ʼ": "", "‘": "", "’": "", "`": ""}
LONG = {"ā": "a", "ē": "e", "ī": "i", "ō": "o", "ū": "u"}
HAW_C = ["h", "k", "l", "m", "n", "p", "w"]
o = []; p = o.append


def unmark(t):
    for a, b in list(MARKS.items()) + list(LONG.items()):
        t = t.replace(a, b).replace(a.upper(), b.upper())
    return t


def hawaiian_lines(text, min_words=3, thresh=0.8):
    """Keep lines that are overwhelmingly Hawaiian by letter inventory."""
    out = []
    for line in text.splitlines():
        line = unmark(line).lower()
        words = [w.strip(".,;:!?()[]\"'-–—…") for w in line.split()]
        words = [w for w in words if w and any(c.isalpha() for c in w)]
        if len(words) < min_words:
            continue
        ok = sum(1 for w in words if all((not c.isalpha()) or c in HAW for c in w))
        if ok / len(words) >= thresh:
            out.append(" ".join(words))
    return out


def syllabify(lines):
    """(C)V runs, one run per line."""
    runs = []
    for line in lines:
        cur = []
        i, n = 0, len(line)
        while i < n:
            c = ""
            if line[i] in HAW_C:
                c = line[i]; i += 1
            if i < n and line[i] in "aeiou":
                cur.append(c + line[i]); i += 1
            else:
                if c: continue
                i += 1
        if len(cur) > 1:
            runs.append(cur)
    return runs


# --- songs ---
raw = io.open(os.path.join(D, "songs_raw.txt"), encoding="utf-8", errors="replace").read()
song_texts = raw.split("@@SONG ")[1:]
song_lines = []
for blk in song_texts:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", blk, flags=re.S)
    h = re.sub(r"<[^>]+>", "\n", h)
    h = h.replace("&nbsp;", " ").replace("&amp;", "&")
    song_lines += hawaiian_lines(h)

# --- prose ---
prose_lines = []
for f in ["fornander_72686.txt", "fornander_73166.txt"]:
    fp = os.path.join(D, f)
    if not os.path.exists(fp): continue
    t = io.open(fp, encoding="utf-8", errors="replace").read()
    i = t.find("*** START"); j = t.find("*** END")
    prose_lines += hawaiian_lines(t[i if i > 0 else 0: j if j > 0 else len(t)])

p("=" * 88)
p("HAWAIIAN SONG vs PROSE, both normalised to unmarked orthography")
p("=" * 88)
p("  songs: %d pages -> %d Hawaiian lines" % (len(song_texts), len(song_lines)))
p("  prose: %d Hawaiian lines" % len(prose_lines))

song = syllabify(song_lines)
prose = syllabify(prose_lines)
p("  song syllable tokens %d in %d runs (mean %.1f)"
  % (sum(len(r) for r in song), len(song), sum(len(r) for r in song) / max(1, len(song))))
p("  prose syllable tokens %d in %d runs (mean %.1f)"
  % (sum(len(r) for r in prose), len(prose), sum(len(r) for r in prose) / max(1, len(prose))))


def recut(runs, lengths):
    flat = [t for r in runs for t in r]
    out, i, j = [], 0, 0
    while i < len(flat) and j < len(lengths) * 40:
        L = lengths[j % len(lengths)]
        out.append(flat[i:i + L]); i += L; j += 1
    return [r for r in out if len(r) > 1]


def sample(runs, n):
    out, k = [], 0
    start = rng.randrange(len(runs))
    i = start
    while k < n and len(out) < len(runs):
        r = runs[i % len(runs)]
        out.append(r); k += len(r); i += 1
    return out


def measure(runs, shuffles=40):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    mu = sum(vals) / len(vals)
    return s, s["hcn"] - mu


def pats(runs):
    aa = aaa = abab = 0
    for r in runs:
        n = len(r)
        for i in range(n - 1):
            if r[i] == r[i + 1]:
                aa += 1
                if i + 2 < n and r[i + 2] == r[i]: aaa += 1
            if i + 3 < n and r[i] == r[i + 2] and r[i + 1] == r[i + 3] and r[i] != r[i + 1]:
                abab += 1
    return aa, aaa, abab


def ratio(runs, reps=12):
    obs = pats(runs); exp = [0.0] * 3
    for _ in range(reps):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        c = pats(sh)
        for j in range(3): exp[j] += c[j] / reps
    return [obs[j] / exp[j] if exp[j] > 0.5 else float("nan") for j in range(3)]


# match N and run lengths: use the song run-length profile for both
lens = sorted(len(r) for r in song)
N = min(sum(len(r) for r in song), sum(len(r) for r in prose))
p("  matched at N = %d, song run lengths" % N)
p("")
p("%-10s %5s %7s %8s %7s %7s %7s" % ("genre", "L", "Hcn", "signal", "AA", "AAA", "ABAB"))
res = {}
for name, runs in (("song", song), ("prose", recut(prose, lens))):
    rs = sample(runs, N)
    s, sig = measure(rs)
    r3 = ratio(rs)
    res[name] = (s, sig, r3)
    p("%-10s %5d %7.3f %+8.4f %7.2f %7.2f %7.2f"
      % (name, s["L"], s["hcn"], sig, r3[0], r3[1], r3[2]))
p("")
p("  rongorongo, best catalogue, matched null: Hcn 0.807 signal -0.047, AA 1.12 AAA 1.68 ABAB 20.7")

txt = "\n".join(o)
io.open("hawaiian_genre_results.txt", "w", encoding="utf-8").write(txt + "\n")
sys.stdout.buffer.write((txt + "\n").encode("utf-8", "replace"))
