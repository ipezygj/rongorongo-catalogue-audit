"""Fetch every input the scripts need. Nothing here is redistributed in the
repository; each source keeps its own licence and is downloaded from where its
maintainers publish it.

  ceipp/xml/A.xml .. Y.xml   CEIPP transliteration, Philip Spaelti's XML edition
                             (kohaumotu.org). The site's TLS certificate is
                             expired, so plain http is used; the server also
                             rejects requests without a browser-like UA.
  ceipp/digit.html           CEIPP's own fixed-column sample (verify_ceipp.py)
  rongopy/                   github.com/jgregoriods/rongopy (GPL-3.0): the
                             Barthel -> Horley map and the tablets/*.json used
                             by measure.py / power.py / normalized.py.
  ref/mri/                   Maori New Testament, ebible.org (public domain)
  ref/LinearBInscriptions.js linearb.xyz corpus (github.com/mwenge/linearb.xyz)
  indus/data/                Mahadevan 1977 concordance + EBUDS (github.com/Hamilchin/
                             indus-cipherable) for indus/indus.py
  ref/rap/rap_nt.txt         Rapa Nui New Testament, Wycliffe, from bible.com
                             (copyright Wycliffe Bible Translators). Fetched
                             page by page with a delay; used for MEASUREMENT
                             ONLY in syllabary_ref.py and never redistributed.
                             Pass --no-rap to skip it.

Usage:  python fetch_data.py [--no-rap]
"""
import html
import io
import os
import re
import subprocess
import sys
import time
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
      "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()


def fetch_ceipp():
    d = os.path.join(HERE, "ceipp", "xml")
    os.makedirs(d, exist_ok=True)
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXY":
        p = os.path.join(d, c + ".xml")
        if os.path.exists(p):
            continue
        b = get("http://kohaumotu.org/Rongorongo/xml/%s.xml" % c)
        open(p, "wb").write(b)
        print("ceipp", c, len(b))
        time.sleep(0.5)
    p = os.path.join(HERE, "ceipp", "digit.html")
    if not os.path.exists(p):
        open(p, "wb").write(get("http://kohaumotu.org/rongorongo_org/corpus/digit.html"))
        print("ceipp digit.html")


def fetch_rongopy():
    d = os.path.join(HERE, "rongopy")
    if os.path.exists(os.path.join(d, "horley_encoding.py")):
        return
    subprocess.check_call(["git", "clone", "--depth", "1",
                           "https://github.com/jgregoriods/rongopy.git", d])


def fetch_mri():
    d = os.path.join(HERE, "ref", "mri")
    if os.path.isdir(d) and any(f.endswith("_read.txt") for f in os.listdir(d)):
        return
    os.makedirs(d, exist_ok=True)
    b = get("https://ebible.org/Scriptures/mri_readaloud.zip")
    zipfile.ZipFile(io.BytesIO(b)).extractall(d)
    print("mri", len(os.listdir(d)), "files")


INDUS_FILES = ["IM77/indus_script_IM77_concordance.txt", "IM77/data_M77.txt", "IM77/IM77_symbol_freq.csv", "ebuds/data_EBUDS_UNIQUE.txt"]


def fetch_indus():
    d = os.path.join(HERE, "indus", "data")
    os.makedirs(d, exist_ok=True)
    for f in INDUS_FILES:
        p = os.path.join(d, os.path.basename(f))
        if os.path.exists(p):
            continue
        for br in ("main", "master"):
            try:
                open(p, "wb").write(get("https://raw.githubusercontent.com/Hamilchin/indus-cipherable/%s/data/%s" % (br, f)))
                print("indus", f)
                break
            except Exception:
                continue


def fetch_linb():
    p = os.path.join(HERE, "ref", "LinearBInscriptions.js")
    if os.path.exists(p):
        return
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(get("https://raw.githubusercontent.com/mwenge/linearb.xyz/master/LinearBInscriptions.js"))
    print("linearb", os.path.getsize(p))


BOOKS = {"MAT": 28, "MRK": 16, "LUK": 24, "JHN": 21, "ACT": 28}


def fetch_rap():
    d = os.path.join(HERE, "ref", "rap")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "rap_nt.txt")
    done = set()
    if os.path.exists(p):
        done = {l.strip()[3:] for l in open(p, encoding="utf-8") if l.startswith("## ")}
    out = open(p, "a", encoding="utf-8")
    for b, n in BOOKS.items():
        for c in range(1, n + 1):
            key = "%s %d" % (b, c)
            if key in done:
                continue
            try:
                s = get("https://www.bible.com/bible/2164/%s.%d.rap" % (b, c)).decode("utf-8", "ignore")
            except Exception as e:
                print("rap ERR", key, e)
                time.sleep(3)
                continue
            i = s.find('data-testid="chapter-content"')
            j = s.find("Learn More About Rapa Nui", i)
            if i < 0 or j < 0:
                print("rap NOCONTENT", key)
                continue
            txt = re.sub(r"<[^>]+>", " ", s[i:j])
            txt = html.unescape(re.sub(r"\s+", " ", txt))
            out.write("## %s\n%s\n" % (key, txt))
            out.flush()
            print("rap", key)
            time.sleep(0.7)


if __name__ == "__main__":
    fetch_ceipp()
    fetch_rongopy()
    fetch_mri()
    fetch_linb()
    fetch_indus()
    if "--no-rap" not in sys.argv:
        fetch_rap()
    print("done")
