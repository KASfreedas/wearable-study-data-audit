# Verifying this analysis

Setup, verification, and optional regeneration — **in that order**. Verify the checkout you
were given *before* regenerating anything, or the rebuild overwrites the very reference the
isolated-build test compares against. This matters most for the `.bson` hashes, which are
recorded in `numbers.json` rather than independently pinned: regenerate first and they are
simply whatever you just built from.

## 1. Get the data

Raw data is not included; obtain it from the original source. Download
`rais_anonymized.zip` from Zenodo record **7229547**
(<https://doi.org/10.5281/zenodo.7229547>), unzip it, and copy **all four** raw inputs into
`./data/`, keeping their original filenames:

```
rais_anonymized/csv_rais_anonymized/daily_fitbit_sema_df_unprocessed.csv
rais_anonymized/csv_rais_anonymized/hourly_fitbit_sema_df_unprocessed.csv
rais_anonymized/mongo_rais_anonymized/sema.bson
rais_anonymized/mongo_rais_anonymized/surveys.bson
```

Confirm you have the same bytes:

```
sha256sum data/*.csv
# daily  82c84ee495be4b0ff636a8a44271ffb124e2358d9dd52012b529b897f3d54963
# hourly 99ecc8e2e0a5d7cfd766de835e97aef62b08d1ff767a73185f2d14fed0aed8fd
```

Both CSV hashes are pinned in `src/adherence.py` and checked on every build. A mismatch stops
the build rather than producing numbers from different bytes. The `.bson` hashes are recorded
in `numbers.json` (`input_sha256_sema_bson`, `input_sha256_surveys_bson`) rather than pinned,
so a different export is visible but not fatal.

## 2. Verify the checkout, before changing anything

```
pip install -r requirements.txt
python3 run_tests.py
```

Run this against the **untouched** checkout. The suite rebuilds everything from source into
two temporary directories of its own and compares the result against the committed
`numbers.json`, `grid_H49.csv`, `exposure_windows.csv` and `usable_days_H49.csv`. It never
writes to those four files. That comparison is the verification — and it is only meaningful
while the committed copies are the ones you were given.

The figure tests render into temporary directories too. They check that each script exits 0 —
which means it asserted every caption number against `numbers.json` — and that the render's
pixel dimensions match the committed PNG. They do **not** compare PNG bytes: matplotlib output
depends on installed fonts, FreeType and libpng, so a correct render on another machine is
legitimately different at the byte level. Pixel dimensions come from `figsize x dpi` and are
deterministic.

No committed artifact — data or figure — is written during a test run; verified by
modification time, not only by hash.

pytest is not installable in the analysis container, so `run_tests.py` installs a minimal
compatible shim only when the real package is absent. Exit codes are three-way on purpose,
because "nothing ran" and "most of it skipped" both print `failed=0` and both read as green:

| exit | meaning |
|---|---|
| 0 | every collected test executed and passed — the only state that verifies the pipeline |
| 1 | a test failed |
| 2 | zero tests executed; an empty suite is not a passing suite |
| 3 | **incomplete** — some tests skipped, normally because the raw data is absent |

A fresh clone has no `data/` (gitignored) and exits **3**. The tests that do run still verify
their own components — the BSON parser fixture and the runner's own contracts — but the
pipeline is unverified until the data is staged.

`skipped=0` is **necessary but not sufficient**: every required test must also pass. The gate
is **exit 0**, meaning `failed=0` **and** `skipped=0`.

## 3. Regenerate the artifacts (optional, and only afterwards)

Only needed if you are changing the analysis. Build into a scratch directory so the committed
artifacts stay intact as a reference:

```
mkdir -p /tmp/scratch
python3 build_numbers.py --out-dir /tmp/scratch     # numbers.json + three CSV tables
diff <(python3 -m json.tool /tmp/scratch/numbers.json) <(python3 -m json.tool numbers.json)
```

`build_numbers.py` also accepts `--data-dir`, `--sema-dir` and `--src-dir` if the inputs live
elsewhere. Run with **no arguments** and it writes into the repository root, replacing the
committed artifacts — which is what you want when deliberately publishing a new version, and
not what you want before verifying.

The figures read `numbers.json` and, by default, write beside themselves. Both also take
`--out-dir`, which is how the test suite renders them without touching the committed copies:

```
python3 figure1.py                      # figure1_light.png / figure1_dark.png
python3 figure2.py --out-dir /tmp/scratch   # render elsewhere and diff
```

`numbers.json` holds every figure quoted anywhere in this repository. Both figure scripts
assert their caption values against it and refuse to write if any disagrees.

## Environment

**Prerequisite: Python 3.11.15.** `pip` neither installs nor selects the interpreter, so this
is on you — use pyenv, conda, a system package, or whatever you prefer.

`requirements.txt` pins the **package** versions only:

```
pandas==3.0.2 · numpy==2.4.4 · matplotlib==3.10.9
```

Byte-identical rebuilds are claimed for that package set **on Python 3.11.15** only. Other versions may well produce the
same numbers, but that has not been tested, and floating-point and serialisation details can
differ across releases. If a rebuild differs under a different environment, compare the parsed
values rather than the bytes before concluding anything is wrong.

## What the suite checks

49 tests across thirteen contracts. The load-bearing ones:

| Contract | What it protects |
|---|---|
| **Raw input** | the input is the file the analysis was written against — pinned hashes, row counts, and a known duplicate defect (one participant carries a duplicated hour-0 row on 68 days; 70 rows are removed) |
| **Parser / source** | only BSON types the fixture covers appear in either file; the prompt-outcome counts are reproduced by a raw type census that never touches a parsed value |
| **Calendar day** | a non-midnight first prompt puts day zero on its own calendar date, and the last included date is day 48. The defect this replaced is pinned too, so a regression is recognisable |
| **Cohort** | membership as a set, not just its size; and that H = 49 is retained while the selection rule, correctly executed, yields 50 |
| **Grid** | the expected-day grid is built first and joined `one_to_one` with an indicator, so a fan-out or an escaped observation raises |
| **Published numbers** | every figure quoted, asserted to the precision it is printed at, including the text the figure scripts actually hand to the renderer |
| **Isolated rebuild** | source → artifact into two empty directories, byte-identical to each other and to the committed files. The four committed data artifacts are never written during tests, and neither are the four committed PNGs |

The suite is mutation-checked. Reverting the calendar-date fix, altering one pinned value in
`numbers.json`, removing the `validate="one_to_one"` join guard, or moving a required caption
phrase into a comment each make it fail.

## Known limitations

- n = 71 in the Fitbit export; 63 have any scheduled prompt; 60 meet the fixed horizon. One
  device (Fitbit Sense), one protocol, observational.
- A first scheduled prompt is a **chosen study-generated anchor, not a verified study start**.
  Nothing in the release establishes enrolment or consent dates. 8 of 71 participants have no
  scheduled prompt, so no SEMA-based window can be assigned to them.
- H = 49 is the committed horizon, retained after corrected execution of the selection rule
  yielded 50. Nothing here supports a claim past day 48.
- Recruitment figures are single-cohort estimates of what would be needed **in expectation**
  if this cohort's observed yields carried over. They are not a guarantee of 50 completers and
  not a transferable constant.
- The pre-specified headline criterion for the signal-choice comparison was **not met**. That
  is not a finding of no difference.
- This is Fitbit data. It is not evidence about any other wearable.
