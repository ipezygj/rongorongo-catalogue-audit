"""Robustness for the song/prose contrast: split-half, and the orthography effect."""
import io, os, sys, random
sys.path.insert(0, ".")
exec(open("hawaiian_genre.py", encoding="utf-8").read().split('p("=" * 88)')[0])


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


def measure(runs, shuffles=30):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    mu = sum(vals) / len(vals)
    return s, s["hcn"] - mu


o = []; p = o.append
raw = io.open(os.path.join(D, "songs_raw.txt"), encoding="utf-8", errors="replace").read()
blocks = raw.split("@@SONG ")[1:]

def lines_of(blks, keep_marks=False):
    out = []
    for blk in blks:
        h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", blk, flags=re.S)
        h = re.sub(r"<[^>]+>", "\n", h).replace("&nbsp;", " ")
        if keep_marks:
            # detect on the unmarked form but keep the marks in the output
            for line in h.splitlines():
                u = unmark(line).lower()
                ws = [w.strip(".,;:!?()[]\"'-–—…") for w in u.split()]
                ws = [w for w in ws if w and any(c.isalpha() for c in w)]
                if len(ws) < 3: continue
                ok = sum(1 for w in ws if all((not c.isalpha()) or c in HAW for c in w))
                if ok / len(ws) >= 0.8:
                    out.append(line.lower().strip())
        else:
            out += hawaiian_lines(h)
    return out

def syll_marked(lines):
    """(C)V with the glottal as its own consonant and long vowels distinct."""
    runs = []
    cons = ["h","k","l","m","n","p","w","ʻ","’","‘"]
    for line in lines:
        cur, i, n = [], 0, len(line)
        while i < n:
            c = ""
            if line[i] in cons: c = "ʻ" if line[i] in "’‘ʻ" else line[i]; i += 1
            if i < n and line[i] in "aeiouāēīōū":
                cur.append(c + line[i]); i += 1
            else:
                if c: continue
                i += 1
        if len(cur) > 1: runs.append(cur)
    return runs

def ratio(runs, reps=12):
    obs = pats(runs); exp=[0.0]*3
    for _ in range(reps):
        sh=[]
        for r in runs:
            q=r[:]; rng.shuffle(q); sh.append(q)
        c=pats(sh)
        for j in range(3): exp[j]+=c[j]/reps
    return [obs[j]/exp[j] if exp[j]>0.5 else float("nan") for j in range(3)]

p("=" * 84)
p("SPLIT-HALF: is the song AAA excess stable across two disjoint halves?")
p("=" * 84)
half = len(blocks)//2
for lab, blks in (("songs A (%d)" % half, blocks[:half]), ("songs B (%d)" % (len(blocks)-half), blocks[half:])):
    r = syllabify(lines_of(blks))
    n = sum(len(x) for x in r)
    r3 = ratio(r)
    p("  %-16s tokens %6d   AA %.2f  AAA %.2f  ABAB %.2f" % (lab, n, *r3))

prose_lines=[]
for f in ["fornander_72686.txt","fornander_73166.txt"]:
    t=io.open(os.path.join(D,f),encoding="utf-8",errors="replace").read()
    i=t.find("*** START"); j=t.find("*** END")
    prose_lines += hawaiian_lines(t[i if i>0 else 0 : j if j>0 else len(t)])
pr = syllabify(prose_lines)
ph = len(pr)//2
for lab, sub in (("prose A", pr[:ph]), ("prose B", pr[ph:])):
    r3 = ratio(sub)
    p("  %-16s tokens %6d   AA %.2f  AAA %.2f  ABAB %.2f"
      % (lab, sum(len(x) for x in sub), *r3))

p("")
p("=" * 84)
p("ORTHOGRAPHY, reported separately as promised: songs with marks kept")
p("=" * 84)
marked = syll_marked(lines_of(blocks, keep_marks=True))
unmarked = syllabify(lines_of(blocks))
for lab, r in (("marked", marked), ("unmarked", unmarked)):
    s, sig = measure(r, shuffles=30)
    r3 = ratio(r)
    p("  %-9s L=%3d tokens %6d  Hcn %.3f  signal %+.4f   AA %.2f AAA %.2f ABAB %.2f"
      % (lab, s["L"], s["n"], s["hcn"], sig, *r3))

txt="\n".join(o)
io.open("hawaiian_genre2_results.txt","w",encoding="utf-8").write(txt+"\n")
sys.stdout.buffer.write((txt+"\n").encode("utf-8","replace"))
