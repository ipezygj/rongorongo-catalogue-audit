"""Resume the huapala download to the full 1331 songs, skipping what is already held."""
import io, os, re, time, urllib.request

D = os.path.expanduser("~/script-audit/ref/hawaiian")
UA = {"User-Agent": "Mozilla/5.0 (research; contact ilpo@ipezygj.com)"}
BASE = "https://www.huapala.org/"
RAW = os.path.join(D, "songs_raw.txt")


def get(url, timeout=40):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


have = set(re.findall(r"@@SONG (\S+)", io.open(RAW, encoding="utf-8", errors="replace").read()))
print("already held:", len(have))

idx = get(BASE)
songs = set()
for ip in sorted(set(re.findall(r'href="((?:[Ii]ndex[^"]*)\.html)"', idx))):
    try:
        h = get(BASE + ip)
    except Exception:
        continue
    for l in re.findall(r'href="([^"]+\.html)"', h):
        if "ndex" not in l and not l.startswith("http"):
            songs.add(l)
    time.sleep(0.2)
todo = sorted(songs - have)
print("total songs:", len(songs), "| to fetch:", len(todo))

got = fail = 0
with io.open(RAW, "a", encoding="utf-8") as out:
    for s in todo:
        try:
            h = get(BASE + s)
        except Exception:
            fail += 1
            continue
        out.write("\n@@SONG %s\n" % s)
        out.write(h)
        got += 1
        if got % 100 == 0:
            out.flush(); print("  fetched", got, flush=True)
        time.sleep(0.15)
print("fetched:", got, "| failed:", fail)
