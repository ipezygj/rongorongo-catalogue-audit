"""Is the syllabary gap language-dependent, or is that an artefact of unmatched L?

Section 7 measures rongorongo against Rapa Nui and Maori at L=51-55 and gets
2.4-3.5x. Hawaiian, added for the genre control, sits at L=40 and gives 1.7-1.9x.
Those cannot be compared until the catalogue size is matched, because signal grows
with L for every series (that is the paper's own sweep result).

Here every reference is merged down to a common L by frequency (rarest folded into
one OTHER class), measured at matched N and rongorongo run lengths, and rongorongo
is merged to the same L under its four rules.
"""
import io, os, sys, random
from collections import Counter
sys.path.insert(0, ".")
from horley import stats, read_lines, tokens_plain, tokens_horley
from sweep import bin_map, apply, num_key
from syllabary_ref import syllabify, load_rap, load_mri, load_linb
from korovina_ref import clean, RAP_C
from fingerprint2 import object_runs
import glob

rng = random.Random(20260822)
MRI_C = ["ng","wh","h","k","m","n","p","r","t","w"]
HAW_C = ["h","k","l","m","n","p","w"]
LS = [30, 40, 55, 90]
o = []; p = o.append


def fold_to(runs, L):
    c = Counter(t for r in runs for t in r)
    keep = set(t for t, _ in c.most_common(L - 1))
    return [[t if t in keep else "OTHER" for t in r] for r in runs]


def recut(runs, lengths):
    flat = [t for r in runs for t in r]
    out, i, j = [], 0, 0
    while i < len(flat) and j < 100000:
        Ln = lengths[j % len(lengths)]
        out.append(flat[i:i+Ln]); i += Ln; j += 1
    return [r for r in out if len(r) > 1]


def sig_of(runs, shuffles=30):
    s = stats(runs)
    vals = []
    for _ in range(shuffles):
        sh = []
        for r in runs:
            q = r[:]; rng.shuffle(q); sh.append(q)
        vals.append(stats(sh)["hcn"])
    return s["hcn"], s["hcn"] - sum(vals)/len(vals), s["L"]


# references
haw_dir = os.path.expanduser("~/script-audit/ref/hawaiian")
def haw_lines(text):
    HAW=set("aeiouhklmnpw")
    out=[]
    for line in text.splitlines():
        for a,b in [("ʻ",""),("ʼ",""),("‘",""),("’",""),("`",""),
                    ("ā","a"),("ē","e"),("ī","i"),("ō","o"),("ū","u")]:
            line=line.replace(a,b)
        line=line.lower()
        ws=[w.strip(".,;:!?()[]\"'-–—…") for w in line.split()]
        ws=[w for w in ws if w and any(c.isalpha() for c in w)]
        if len(ws)<3: continue
        if sum(1 for w in ws if all((not c.isalpha()) or c in HAW for c in w))/len(ws) >= 0.8:
            out.append(" ".join(ws))
    return out

def syll(lines, cons):
    runs=[]
    for line in lines:
        cur,i,n=[],0,len(line)
        while i<n:
            c=""
            if line[i] in cons: c=line[i]; i+=1
            if i<n and line[i] in "aeiou": cur.append(c+line[i]); i+=1
            else:
                if c: continue
                i+=1
        if len(cur)>1: runs.append(cur)
    return runs

import re
prose_txt = "\n".join(io.open(os.path.join(haw_dir,f),encoding="utf-8",errors="replace").read()
                      for f in ["fornander_72686.txt","fornander_73166.txt"])
song_raw = io.open(os.path.join(haw_dir,"songs_raw.txt"),encoding="utf-8",errors="replace").read()
song_html = re.sub(r"<[^>]+>","\n", re.sub(r"<script.*?</script>|<style.*?</style>"," ",song_raw,flags=re.S))

refs = {
  "Rapa Nui NT":  syllabify(load_rap()[0], RAP_C, True),
  "Maori NT":     syllabify(load_mri(), MRI_C, True),
  "Rapa Nui Isla6": syllabify(clean(io.open("korovina_files/Isla6.txt",encoding="utf-8-sig").read())[0], RAP_C, True),
  "Hawaiian prose": syll(haw_lines(prose_txt), HAW_C),
  "Hawaiian song":  syll(haw_lines(song_html), HAW_C),
  "Linear B":     load_linb(),
}

objs={}
for path in sorted(glob.glob("ceipp/xml/*.xml")):
    r=object_runs(path,"horley")
    if sum(len(x) for x in r)>=100: objs[os.path.basename(path)[:-4]]=r
rr_runs=[r for runs in objs.values() for r in runs]
rr_lengths=sorted(len(r) for r in rr_runs)
N_RR=sum(len(r) for r in rr_runs)

lines=read_lines()
base=[r for s in lines for r in tokens_plain(s,True)]
horl=[r for s in lines for r in tokens_horley(s)]
base_types=sorted(Counter(t for r in base for t in r),key=num_key)
horl_types=sorted(Counter(t for r in horl for t in r),key=num_key)
base_freq=[t for t,_ in Counter(t for r in base for t in r).most_common()]

p("="*92)
p("EVERY REFERENCE AT THE SAME L, matched N=%d and rongorongo run lengths" % N_RR)
p("="*92)
p("%-17s %s" % ("reference", "  ".join("L=%-3d sig" % L for L in LS)))
for name, runs in refs.items():
    row=[name]
    for L in LS:
        r = recut(fold_to(runs, L), rr_lengths)
        flat=[t for x in r for t in x]
        if len(flat) > N_RR:
            acc,cut=0,[]
            for x in r:
                cut.append(x); acc+=len(x)
                if acc>=N_RR: break
            r=cut
        _h, sig, _L = sig_of(r)
        row.append(sig)
    p("%-17s %s" % (row[0], "  ".join("%+8.4f" % v for v in row[1:])))

p("")
p("rongorongo, best of the three catalogue rules at each L"
  "  (numeric cut, Horley cut where L<=125, frequency fold; random is a"
  "  baseline, not a candidate):")
row=["rongorongo"]
for L in LS:
    cands=[]
    cands.append(sig_of(apply(base, bin_map(base_types,L)))[1])
    if L<=len(horl_types): cands.append(sig_of(apply(horl, bin_map(horl_types,L)))[1])
    keep=set(base_freq[:L-1])
    cands.append(sig_of(apply(base,{t:(t if t in keep else "OTHER") for t in base_types}))[1])
    row.append(max(cands, key=abs))
p("%-17s %s" % (row[0], "  ".join("%+8.4f" % v for v in row[1:])))

txt="\n".join(o)
io.open("crosslang_L_results.txt","w",encoding="utf-8").write(txt+"\n")
sys.stdout.buffer.write((txt+"\n").encode("utf-8","replace"))
