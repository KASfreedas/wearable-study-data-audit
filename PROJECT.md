> **SUPERSEDED — historical planning document.**
>
> This is the original project specification, written before the provenance audit. It describes
> the retired Fitbit-clock analysis: a 63-day horizon, all 71 participants, and a `run.py` /
> `pytest -v` workflow that no longer exists. Its premise did not survive — see
> `WINDOW_RULE.md` §8 and `CHANGELOG.md`.
>
> **Do not follow the instructions in this file.** Current state:
> [`README.md`](README.md) · [`RESULT.md`](RESULT.md) · [`VERIFY.md`](VERIFY.md)
>
> It is kept because the project's contribution is a record of a corrected assumption, and
> deleting the superseded premise would remove the evidence of what was corrected.

---

# Wearable adherence: what a definitional choice costs you in participants

**Project specification, reasoning, and audit prompt**
KASfreedas · started 2026-09-12 · spec current as of 2026-09-13
Repository: analysis code, tests, and criteria. Data not included (CC-BY, 615 MB).

---

## 1. What this is, in one paragraph

A small, fully reproducible analysis of a public wearable dataset that answers one
operational question: **if you need 50 participants who each contribute 60 usable days of
device data, how many do you have to enroll?** The answer on this dataset is 155 — or 119,
depending on a definitional choice most study protocols never write down. The project
exists to be checked, not to be impressive. Every number it publishes is asserted by an
automated test, and a stranger can reproduce all of them in three commands.

---

## 2. Cause — why this project exists

Written plainly, because a reader who understands the motivation will read the work
correctly.

**The gap it is built to fill.** I have 21 months of dated human-subjects research
experience across four university laboratories, against roles that ask for two or more
years. I hold no industry clinical research title and no EDC or CTMS experience. I am
second author on a published systematic review and meta-analysis, where I independently
appraised 31 trials covering 905 participants using RoB-2 and the PEDro scale. I
coordinated a year-long wearable study on physiological response to heat exposure, with a
target enrollment of 200, in which participants wore Fitbit devices at home between
on-site visits, and I supervised a team of twelve researchers.

What no line of that record demonstrates is **analytical judgment** — that I can define a
measurement rule, apply it honestly, discover I was wrong, and say so. A résumé asserts
that. An artifact shows it.

**The second cause, which is less comfortable.** During the preparation of these
materials I produced or accepted three claims I could not support: a "four years of
research" line whose own dates added to 21 months, a data-verification claim I later
confirmed I never performed, and a set of protocol-deviation narratives I did not live.
Each was caught before it reached anyone who matters. The pattern is what matters, not
the incidents.

This project is the structural answer to that pattern. Not an apology — a mechanism. The
tests in this repository exist so that no number here depends on my word.

---

## 3. Reasoning — why this subject, and why the original framing was wrong

**The original thesis was false and has been withdrawn.** I began with the claim that
"wearable studies fail on adherence, and almost nobody quantifies it." That is not true.
Adherence in wearable research is a populated literature. Chan et al. (*International
Journal of Medical Informatics*, 2022, doi:10.1016/j.ijmedinf.2022.104696) is a systematic
review of 27 studies covering roughly 1.7 million subjects, specifically on how adherence
is analyzed and reported. Anyone evaluating this work would have found it in one search.

**What survived is narrower and better supported.** That same review reports the real
gap: *"there is still a lack of standardization in the medical literature regarding the
analysis and reporting of adherence"*, and concretely, that **only 37% of the studies
reviewed (n = 10 of 27) used the same definition of a valid day** — at least 10 hours of
wear. The review closes by calling for minimum reporting thresholds.

So the field already knows its definitions disagree. What it has not done is **price the
disagreement**. That is what this project does, and it is a deliberately small
contribution:

> Adherence is measured constantly. What is not standardized is what counts as a valid
> day. On this dataset, that choice moves required enrollment from 119 participants to
> 155 — a 30% difference in recruitment budget, hidden inside a sentence most protocols
> never write.

**Why I am the person to write it.** The analysis itself is simple counting; many people
could do it. The section that closes the write-up — what a coordinator would change —
requires having run the visits. I have called participants whose devices went dark. That
combination is uncommon: people who can run the analysis usually have not made those
calls, and people who have made those calls usually do not publish the analysis.

---

## 4. Hope — what I actually expect from this

Stated honestly so that nobody, including me, over-reads it later.

**What this is not.** Not novel research. Not publishable. It will not change how anyone
designs a study. It is a single small cohort analyzed with arithmetic a competent
undergraduate could reproduce.

**What I hope it does.** I hope one person reads the methods section and concludes that I
can be trusted with a dataset and a protocol. That is the entire ambition. The realistic
best outcome is a conversation — someone asks about the day-zero finding in an interview,
and I can answer it from memory because I actually did the work.

**What would make it a failure.** If it becomes another claim I cannot defend. The kill
condition is explicit and is stated in §9.

**What it cannot fix.** Nothing here moves a two-year experience requirement. Only time
in a clinical research role does that.

---

## 5. Dataset

**LifeSnaps** — Yfantidou, Karagianni, Efstathiou, Vakali, Palotti, Giakatos, Marchioro,
Kazlouski, Ferrari & Girdzijauskas, *Scientific Data* 9, 663 (2022),
doi:10.1038/s41597-022-01764-x.

- Zenodo record **7229547** (open, CC-BY 4.0), file `rais_anonymized.zip`, 615 MB.
  *Note: record 6826683, cited in many places including my own earlier notes, is
  access-restricted and requires an approval request. Use 7229547.*
- 71 participants, Fitbit Sense, in-the-wild collection
- Two CSV exports used: `daily_fitbit_sema_df_unprocessed.csv` (7,410 rows, 63 columns)
  and `hourly_fitbit_sema_df_unprocessed.csv` (159,508 raw rows)
- The MongoDB dump in the same archive is not used
- **Raw data is not committed to this repository.** Input file SHA-256 hashes are pinned
  in `src/adherence.py` so a verifier can confirm identical bytes.

**Structure discovered in the data, not taken from the paper.** The paper describes two
rounds (24 May – 26 Jul 2021, n = 38; 15 Nov 2021 – 17 Jan 2022, n = 34). First-recorded
days in the released file fall across **five** months — April (2), May (42), June (2),
October (12), November (13). Participant observation spans run from **64 to 244 days**
(median 88), not 63. Any seasonal analysis must be defined on observed start dates, not on
the published windows.

---

## 6. Method

### 6.1 Analysis window and denominator

Study day is indexed **per participant** from their own first recorded day, so
differently-timed cohorts align on one axis.

The analysis stops at **study day 63**. This is not because the data ends — it does not —
but because **day 63 is the longest horizon at which all 71 participants are still
observed.** That makes a fixed denominator of 71 honest. Past day 63 the denominator
shrinks and protocol end becomes confounded with dropout.

The denominator is **fixed at 71 at every study day** and never shrinks. A denominator
that falls as people drop out conceals exactly the attrition this analysis measures.

### 6.2 What counts as a valid day

Three nested definitions, computed from the daily file:

| Name | Rule | Valid-day rate |
|---|---|---|
| loose | a step count is present | 64.5% |
| primary | a step count **and** a resting heart rate are present | 59.6% |
| strict | steps, resting heart rate **and** calories | 59.6% |

Strict and primary are **identical at every study day** — calories is never present
without the other two — so the published figure shows two lines, not three.

A fourth definition is computed from the hourly file: **hours carrying a heart-rate
reading**, which is the field-standard Fitbit wear proxy. NIH *All of Us* guidance derives
adherence from minute-level heart-rate coverage over 1,440; hourly granularity is used
here, so the unit is hours out of 24.

| Threshold | Valid-day rate |
|---|---|
| ≥ 8 hours | 64.2% |
| ≥ 10 hours (the field's modal convention) | 62.8% |
| ≥ 12 hours | 60.8% |

### 6.3 The rule that was pre-registered and had to be abandoned

`CRITERIA.md` fixed a primary definition **before the data was opened**: a valid day is
one with at least 600 minutes (10 hours) of recorded wear. That is the conventional
threshold and it could not be applied.

The daily file has no wear-time field. The nearest candidate — the sum of lightly,
moderately, very active and sedentary minutes — does not measure wear: **48.8% of
participant-days sum to exactly 1,440 minutes**, because Fitbit fills the day, and only 31
of 7,083 days fall below 600. A 600-minute threshold would have marked 99.6% of days valid
and discriminated nothing.

The pre-registered fallback became primary, exactly as written. That is the
pre-registration working, not failing.

### 6.4 Enrollment arithmetic

For a required number of valid days *K* within the 63-day window: the share of enrolled
participants reaching *K*, and the enrollment needed to finish with 50 who do.

```
share_reaching(K) = (participants with >= K valid days) / 71
enroll_for_50(K)  = ceil(50 / share_reaching(K))
```

One cohort, one device, one protocol. A planning estimate, not a transferable constant.

---

## 7. Findings

### 7.1 Predictions recorded before the data was opened, and how they scored

| # | Prediction | Result |
|---|---|---|
| 1 | Adherence declines monotonically with study day | **FAILED.** It rises for two days, plateaus near 80% for roughly three weeks, then erodes. |
| 2 | The steepest drop occurs in the first 14 days | **FAILED.** The first 14 days are the *highest*-adherence period. Decline begins around day 21. |
| 3 | Missingness is concentrated in a minority of participants | **CONFIRMED.** |
| 4 | The winter cohort shows lower adherence than the summer cohort | **Not tested** — cut from scope, and see §5 on why the cohort definition is not what the paper describes. |

Two of three tested predictions were wrong. They are reported as wrong. This is the part
of the project I would point at first.

### 7.2 The shape of adherence

- **Day 0: 50.7%.** Half of participants produce no usable data on the day they are
  enrolled. This is an onboarding failure, not attrition — the device is handed over and
  not set up, synced, or worn home.
- Peak at day 2 (81.7%), then a plateau near 80% through roughly day 21
- Erosion from day 21 onward, reaching 54.9% by day 62

### 7.3 The enrollment cost

Target: 50 participants who each reach the stated number of valid days inside 63 days.

| Required valid days | Enroll (primary) | Enroll (loose) |
|---|---|---|
| 30 | 66 | 63 |
| 45 | 85 | 74 |
| 60 | **155** | **119** |

### 7.4 The headline: signal choice matters, threshold barely does

Two different things get called "the valid-day definition", and they behave nothing alike.

- **Threshold** (8 h vs 10 h vs 12 h of heart-rate coverage): moves the valid-day rate by
  **3.3 percentage points**. Close to inert.
- **Signal choice** (steps only vs steps-and-heart-rate): moves required enrollment from
  **119 to 155** — 36 additional participants for the identical study.

The literature's standardization debate is largely about thresholds. On this dataset the
threshold is the variable that barely matters.

### 7.5 Where the missing data lives

Under the primary definition, within 63 days: **1,344 missing participant-days.**

- The worst **10%** of participants (8 people) hold **35.7%** of all missing days
- The worst **25%** (18 people) hold **65.1%**
- The worst **50%** (36 people) hold **93.2%**
- **5 of 71 participants produced zero valid days** across the entire 63-day window

These have opposite operational fixes. Thinly spread missingness is a reminder problem.
Concentrated missingness is a screening and onboarding problem. Five participants who
never produced a usable day were consented, enrolled, counted — and contributed nothing.

---

## 8. What this does not show

- **n = 71**, one device (Fitbit Sense), one protocol, observational. Not a trial.
- Enrollment figures are point estimates from a single cohort **with no confidence
  interval**. They are the weakest numbers in the document and they are the most
  quotable, which is a dangerous combination. Treat them as a starting point for a power
  calculation, never as a constant.
- Nothing here supports any claim past **study day 63**.
- This is **Fitbit data**. It is not evidence about any other wearable, and no comparison
  to another device is made or implied.
- No causal claims. Differences between cohorts are confounded with season, calendar and
  recruitment, and that confounding is stated rather than modeled away.
- The heart-rate coverage measure is **hourly**, not minute-level as in the *All of Us*
  formulation. It is coarser.
- **The daily file is not dense.** Eight of 71 participants have calendar gaps totaling
  563 absent participant-days, 235 of them inside the analysis window. Absent rows
  correctly contribute nothing to the numerator while the denominator stays at 71, so the
  curve is unaffected — but an earlier draft of `CRITERIA.md` claimed the file had no
  gaps, and that claim was false.
- **One participant carries a duplicated hour-0 row on 68 of their 244 days.** Seventy
  duplicate `(id, date, hour)` rows are removed at load. Left in, they inflate that
  participant's heart-rate coverage. My first hypothesis — a daylight-saving transition —
  was wrong; the affected days run one-per-date across May–August 2021 and the only US
  transition in range does not appear among them.

Both of the last two were found by the test suite on its first run, before publication.
Both are recorded in `CRITERIA.md`, Amendment 2.

---

## 9. Verification, and the rule that governs this project

### Reproducing it

See `VERIFY.md`. Three commands: fetch the data from Zenodo and confirm the pinned
hashes, run `python run.py` to regenerate `numbers.json`, run `pytest -v`.

### The test suite

24 tests in four layers:

1. **Data contract** — pinned input hashes, row counts, the known duplicate defect, the
   known calendar gaps
2. **Invariants** — the three definitions must nest; the denominator must never shrink;
   requiring more valid days can never require enrolling fewer people
3. **Published numbers** — every figure in this document, asserted at the precision it is
   printed
4. **Reproducibility** — determinism, and `run.py` emitting every published key

**Layer 3 is the point.** If this document says 62.8% and the code produces 62.9%, the
suite goes red. The document and the code fail together.

### Kill condition

**If a published paper already reports that wear-signal choice changes required
enrollment, this project stops and does not ship.** The original premise was falsified
once. A second falsification means the topic is not mine to write about, and the correct
response is to stop rather than reframe a third time.

### Independent check

Before publication, one named person other than me reruns `pytest` against a fresh
download and confirms the numbers. If nobody has done so, page one of the published
version reads **"Not independently rerun."** No verification, no claim.

---

## 10. Status

| Component | State |
|---|---|
| Pre-registered criteria + two amendments | Written, dated, committed |
| Data profiled, structure verified | Done |
| Adherence curve, enrollment math, missingness | Computed |
| Figure (light and dark) | Rendered |
| Analysis module, `run.py`, `numbers.json` | Done |
| Test suite (24 tests, four layers) | All green |
| `VERIFY.md` | Written |
| Write-up (700–1,000 words) | **Not written** |
| Literature check on the §7.4 headline | **Not run** — gates publication, see §9 |
| Independent rerun | **Not secured** |
| Repository public | **No** |

---

## 11. Audit prompt

Paste everything below into a fresh session of a capable model — or hand it to a person
along with this file and the repository.

> You are auditing a small data-analysis project for factual and methodological defects
> before it is published. The author has a documented history of producing claims he
> could not support, so your job is to find what is wrong, not to encourage him. Assume
> there is at least one error. If you cannot find one, say so plainly rather than
> inventing a concern to seem useful.
>
> You are given `PROJECT.md` (the spec), `CRITERIA.md` (pre-registered criteria plus two
> amendments), `src/adherence.py`, `test_adherence.py`, `run.py`, and `numbers.json`.
>
> Work through these in order and answer each one specifically, citing the line or number
> you are responding to.
>
> **1. Novelty.** §7.4 claims that the choice of wear signal (steps only versus steps and
> heart rate) moves required enrollment materially, while the threshold does not, and
> implies nobody has priced this. Search the literature. Does a published paper already
> report this? If yes, name it — that finding triggers the project's stated kill condition
> and it should not be published. This is the single most important question you will
> answer.
>
> **2. Arithmetic.** Recompute `enroll_for_50(K) = ceil(50 / share_reaching(K))` from the
> stated shares. Do 66, 85, 155 and 119 follow? Does any rounding choice change a headline
> number?
>
> **3. The denominator argument.** §6.1 argues that a fixed denominator of 71 is honest
> through day 63 because all 71 participants are observed to that point. Is that valid
> given that 235 participant-days inside the window are absent rows rather than null
> fields? Does treating an absent row as a non-valid day overstate or understate
> adherence, and by roughly how much?
>
> **4. The abandoned pre-registration.** §6.3 says the 600-minute wear rule was
> unusable because 48.8% of days sum to exactly 1,440 minutes. Is that the right
> conclusion, or is there a defensible way to recover wear time from those fields that was
> missed? Would any such method change the findings?
>
> **5. Overclaiming.** Read §7 and §3 as a hostile reviewer. Find every sentence that
> claims more than the data supports. Pay particular attention to the enrollment figures,
> which are point estimates from n = 71 with no confidence interval, and to the word
> "headline" in §7.4.
>
> **6. Missing limitations.** §8 lists what the project does not show. What belongs on
> that list and is not there?
>
> **7. The tests.** Does layer 3 actually assert every number that appears in
> `PROJECT.md`? Name any published figure with no corresponding assertion. Are any of the
> invariant tests in layer 2 vacuous — passing regardless of whether the code is correct?
>
> **8. The framing.** §3 and §4 make a case for why this project exists and what it is
> worth. Is that case honest, or is it a more sophisticated version of the overclaiming it
> says it is correcting?
>
> Finish with a single verdict: **publish**, **publish after specific fixes** (list them),
> or **do not publish** (say which finding makes it unpublishable). Do not hedge, and do
> not soften the verdict to be agreeable.

---

## 12. Sources

- Yfantidou S, et al. LifeSnaps, a 4-month multi-modal dataset capturing unobtrusive
  snapshots of our lives in the wild. *Scientific Data* 9, 663 (2022).
  https://doi.org/10.1038/s41597-022-01764-x — dataset at
  https://zenodo.org/records/7229547 (CC-BY 4.0)
- Chan A, Chan D, Lee H, Ng CC, Yeo AHL. Reporting adherence, validity and physical
  activity measures of wearable activity trackers in medical research: A systematic
  review. *International Journal of Medical Informatics* 160, 104696 (2022).
  https://doi.org/10.1016/j.ijmedinf.2022.104696
- NIH *All of Us* Research Program — Considerations while using Fitbit Data.
  https://support.researchallofus.org/hc/en-us/articles/9651723386388
