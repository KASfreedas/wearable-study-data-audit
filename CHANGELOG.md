# Changelog

## 2026-09-14 — execution corrections against the frozen specification

`WINDOW_RULE.md` v2 is unchanged: H, K, the cohort definitions, the signal definitions and
the four null conditions are exactly as frozen, and the null verdict is unchanged. These
are defects in the code that executes the rule and in how results were reported. Full
detail in `WINDOW_RULE.md` §8.

**Corrected**
- Study-day offsets and exposure spans were computed by subtracting a wall-clock instant
  from a midnight date. Negative timedeltas floor, so day 0 landed one day late for all
  63 SEMA-anchored participants and every window was shifted (§8.1). Now date-minus-date
  through a single `calendar_date()` helper; no timezone conversion, because the SEMA
  timestamps are naive local wall-clock strings.
- Expected-day join hardened with `validate="one_to_one"` and `indicator=`; silent `NaT`
  coercion of present timestamps now raises; the reader's exercised BSON type surface is
  asserted rather than assumed (§8.4).
- `build_numbers.py` takes explicit source and output paths and is verified by rebuilding
  into two empty directories; tests never write to committed artifacts.

**Retracted**
- "The ratio declines monotonically with K" — false, both of the numbers it was written
  about and of the corrected ones (§8.3). Monotonicity is now measured, not assumed.

**Recorded, not applied**
- Re-executing the mechanical H-selection rule under corrected date arithmetic yields
  H = 50. H stays 49 because it was pre-committed (§8.2).

**Removed**
- `figure.py`, `adherence_light.png`, `adherence_dark.png` — generated from the retired
  63-day Fitbit-clock analysis whose premise was invalidated. Superseded figures are
  deleted rather than kept, for the same reason `run.py` was.

**Added**
- `figure1.py` and `figure1_{light,dark}.png` — the audit figure: all 71 participants'
  Fitbit availability and scheduled-prompt density against the two published collection
  rounds. Caption numbers are asserted against `numbers.json` before the file is written.
- `numbers.json` gains the coverage keys the figure quotes
  (`fitbit_participant_days_outside_published_rounds` and companions).

**Corrected in reporting**
- Study day 0 is now described as a *chosen study-generated exposure anchor, not a verified
  study start* — the released records establish no enrolment, consent or wear start.
- Added an explicit statement that the unmet headline criterion is **not** a finding of no
  difference, and that the interval's upper endpoint is a structural boundary rather than
  an interior null.
- The H = 49 retention is restated as a disclosed decision resolving a real conflict between
  a pre-committed horizon and a selection rule that, executed correctly, yields 50.

**Corrected after review (second pass)**
- Figure 1: published round windows given a perceptible fill; numeric paragraph moved from
  the subtitle into the caption; "the only study-generated clock" dropped (survey timestamps
  also exist); the falsifiability line no longer predicts exact agreement between device
  records and prompts, which measure different events with different missingness.
- **Retracted: "panel B is confined to the published windows."** Measured against the same
  calendar boundaries, 238 of 15,380 scheduled prompts (1.5%) fall outside, belonging to 2 of
  63 participants; all precede round 1, earliest 2021-04-07. The claim is now "largely
  concentrated within", and the contrast is stated as one of degree (33.8% vs 1.5%).
- Removed the "therefore" linking the 33.8% coverage statistic to the 9 cross-round spans;
  they are separate measurements. A bridging span is also distinguished from verified repeat
  participation — the prompt-clock count matches the paper's in number only.
- H = 49 vs the rule's corrected 50 is now disclosed in the main text of `RESULT.md`.
- Observed point estimates (0.9623 = 51/53, 1.0351 = 59/57) are reported separately from the
  bootstrap medians (0.9630, 1.0357), which were previously presented as if observed.
- Curve ratios are computed from counts, not from rounded percentages.
- Deleted "a larger cohort could place the interval away from 1.0 in either direction" —
  false under nesting. Separated *why the ratio cannot exceed 1.0* (construction, any sample)
  from *why this interval reaches it* (12.85% of replicates sit exactly at 1.0). Removed
  "not powered to establish either", which no power analysis supports.
- "No significance is claimed at any K other than the pre-specified primary" → "at any K".
- Added `SUMMARY.md`, the short standalone explanation.

**Corrected after review (third pass)**
- Figure footer no longer assumes the published windows capture every legitimate study event.
  It now reads: released Fitbit availability extends beyond the published collection windows
  and should not be treated as a verified participant-specific exposure window.
- **33.8% and 1.5% were different units** — participant-days against individual prompts. SEMA
  is now also aggregated to unique participant-dates, the comparable unit: 70 of 3,886 (1.8%)
  outside, against 2,501 of 7,410 (33.8%) for Fitbit. The prompt-level figure is retained with
  its own denominator and is no longer set against the participant-day figure.
- "Unanchorable" → "no SEMA-based exposure window can be assigned"; anything stronger needs
  the separate survey audit.
- Before/after table now uses observed estimates throughout (1.30 = 155/119 against
  1.0351 = 59/57), the original value's provenance having been checked. The bootstrap median
  and CI are reported separately and labelled.
- H disclosure drops the claim that re-deriving would make pre-commitment meaningless: we
  retained the committed H = 49 after discovering the discrepancy, which preserves the named
  horizon but departs from the correctly executed selection rule.
- Test no longer asserts observed ≠ bootstrap median (incidental to this dataset); each is
  checked against its own independent computation. A test that compared a participant-day
  percentage against a prompt percentage was corrected to compare like with like.
- "Pre-specified curve, reported in full" → "selected points"; the complete K = 7–49 curve is
  `usable_day_curve_K7_to_K49` in `numbers.json`.

**Added (fourth pass)**
- `figure2.py` and `figure2_{light,dark}.png` — both pre-specified attainment curves across
  K = 7–49, K = 21 marked, N = 60 and the retained H = 49 stated, and the unmet headline
  criterion stated on the face of the figure. Subordinate to Figure 1 by design.

**Corrected after review (fourth pass)**
- Figure 1 footer and `RESULT.md` now state that the 33.8% and 1.8% figures rest on different
  source populations (71 Fitbit participants against 63 with SEMA), so the comparison is
  descriptive of the two exports rather than controlled on identical participants.
- `VERIFY.md`: `skipped=0` is necessary but **not sufficient** — the gate is exit 0, meaning
  `failed=0` and `skipped=0`. A partial run still verifies the components that did execute.

**Corrected after review (fifth pass)**
- "strict subset" → "subset" wherever the curve/ratio bound is justified. Nesting permits
  equality and equality occurs: at K = 7–11 the two counts are identical and the ratio is
  exactly 1.0. A test now pins those K values and forbids the word returning.
- Figure 2's axis rationale is recorded correctly in the source: the full 0–100% scale gives
  attainment percentages their natural context; it does **not** establish whether any gap
  between the curves is practically important, which this analysis does not settle.
- Caption tests now assert the text **generated and handed to the renderer**
  (`build_caption()` in both figure scripts), not the source file. Searching source would
  match a comment or an unused literal; mutation-checked by moving the required phrases into
  a comment, which the new test fails and the old one passed.

**Added**
- `README.md` — the portfolio page: the assumption investigated, Figure 1 as main evidence,
  three points (discrepancy, correction, remaining limitation), Figure 2 as secondary, and
  reproduction instructions. The repository URL is a marked TODO, not invented.

**Corrected after review (sixth pass)**
- **The reproduction command did not work for anyone else.** `--sema-dir` defaulted to a
  container-specific absolute path. It now defaults to `data/` alongside the Fitbit CSVs, the
  test suite looks there too, and `VERIFY.md` says to stage all four raw inputs in `data/`.
  Verified end to end: a fresh clone exits 3, and after staging, the README's bare
  `python3 build_numbers.py` and `python3 run_tests.py` both exit 0 and reproduce the
  committed artifacts byte-for-byte.
- README opening softened — the audit shows the assumption needs verification, it does not
  establish that Fitbit dates are never study-exposure dates.
- README Secondary analysis now discloses the H = 49 / rule-yields-50 discrepancy, and the
  recruitment estimates are qualified: approximately 57 versus 59 recruits to obtain 50
  completers **in expectation**, not a guarantee.
- Nesting tests split three ways: a structural test (primary_n <= loose_n at every K,
  equality permitted), a separate pinned dataset result (equality occurs at K = 7-11), and a
  caption test that verifies the intended statement rather than forbidding a word.
- Runner: an in-test `pytest.skip()` decremented a `passed` counter that was never
  incremented, under-reporting passes on a partial run. Fixed; the INCOMPLETE message now
  states the gate as exit 0.

**Corrected after review (seventh pass)**
- **Verification order was backwards.** `VERIFY.md` told readers to rebuild `numbers.json`
  before running the suite — which overwrites the reference the isolated-build test compares
  against, so the test would have compared a rebuild to a rebuild. It matters most for the
  `.bson` hashes, which are recorded in `numbers.json` rather than independently pinned. The
  order is now: stage inputs → verify the untouched checkout → regenerate afterwards, into a
  scratch directory.
- Verified rather than asserted: a suite run leaves all four data artifacts byte-identical.
  Stated precisely, because the figure tests **do** rewrite the four PNGs in place —
  deterministically, to identical bytes, but rewritten.
- `requirements.txt` added, pinning the versions actually used: python 3.11.15, pandas 3.0.2,
  numpy 2.4.4, matplotlib 3.10.9. Byte-identical rebuilds are claimed for that set only.
- "not mine to redistribute" → "Raw data is not included; obtain it from the original source."
- `PROJECT.md` and `CRITERIA.md` marked superseded — `PROJECT.md` still instructed readers to
  run `run.py` and `pytest -v`, both long gone. `CRITERIA.md`'s banner is scoped: its design
  parameters are superseded, its round-window table is still cited by Figure 1.
- **`figure1.py` hardcoded a container path** for the BSON files and would have failed for
  anyone else. Now reads `data/`, like the build and the tests.

**Corrected after review (eighth pass)**
- `figure1.py` and `figure2.py` take `--out-dir`; the figure tests now render into temporary
  directories and compare against the committed PNGs. The earlier "deterministic rewrite"
  exception is gone: **no committed artifact, data or figure, is written during a test run**,
  verified by modification time as well as by hash.
- `requirements.txt` scoped to packages only, with Python 3.11.15 stated as a separate
  prerequisite that pip neither installs nor selects.
- Contract table no longer says "committed artifacts are never written" while an exception
  stood above it.

**Fixed after first independent execution (2026-09-14)**
- **The runner did not work on any machine that had pytest installed.** It
  deferred to real pytest when importable, but resolves fixtures by looking for
  markers only its own shim sets — so every fixture-taking test failed with
  `KeyError: no fixture named 'N'`. 37 of 49 failures, none of them real defects.
  The shim is now installed unconditionally. This was invisible in the container
  where the suite was written, because pytest cannot be installed there; it
  surfaced the first time someone ran the suite on their own machine.
- Regression test added: the suite now puts a stand-in pytest on the path and
  requires the runner to still resolve fixtures and exit 0.
- To use real pytest instead, invoke `pytest -v` directly — the test files are
  ordinary pytest files; you only lose this runner's three-way exit codes.

- **The byte-identical rebuild claim was platform-specific.** `write_text` and
  `to_csv` translate to CRLF on Windows, so a Windows rebuild produced identical
  values and different bytes — 14,452 bytes against 13,918, exactly one extra
  byte per line. All four writers now force `newline='\n'` / `lineterminator='\n'`,
  a `.gitattributes` pins LF, and a test fails if any committed artifact contains
  CRLF. Every value had already reproduced exactly on Windows under a different
  Python and pandas version, which is the part that mattered.
- Silenced a pandas downcasting FutureWarning without changing any value
  (`fillna(False)` on an object column replaced by `== True`).

- **The figure test asserted something untrue.** It required PNGs rendered on
  different machines to be byte-identical. Matplotlib output depends on installed
  fonts, FreeType and libpng, so that never held across environments — it passed
  only because it had only ever run in one. Replaced with what is actually
  invariant: the script exits 0 (having asserted every caption number against
  `numbers.json`) and the render's pixel dimensions match, since those come from
  `figsize x dpi`. Mutation-checked: changing a figure's height fails the test.

**Effect on the verdict: none.** Null condition 2 fires; the signal-choice headline stays
abandoned.
