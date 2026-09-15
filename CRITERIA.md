> **Partly superseded.** This is the original pre-registration and its amendments. The design
> parameters here (horizon, cohort, targets) were replaced by `WINDOW_RULE.md`, which is the
> frozen specification the current analysis follows. The published collection-round dates and
> the recorded amendments remain live and are cited by Figure 1. Where this file and
> `WINDOW_RULE.md` disagree, `WINDOW_RULE.md` governs.

---

# Pre-analysis criteria — wearable adherence in LifeSnaps

Written **before** loading the data. Nothing below was chosen after seeing a result.

- Author: KASfreedas
- Date written: 2026-09-12
- Dataset: LifeSnaps (Yfantidou et al., *Scientific Data* 2022, doi:10.1038/s41597-022-01764-x).
  Files from Zenodo record 7229547 (`rais_anonymized.zip`), CC-BY 4.0. Raw data is **not**
  committed to this repository.

## What this analysis asks

1. What fraction of enrolled participants contribute a valid day, by study day?
2. Is missing data spread evenly across participants, or concentrated in a subset?
3. How many participants must be enrolled to end with a target n at a target number of valid days?

## Study structure (from the data descriptor, not from the data)

LifeSnaps ran in two rounds, not one continuous window:

| Round | Dates | n enrolled |
|---|---|---|
| 1 | 2021-05-24 – 2021-07-26 | 38 |
| 2 | 2021-11-15 – 2022-01-17 | 34 |

**63 days per round.** 71 participants appear in the released data against 72 enrolled across
the two rounds; that discrepancy is itself an attrition data point and will be reported, not
silently dropped.

**Hard limit: the maximum observable horizon is 63 days.** Any statement about 90-day adherence
would require extrapolating beyond observed data. This analysis will not do that. Enrollment
math is reported at 30, 45, and 60 valid days only.

## Definition of a valid day

Primary definition, fixed now:

> A participant-day is **valid** if the device recorded at least **600 minutes (10 hours)** of wear.

600 minutes is the standard accelerometry convention (the NHANES/Troiano threshold), chosen
because it is conventional and externally justifiable, not because it produces a preferred result.

If the released files carry no explicit wear-minute field, the fallback — declared now, before
looking — is: a day is valid if it has a non-null resting heart rate **and** a non-null step
count. This is a coverage proxy, weaker than true wear time, and will be labeled as a proxy
everywhere it appears.

**Sensitivity analysis, committed in advance:** the entire analysis is re-run at 8-hour and
12-hour thresholds. If conclusions change across thresholds, that is reported as the headline
finding rather than buried.

## Denominator rule

The denominator at every study day is **all participants enrolled in that round**, including
those who have already stopped contributing. A denominator that shrinks as people drop out
hides exactly the attrition this analysis exists to measure.

## Day indexing

Study day is indexed per participant from that participant's **first recorded day**, not by
calendar date, so the two seasonal rounds align on a common axis.

## Missingness classification

Every participant-day is classified as one of:

- **Recorded** — valid day under the definition above
- **Intermittent gap** — no valid data, but the participant has valid data on a later day
- **Post-dropout** — no valid data, and no valid data on any later day

Separating intermittent non-wear from permanent dropout is the point. They have opposite
operational fixes: one is a reminder problem, the other is a retention problem.

## Predictions, recorded before looking

Stated so they can be wrong:

1. Adherence declines monotonically with study day.
2. The steepest drop occurs in the first 14 days.
3. Missingness is concentrated — a minority of participants account for the majority of
   missing days — rather than spread evenly.
4. The winter round (Nov–Jan) shows lower adherence than the summer round (May–Jul).

Prediction 4 is a genuine coin-flip and is included because it can fail.

## Stopping rules

- One primary figure. Additional figures only if the pre-registered questions require them.
- No comparison to devices not present in this dataset. This is Fitbit Sense data; it is not
  evidence about any other wearable.
- No causal language. Adherence differences between rounds are confounded with season,
  cohort, and calendar; that confounding is stated, not modeled away.
- Limitations section is drafted before the results section.

---

# AMENDMENT — 2026-09-12, after step 0, before any result was interpreted

The criteria above were written before the data was opened. Opening it broke two of
them. They are amended here rather than edited in place, so the original commitments
and the reason each changed both stay visible.

## 1. The 600-minute wear rule is unusable. The pre-registered fallback is now primary.

There is no wear-time field. The closest candidate is the sum of
`lightly_active_minutes + moderately_active_minutes + very_active_minutes +
sedentary_minutes`. It does not measure wear:

- **48.8%** of participant-days sum to **exactly 1440** — Fitbit fills the full day
- only **31 of 7,083** days fall below 600 minutes

A 600-minute threshold would mark 99.6% of days valid and discriminate nothing.

**Primary definition is now the fallback declared above:** a day is valid if it has a
non-null resting heart rate **and** a non-null step count. This is a coverage proxy,
not wear time, and is labeled as such everywhere it appears. Overall valid-day rate
under this definition: **59.6%**.

## 2. The 63-day window stands, for a different and better reason.

The earlier justification — that observation stops at 63 days — was **wrong**.
Participant spans run from **64 to 244 days** (median 88), and the file carries one row
per calendar day with no gaps; missingness appears as null fields, not absent rows.

The window stands because **every one of the 71 participants is observed through exactly
day 63**. That is the longest horizon at which a fixed denominator of 71 is honest.
Past day 63 the denominator shrinks and protocol end becomes confounded with dropout.

**90 valid days remains out of scope** — not because the data ends, but because no
horizon past day 63 supports a clean denominator.

## 3. Sensitivity analysis redefined.

The pre-committed 8h/12h threshold sweep is meaningless on a field that does not measure
wear. It is replaced by a sweep across **coverage definitions**, which is the decision
this dataset actually forces:

| Definition | Valid-day rate |
|---|---|
| strict — heart rate + steps + calories | 59.6% |
| primary — heart rate + steps | 59.6% |
| loose — steps only | 64.5% |

Strict and primary are **identical at every study day**; calories is never present
without heart rate and steps. Two lines, not three.

## 4. The round structure in the data does not match the paper.

The data descriptor reports two windows (May 24–Jul 26, n=38; Nov 15–Jan 17, n=34).
First-recorded-day counts in the released file: **Apr 2021 = 2, May = 42, Jun = 2,
Oct = 12, Nov = 13.** Starts appear in five months, including two the paper does not
describe. Any seasonal comparison must be defined on observed start dates, not on the
published windows.

## 5. Predictions — scored

| # | Prediction | Result |
|---|---|---|
| 1 | Adherence declines monotonically | **FAILED.** It rises for two days, plateaus ~3 weeks, then declines. |
| 2 | Steepest drop in the first 14 days | **FAILED.** The first 14 days are the *highest*-adherence period. Decline begins ~day 21. |
| 3 | Missingness is concentrated | **CONFIRMED.** Worst 10% of participants hold 35.7% of missing days; worst 25% hold 65.1%. Five participants produced zero valid days in 63. |
| 4 | Winter round lower than summer | **Not tested** — cut from the ship-by scope, and see item 4 above. |

Two of three tested predictions failed. They are reported as written.

---

# AMENDMENT 2 — 2026-09-13, found by the test suite on its first run

Two statements in Amendment 1 were wrong. Both were caught by
`test_adherence.py` the first time it ran, before anything was published.

## 1. "The file carries one row per calendar day with no gaps" — FALSE

Amendment 1 stated that missingness appears only as null fields, never as
absent rows. It appears as both.

- **8 of 71 participants** have calendar gaps
- **563 participant-days** are absent from the daily file entirely
- **235 of those fall inside the 63-day analysis window**: the window holds
  4,238 rows where a dense file would hold 4,473

**The analysis is unaffected.** An absent row contributes nothing to the
numerator, which is correct — no data means no valid day — and the denominator
stays fixed at 71 regardless. But the *claim about the data* was wrong, and it
would have gone into the methods section of a document whose whole argument is
that its numbers can be checked.

Pinned by `test_calendar_gaps_are_exactly_as_known`.

## 2. The 25-hour days are not a daylight-saving artifact — ALSO FALSE

Amendment 1 attributed participant-days holding 25 hourly rows to a DST
transition. That was a guess and it was wrong.

The real cause: **one participant** (`621e301e…`) carries a **duplicated hour-0
row** on 68 of their 244 days. The hour sequence on an affected day reads
`0, 0, 1, 2, … 23`. The 68 days run one-per-date across May–August 2021, and the
only US transition in range — 7 November 2021 — does not appear in the set at
all, which is what ruled the hypothesis out.

A further detail the first count missed: **70 duplicate rows were removed, not
68.** Two of them sit on days short enough to stay under 24 rows even with the
extra. Counting over-long days alone would not have found them.

**Correction applied:** `load_hourly()` now de-duplicates on
`(id, date, hour)`. Left in place, the duplicate inflates that participant's
heart-rate coverage and can push a day over a wear threshold spuriously.

**Effect on published numbers:** the ≥12-hour heart-rate valid-day rate moves
from **60.9% to 60.8%**. Every other figure is unchanged. The threshold spread
stays 3.3 points and the signal-choice result (119 vs 155) is untouched.

Pinned by `test_known_hourly_duplicate_defect`.

## Why this is recorded rather than quietly fixed

Both errors were mine, both were caught by a test rather than by a reader, and
both are the kind of thing that is invisible once the document ships. The
amendment stays so that the record shows what was believed, what turned out to
be true, and which test found the difference.
