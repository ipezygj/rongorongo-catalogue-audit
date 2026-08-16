# The Catalogue Is the Instrument

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21964265.svg)](https://doi.org/10.5281/zenodo.21964265)

How the choice of sign inventory moves the statistics of an undeciphered script,
measured on rongorongo. Code, results and paper draft.

**Paper:** `paper/paper.pdf` (draft, August 2026; arXiv link to follow).
**Cite the code:** doi:10.5281/zenodo.21964265 (concept DOI, resolves to the latest version; v0.1.1 = 10.5281/zenodo.21964266).
Author: Ilpo Väätäinen. Correspondence with Evgeniya Korovina (Institute of
Linguistics, RAS) shaped the questions in §5–§7; see acknowledgements.

## The claim in one paragraph

Three published readings of the same 25 rongorongo inscriptions (CEIPP with
variants, L = 1 897; CEIPP numeric, L = 633; Horley's basic glyphs, L = 125)
move the length-normalised conditional entropy of Rao et al. (2010) by 0.318 of
its [0, 1] scale. The corpus's distance from its own unigram-matched shuffle —
the structure the statistic is meant to detect — is 0.077. The catalogue moves
the instrument about four times further than the signal. A sweep over
catalogue sizes shows the effect is mostly *size*; composition matters for a
different question (which signs the scribes interchanged); and real
syllabaries — Rapa Nui, Māori, Linear B — at matched size and length have
2.5–10× more sequential structure than rongorongo under any catalogue, even
where the raw numbers coincide.

## Reproduce

Standard-library Python 3.10+; no packages. `git` for one clone.

```
python fetch_data.py          # ~15 MB; add --no-rap to skip the Rapa Nui text
python horley.py              # Table 1  (ladder, 4.1x)          -> results/horley_results.txt
python miller_madow.py        # Table 1 note (MM correction, 3.7x)-> results/mm_results.txt
python sweep.py               # Table 2  (size sweep, 15 sizes)  -> results/sweep_results.txt      ~2 min
python composition2.py        # §6 core-held composition (0.004) -> results/composition2_results.txt
python parallels3.py          # §6 scribes' substitutions table  -> results/parallels3_results.txt
python syllabary_ref.py       # Table 3  (syllabary references)  -> results/syllabary_ref_results.txt ~3 min
python noise.py               # §8 transliteration-error test    -> results/noise_results.txt
python decipher.py            # Appendix A calibrated decipherment  -> results/decipher_results.txt   ~3 min
python robustness.py          # §7 run-length + sample-size checks -> results/robustness_results.txt ~6 min
```

Earlier / supporting runs: `measure.py`, `power.py`, `normalized.py` (rongopy
JSON tablets, 13 objects — the first pass), `ceipp_run.py` (CEIPP XML with the
author's own reductions, before the Horley map), `verify_ceipp.py` (shows the
rongopy tablets are the CEIPP transliteration reformatted, 15/15),
`composition.py`, `parallels.py`, `parallels2.py` (the unfair-set version;
`parallels3.py` is the one in the paper).

Random seeds are fixed. Console headings are partly in Finnish; the files in
`results/` are what the paper's tables were transcribed from.

## Data (fetched, not redistributed)

| what | from | licence / note |
|---|---|---|
| CEIPP transliteration, XML | kohaumotu.org/Rongorongo/xml/ (Philip Spaelti) | as published there; cite CEIPP |
| Barthel → Horley map, tablets JSON | github.com/jgregoriods/rongopy | GPL-3.0 (cloned into `rongopy/`, not vendored) |
| Māori New Testament | ebible.org `mri_readaloud.zip` | public domain |
| Linear B corpus | github.com/mwenge/linearb.xyz | see that repository |
| Rapa Nui New Testament | bible.com (Wycliffe) | © Wycliffe Bible Translators; measurement only, never stored here |

## Method in brief

Plug-in conditional entropy H(bigram) − H(unigram), normalised by log₂ L
(Rao et al. 2010). Null = tokens permuted with run lengths kept (unigram
distribution and L identical). Signal = real − null mean; z over null s.d.
Coverage = share of the L×L bigram table observed. Bigrams counted only across
attested adjacencies: line breaks, lacunae, illegible and end markers cut the
chain. Merge rules for the sweep: Barthel-adjacent, Horley-then-numeric,
frequency-pooled, random partitions.

## Licence

Code and text in this repository: MIT. Data sources keep their own licences
(table above).
