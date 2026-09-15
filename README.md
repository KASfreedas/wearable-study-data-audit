# Wearable Study Data Audit

This audit checks whether Fitbit record dates can be treated as study-exposure dates. Their
disagreement with published collection windows shows why that assumption needs verification.

![Figure 1 — released Fitbit records extend well beyond the published collection windows](figure1_light.png)

## What the audit found

**The discrepancy.** 2,501 of 7,410 Fitbit participant-days (33.8%) fall outside both
published collection windows, affecting 68 of 71 participants. Measured the same way,
scheduled survey prompts put 70 of 3,886 participant-days (1.8%) outside, affecting 2
of 63. Device-record availability cannot be used uncritically as a participant's
study-exposure window.

**The correction.** Observation windows were rebuilt from each participant's first scheduled
survey prompt, a date the study itself generated. Doing so exposed a calendar-date defect that
had shifted every window by one day, and the rebuilt analysis counts *expected* participant-days
rather than only the rows that exist — so missing days stay in the denominator instead of
disappearing from it. 18 of 2,940 expected participant-days in the 49-day window have no
source row at all.

**What it still does not establish.** A first scheduled prompt is a *chosen* study-generated
anchor, not a verified study start; nothing in the release establishes enrolment or consent
dates. 8 of 71 participants have no scheduled prompt, so no SEMA-based window can be
assigned to them. The two exports also cover different populations — 71 participants against
63 — so the percentages above describe the exports, not a controlled comparison on
identical participants.

## Secondary analysis

![Figure 2 — usable-day attainment under two definitions](figure2_light.png)

The question that started the project was a planning one: how many participants would need to
be enrolled to finish with 50 who have enough usable data? The committed 49-day horizon was
retained after corrected execution of the selection rule yielded 50. If this cohort's observed
yields carried over to a future study, the two definitions of "usable" imply approximately 57
versus 59 recruits to obtain 50 completers **in expectation** — they do not guarantee 50
completers, and this cohort is one protocol on one device.
**The pre-specified headline criterion was not met** — the bootstrap 95% CI for the yield ratio
is 0.9038 to 1.0000, which includes 1.0 — so this is reported as an inconclusive secondary
result. It is not a finding of no difference. The audit above is the contribution.

## Reproducing it

The raw dataset is not committed. To verify the artifacts from source:

```bash
# 1. download LifeSnaps (Zenodo 7229547) and place all four raw inputs in data/
#    (two CSVs and two .bson files - exact filenames in VERIFY.md)
# 2. rebuild every published number from source
python3 build_numbers.py
# 3. run the suite - the gate is exit 0, meaning failed=0 AND skipped=0
python3 run_tests.py
```

Both commands take no arguments once the files are in `data/`. `build_numbers.py` also accepts
explicit `--data-dir`, `--sema-dir` and `--out-dir` if the inputs live elsewhere.

A fresh clone has no `data/` and exits **3 (INCOMPLETE)**: the tests that can run still verify
their own components, but the pipeline is unverified until the data is staged. `build_numbers.py`
rebuilds byte-identically into an empty directory, and the suite checks that against the
committed artifacts.

Every number in these figures and documents is a key in [`numbers.json`](numbers.json),
regenerated from source by [`build_numbers.py`](build_numbers.py).

## Contents

| File | What it is |
|---|---|
| [`SUMMARY.md`](SUMMARY.md) | the short plain-language explanation |
| [`RESULT.md`](RESULT.md) | full result, both figures, all denominators |
| [`WINDOW_RULE.md`](WINDOW_RULE.md) | the frozen specification, and §8 the execution defects found and corrected |
| [`CHANGELOG.md`](CHANGELOG.md) | every correction made after review |
| [`VERIFY.md`](VERIFY.md) | how to stage the data and what the exit codes mean |
| [`PROJECT.md`](PROJECT.md) | superseded planning document, kept as the record of what was corrected |
| [`CRITERIA.md`](CRITERIA.md) | original pre-registration and amendments; design parameters superseded by `WINDOW_RULE.md` |
| `figure1.py`, `figure2.py` | regenerate both figures; each asserts its caption against `numbers.json` before writing |
| `test_adherence.py`, `run_tests.py` | 47 tests across thirteen contracts |

## Data

LifeSnaps: Yfantidou et al., *Scientific Data* 2022.
[doi:10.1038/s41597-022-01764-x](https://doi.org/10.1038/s41597-022-01764-x) ·
[Zenodo 7229547](https://doi.org/10.5281/zenodo.7229547) · CC-BY 4.0.
Published collection-round windows are taken from the dataset paper.

Repository: https://github.com/KASfreedas/wearable-study-data-audit
