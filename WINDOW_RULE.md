# Participation window, observation horizon, estimand, and null conditions

**Version 2 — 2026-09-14.** Supersedes v1 of the same date, which conflated the
observation horizon with the usable-day target and proposed a pair of "bounds" whose
ratio is algebraically identical. Both errors are described in §7.

**No wearable-validity outcome has been computed on the corrected cohort at the time of
writing.** The horizon in §2 was derived from SEMA exposure alone. The conditions in §5
were fixed before any yield, ratio or bootstrap was calculated, so a null result cannot
later be renegotiated into a finding.

---

## 1. Populations

Three nested populations, each with its own purpose and its own exclusion reason.

| Population | N | Used for |
|---|---|---|
| **Provenance cohort** | 71 | Everything auditing the released export against the published study structure. No exclusions. |
| **SEMA-anchored cohort** | 63 | Anything requiring a participant-specific exposure window. |
| **Fixed-horizon cohort** | 60 | The usable-data yield analysis, which requires a common observation window. |

**71 → 63.** Eight participants cannot be assigned a defensible study exposure window
from the available study-generated timestamps:
- 5 have no SEMA records; survey records exist but carry only the `1980-01-01` sentinel
  submission date, or a terminal date with no start
- 3 are present in the Fitbit export and absent from both SEMA and surveys

**63 → 60.** Three participants have fewer than H days of reconstructed exposure. The
exclusion is exposure-based and outcome-independent: it was determined before any
wearable outcome was examined.

Excluded participants remain in the provenance cohort and appear in Figure 1. They are
evidence, not contamination.

## 2. Exposure window and observation horizon

**Exposure window.** A participant's exposure window runs from their first
`SCHEDULED_TS` to their last `SCHEDULED_TS` in the SEMA export, inclusive.

Scheduled prompts are used rather than completed responses because a prompt is a
study-generated event independent of whether the participant answered. With 45.2% of
prompts answered, a completed-response boundary would truncate real exposure by response
behaviour. This choice recovers zero additional participants — all 63 with scheduled
prompts also completed at least one — and is adopted for the definitional reason alone.

**Study day 0** is the date of a participant's first scheduled prompt. No day is called
an enrollment day. No onboarding, dropout, attrition or adherence language appears
anywhere in this project.

**Observation horizon H.** Fixed mechanically from the exposure distribution, before any
outcome: *the largest horizon for which at least 95% of the SEMA-anchored cohort has
sufficient exposure.*

> **H = 49 days.** 60 of 63 participants (95.2%) have ≥49 days of reconstructed exposure.
> At H = 50 the figure falls to 58 of 63 (92.1%), below the threshold.

Only each participant's **first 49 study days** are evaluated, so every included
participant is given an identical opportunity window.

H = 49 is exactly seven weeks, which is what makes the primary target in §3
literature-anchored rather than invented.

## 3. Estimand

The outcome is **usable-data yield**, never adherence. LifeSnaps documents that missing
Fitbit records arise from both participant non-wear and failures in synchronisation or
archive export; these mechanisms cannot be separated in the released data.

Two quantities are defined separately and never collapsed into one:

- **H — observation horizon.** The fixed number of calendar study days over which each
  participant is given an equal opportunity to contribute usable data. **H = 49.**
- **K — usable-day target.** The number of usable Fitbit days required within that
  horizon. K ≤ H.

**Primary estimand:**

> the proportion of fixed-horizon-cohort participants accumulating at least **K** usable
> Fitbit days within their common **49-day** observation window.

Both pre-specified signal definitions are evaluated on the same participants over the
same 49-day windows.

**Pre-specified K.** The full cumulative usable-day curve is reported for K = 7 to 49.
The primary comparison is K = 21 usable days within the 49-day horizon.

K = 21 was fixed before any wearable-validity outcome was examined. Its selection is
**literature-informed rather than a direct implementation of a published valid-week
rule.** Chan et al. (2022) found that the most common valid-interval definition among the
reviewed studies was a week containing at least three valid days (8 of 27 studies).
Because the mechanically selected observation horizon is exactly seven weeks, that
convention motivated a cumulative target of 21 usable days for this planning analysis.

A cumulative 21-of-49-day target is **not equivalent** to requiring at least three valid
days in each of seven separate weeks, and no claim of equivalence is made.

**Realized cohort yield** may be reported as a separate descriptive quantity: attainment
across all 63 SEMA-anchored participants without a common horizon. It is labelled as
such, and **it is not a bound on the fixed-horizon estimand.** A conditional estimate
among adequately exposed participants says nothing about what the short-exposure
participants would have done with a full horizon.

**The original K = 60 planning estimate is invalidated** and is not recreated. No common
observation horizon of 60 days is supported: only 44 of 63 participants have that much
exposure. Short exposure will not be treated as participant failure.

Expected-day usable-data yield is the primary day-level denominator. Observed-row
validity and file-wide signal completeness are supporting metrics. Every `numbers.json`
key carries its denominator in the key name.

## 4. Why there are no "bounds"

v1 proposed a lower bound (successes ÷ 63) and an upper bound (successes ÷ adequately
exposed). For the **signal-choice ratio** these are algebraically identical:

$$\frac{S_A/D}{S_B/D}=\frac{S_A}{S_B}\quad\text{for any common } D$$

Both signal definitions are evaluated on the same participants, so the denominator
cancels and no interval exists. The v1 null condition built on that interval could never
have fired. Uncertainty on the ratio comes from the **paired participant bootstrap**, not
from a choice of denominator.

## 5. Null conditions, fixed in advance

The sensitivity result is abandoned as a headline finding if any of the following holds
once H and the K range are frozen:

1. **No useful common horizon exists.** The largest horizon supported by ≥95% of the
   anchored cohort is too short to evaluate a practically meaningful usable-day target.
2. **No detectable signal-definition difference remains.** The paired-bootstrap 95%
   interval for the signal-choice ratio at the primary K includes 1.0. The comparison is
   then reported only as an inconclusive secondary analysis.
3. **The fixed-horizon cohort is too small.** Fewer than 40 participants have ≥H days of
   reconstructed exposure.
4. **The result is operationally trivial.** Nearly all participants attain the target
   under both definitions and the implied enrollment multiplier is effectively 1 under
   both.

If any condition is met, H, K, the signal definitions, the validity thresholds and the
target completer count are **not changed in search of a stronger result.**

**Explicitly forbidden:** trying additional observation horizons, K values, signal
definitions, validity thresholds or target completer counts after wearable outcomes have
been examined, in order to recover a significant or more impressive result.

## 6. What ships if the sensitivity result is abandoned

A provenance audit with no sensitivity headline. This is a complete artifact and a
legitimate destination, named in advance so that arriving at it is not treated as a
failure requiring rescue.

- **Figure 1** — all 71 participants, published round windows, Fitbit record availability
  against scheduled-prompt density
- Fitbit record spans imply **9** participants bridging both published rounds; SEMA
  exposure implies **1**; the publication requires exactly **1**
- **8,357 of 15,380** scheduled prompts expired unanswered, demonstrating that absence of
  a completed SEMA response is not evidence of absence of study-generated exposure
- Survey submission dates carry a **1980-01-01 sentinel** affecting all 67 participants
  with survey records
- **Eight participants cannot be assigned a defensible study exposure window from the
  available study-generated timestamps**
- The conclusion: a timestamp being participant-linked and physiologically plausible does
  not make it a study-procedure timestamp

## 7. Errors corrected from v1 of this document

1. **H and K were conflated.** v1 used "exposure ≥ K" as the opportunity criterion. That
   is insufficient: a participant with exactly K days of exposure has no slack, so one
   missing day makes success impossible. Horizon and target are now separate.
2. **The proposed bounds were not bounds.** Their ratio is identical by cancellation
   (§4), and the conditional estimate is not a ceiling on the unobserved counterfactual.
3. Wording corrected: "cannot be anchored to any study-generated timestamp at all" →
   "cannot be assigned a defensible study exposure window from the available
   study-generated timestamps," since two of the eight do have terminal survey dates.
4. Wording corrected: "non-response is not non-participation" → a statement about
   study-generated exposure, which is what the records actually establish.
5. **K = 21 was described as following Chan et al.** It does not. Chan's convention is a
   per-week rule (a week containing ≥3 valid days); a cumulative 21-of-49 target is an
   adaptation, and the two are not equivalent — 21 cumulative days could fall entirely
   within three weeks and fail the per-week rule. K = 21 is retained because it was fixed
   before any outcome, but it is now described as literature-informed, with the
   non-equivalence stated explicitly.

Both substantive errors were found by external review before any outcome was computed.


---

## FROZEN

**This specification is frozen as of 2026-09-14.** H = 49, the fixed-horizon cohort of 60,
K = 21 primary with the K = 7–49 curve, the two signal definitions and the four null
conditions are fixed. No methodological parameter is revisited after outcomes are seen.

Locked sequence: 71 provenance → 63 SEMA-anchored → H = 49 → 60 fixed-horizon → K = 21
primary, K = 7–49 descriptive → two signal definitions → paired bootstrap → evaluate §5.


---

## 8. Post-freeze execution log

The specification above is unchanged. This section records defects found in the **code
that executes it**, not revisions to the rule. H, K, the cohort definitions, the signal
definitions and the four null conditions are exactly as frozen.

### 8.1 Calendar-day arithmetic shifted every window by one day (corrected 2026-09-14)

**What the rule says.** §2 defines study day 0 as the **date** of a participant's first
`SCHEDULED_TS`, and the exposure window as spanning calendar dates.

**What the code did.** The 02:31 build computed `(fitbit_date - first_scheduled_ts).days`,
subtracting a wall-clock instant from a midnight date. A negative timedelta floors rather
than truncates, so for a first prompt at 20:19 the prompt's own date evaluated to −1 and
was discarded; day 0 landed on the following date and the whole 49-day window slid forward
one day.

**Scope.** Not a corner case. All 63 SEMA-anchored participants have a non-midnight first
prompt and every Fitbit row is dated at midnight, so **every** window was shifted.

**Fix.** Calendar dates are derived in one named place, `calendar_date()`, and both the
study-day offset and the exposure span are computed date-minus-date. No timezone
conversion is applied, and none would be defensible: `SCHEDULED_TS` is a BSON **string**
(type 0x02) holding naive local wall-clock text with no offset, and the Fitbit dates are
naive local dates. Converting one side only would move dates.

**Effect on the frozen verdict: none.** Null condition 2 still fires; the headline stays
abandoned. What moved:

| | 02:31 build | corrected |
|---|---|---|
| fixed-horizon cohort | 60 | 60 — *identical membership, not merely the same count* |
| observed participant-days | 2,923 | 2,922 |
| valid days, loose / primary | 2,348 / 2,205 | 2,357 / 2,217 |
| expected-day yield, loose / primary | 79.86% / 75.00% | 80.17% / 75.41% |
| reaching K=21, primary | 50 of 60 | 51 of 60 |
| yield-ratio 95% CI | 0.875 – 1.000 | 0.904 – 1.000 |
| **null condition 2** | **fired** | **fired** |

### 8.2 The H-selection rule now yields 50; H stays 49

H = 49 was chosen mechanically as the largest horizon retaining ≥95% of the 63
SEMA-anchored participants. Re-executing that rule under corrected calendar arithmetic
yields **H = 50** (60 of 63 retained at both 49 and 50; 51 fails).

This is a genuine conflict between two things that were both committed in advance: an
explicit horizon of 49, and a selection rule that — executed correctly — does not produce
49. It is resolved by **disclosed decision**: H remains 49, because the horizon was fixed
before any outcome was seen and re-deriving it after seeing outcomes would make the freeze
meaningless. That is a choice, not a deduction, and the discrepancy is not retired by it —
it stays part of the analysis and is reported wherever H is reported. `numbers.json` carries
both values (`H_rule_reexecuted_under_corrected_calendar`, `H_frozen_value_retained`), and
the test suite asserts the conflict rather than the frozen value alone. A reader who prefers
H = 50 has everything needed to rebuild at 50; the artifacts are not constructed to prevent
that.

### 8.3 Retracted: "the ratio declines monotonically with K"

Stated in the 02:31 `RESULT.md`. **False.** Each attainment curve is individually
non-increasing, but their ratio need not be, and is not: under the corrected numbers it
rises at K → K+1 for K = 13, 14, 24, 30, 32, 40, 42, 43, 45. It was also false of the
numbers it was written about (rises at K = 13, 16, 23, 26, 29, 31, 42). The claim is
withdrawn; monotonicity is now measured in the build and asserted in the suite rather
than assumed.

### 8.4 Provenance and verification hardening

- The expected-day join now runs under `validate="one_to_one"` with `indicator=`, so a
  fan-out or an observation falling outside the grid raises instead of passing.
- `parse_ts()` refuses silent `NaT` coercion: a present-but-unparseable timestamp is an
  error, not a missing value. 0 survey `submitdate` values are unparseable.
- The reader's exercised surface is asserted, not assumed: only BSON types
  `0x01, 0x02, 0x03, 0x07, 0x0A, 0x10` occur in either file. **No BSON datetimes**, so the
  `utcfromtimestamp` branch is never reached by this dataset. The prompt-outcome counts
  are independently reproduced by a raw type census that never uses a parsed value.
- Sentinel reporting is stated exactly: 66 survey records held by 66 participants carry a
  pre-1990 `submitdate`, and the only such value is `1980-01-01`.
- `build_numbers.py` takes explicit source and output paths; the freeze gate rebuilds into
  two empty directories and requires byte-identical artifacts matching the committed ones.
  Tests never write to the committed artifacts.
