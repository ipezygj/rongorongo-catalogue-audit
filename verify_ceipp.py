"""Parity check: is rongopy's tablets.json actually the CEIPP transliteration?

CEIPP publishes a fixed-column sample of its digitised corpus on
kohaumotu.org. Each row carries the object/side/line id, a sign code, and a
separator character in the final column. rongopy stores the same material as
one inline string per line.

If the reconstruction from the published sample reproduces rongopy byte for
byte, the base encoding is CEIPP and not a rongopy invention -- which decides
whether the measurement rests on an independent published source.
"""
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_HTML = os.path.join(HERE, "ceipp", "digit.html")
TABLETS = os.path.join(HERE, "rongopy", "ga_lstm", "tablets", "tablets.json")

# Rows look like: "Aa01 001 430----- ! ."  -- id, index, code padded with
# hyphens, an optional modifier, then the separator that follows the sign.
ROW = re.compile(
    r"\bAa01\s+(\d{3})\s+([0-9]{3}[a-z]*)-*\s*(!?)\s*([.\-])",
)


def main():
    html = io.open(SAMPLE_HTML, encoding="utf-8", errors="replace").read()
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ")
    text = re.sub(r"[ \t]+", " ", text)

    rows = ROW.findall(text)
    if not rows:
        print("CEIPP-naytteesta ei saatu riveja irti — tarkista jasennin")
        return 1

    rows.sort(key=lambda r: int(r[0]))
    rebuilt = "".join(f"{code}{bang}{sep}" for _idx, code, bang, sep in rows)
    print(f"CEIPP-naytteesta jasennetty {len(rows)} merkkia (Aa01 001-"
          f"{rows[-1][0]})")
    print("  rekonstruktio:", rebuilt)

    aa1 = json.load(io.open(TABLETS, encoding="utf-8"))["A"]["Aa1"]
    prefix = aa1[:len(rebuilt)]
    print("  rongopy Aa1   :", prefix)

    if prefix == rebuilt:
        print()
        print(f"TASMAA taydellisesti {len(rows)}/{len(rows)} merkin osalta.")
        print("=> rongopy/tablets.json ON CEIPP:n transliteraatio, "
              "vain eri muotoiltuna.")
        return 0

    print()
    print("EI TASMAA. Ensimmainen ero:")
    for i, (a, b) in enumerate(zip(rebuilt, prefix)):
        if a != b:
            print(f"  kohta {i}: odotettu {a!r}, saatu {b!r}")
            break
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
