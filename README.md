# How the Choice of Sign Inventory Moves the Statistics of an Undeciphered Script

[![Paper DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22057706.svg)](https://doi.org/10.5281/zenodo.22057706)
[![Code DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21964265.svg)](https://doi.org/10.5281/zenodo.21964265)

How the choice of sign inventory moves the statistics of an undeciphered script,
measured on rongorongo. Code, results and paper draft.

**Paper:** `paper/paper.pdf`, preprint of September 2026 — doi:10.5281/zenodo.22057706
(concept DOI, resolves to the latest version; the deposit this repository now
matches is 10.5281/zenodo.22257931, 2 September 2026).

Version 10 changes no result, table or figure. It adds Davletshin's own caveat on
ABAB, that he reads those alternations as rhetorical repetition and not as
morphological reduplication (p.c., 1 September 2026), so that the cross-language
comparison is stated as a fact about the rate and not about the mechanism. It
repairs a cross-reference in the robustness section that had lost its backslash:
versions since the clarity pass of 29 August print "The ratio in Table~
ef{tab:ladder}" where the table number should be, because LaTeX saw ordinary words,
raised no warning and set them. And it unpacks 125 em dashes in the prose.

Version 9 corrects a sign identification that reversed one of the paper's own
results. Versions 1–8 gave Davletshin's "*Staff" sign as Barthel 200; it is
Barthel 001 (R. Wieczorek, p.c., 2 September 2026), and the figures printed under
that name were 200's. Corrected, *Staff is the leading ABAB carrier of the 125
sign types at 2.4 times the ligature-corrected median, where it had been reported
as a median sign ranking high only through its frequency. 200 looked like the
corpus's commonest sign only because the Horley map folds eight Barthel codes into
it — which makes the mistake an instance of what this paper measures.
`davletshin_locate.py` now runs the ligature audit per sign as well as on the
total, and a plain-language conclusion has been added (§11).
**Not redistributed:** `korovina_ref.py` and `campbell_probe.py` read four Rapa Nui text
collections sent privately by E. Korovina. They are not in this repository and `fetch_data.py`
does not download them; those two scripts will not run without them. Everything else does.

**Cite the code:** doi:10.5281/zenodo.21964265 (concept DOI; v0.1.1 = 10.5281/zenodo.21964266).
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
python mamari.py              # Appendix A Mamari calendar anchor    -> results/mamari_results.txt     ~3 min
python mixed.py               # Appendix A mixed model (fails control) -> results/mixed_results.txt   ~5 min
python fingerprint.py          # Appendix A repetition fingerprint    -> results/fingerprint_results.txt
python indus/indus.py          # Table 4 Indus on the same instrument  -> indus/indus_results.txt   ~2 min
python robustness.py          # §7 run-length + sample-size checks -> results/robustness_results.txt ~6 min
```

Added since the first release; each is named in the paper where its number appears:

```
python pseudoglyph_audit.py     # the two CEIPP codes that are not signs
python coverage_symmetry.py     # rongorongo and Indus coverage on one grid, one rule
python indus_published_range.py # the published Indus catalogues, same instrument
python crosslang_L.py           # is the syllabary gap language-dependent, or unmatched L?
python hawaiian_genre.py        # song against prose, one language
python genres_mri2.py           # chant against narrative, Maori
python genealogy.py             # genealogy: the genre the rongorongo tradition names
python robust_all.py            # Table 9: every claim under the stricter null
python null_choice3.py          # AA, AAA and ABAB under three nulls
python ligature_aa.py           # the ligature check asked of AA and AAA, not only ABAB
python abab_null_stability.py   # how stable the ABAB ratio is across seeds
python fingerprint2.py          # per-object repetition, and the Santiago Staff
python davletshin_classes.py    # Davletshin's combinatorial-class claim, measured
python davletshin_signs.py      # his deciphered signs against the ABAB/AAA ranking
python davletshin_locate.py     # where those ABAB events sit in the CEIPP XML
```

Some of these exist because a correspondent asked rather than because we planned
them: `indus_published_range.py` after R. Sproat asked whether the Indus sign lists
move their own statistics, and the Davletshin scripts after A. Davletshin asked to
see the lines the events sit on rather than the counts. Both answers went into the
paper, and one of them took a claim out of it.

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
| Mahadevan 1977 concordance + EBUDS | github.com/Hamilchin/indus-cipherable | see that repository |
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
