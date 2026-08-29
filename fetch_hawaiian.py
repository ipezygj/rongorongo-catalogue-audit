"""Fetch a Hawaiian song corpus (huapala.org) and locate the Fornander prose.

Korovina (22 Aug 2026): song syntax differs from prose, "although I am not sure
if anyone has clearly specified exactly how", and pointed at these sources. The
comparison matters here because the genres the rongorongo tradition names -
kohau ika, genealogies, litanies - are chanted, not narrated, and section 7
compares rongorongo against prose only.

Hawaiian is the right control: same family, same (C)V canon, and both a song
corpus and a prose corpus survive from one culture.
"""
import io, os, re, time, urllib.request, urllib.error

D = os.path.expanduser("~/script-audit/ref/hawaiian")
os.makedirs(D, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (research; contact ilpo@ipezygj.com)"}
BASE = "https://www.huapala.org/"


def get(url, timeout=40):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


idx = get(BASE)
index_pages = sorted(set(re.findall(r'href="((?:[Ii]ndex[^"]*)\.html)"', idx)))
print("index pages:", len(index_pages))

songs = set()
for ip in index_pages:
    try:
        h = get(BASE + ip)
    except Exception as e:
        print("  skip", ip, e); continue
    for l in re.findall(r'href="([^"]+\.html)"', h):
        if "ndex" not in l and not l.startswith("http"):
            songs.add(l)
    time.sleep(0.4)
songs = sorted(songs)
print("song pages found:", len(songs))

LIMIT = 260
got = 0
out = io.open(os.path.join(D, "songs_raw.txt"), "w", encoding="utf-8")
for s in songs[:LIMIT]:
    try:
        h = get(BASE + s)
    except Exception:
        continue
    out.write("\n@@SONG %s\n" % s)
    out.write(h)
    got += 1
    time.sleep(0.35)
out.close()
print("song pages downloaded:", got)
