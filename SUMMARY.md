# What this audit found

The released Fitbit records extend beyond the dataset's published collection windows. In this
audit, 2,501 of 7,410 participant-days — 33.8% — fall outside both windows, affecting 68 of 71
participants. Device-record availability therefore cannot be used uncritically as a
participant's study-exposure window.

Scheduled SEMA prompts provide a separate, study-generated reference for examining that
assumption. They do not establish enrollment or consent dates, and eight participants have no
scheduled prompts in the release. The audit documents those limitations, reconstructs explicit
analysis windows, and retains missing days in the denominator.

A secondary comparison evaluates two definitions of usable Fitbit data within a retained
49-day horizon. Its pre-specified headline criterion was not met. The contribution is the
documented investigation of dates, source meaning, and denominators — not a claim that the two
definitions are equivalent.

---

Every figure above is a key in `numbers.json`, regenerated from source by `build_numbers.py`.
Figure 1 (`figure1.py`) and the full result (`RESULT.md`) carry the detail; `WINDOW_RULE.md`
§8 records the execution defects found and corrected, including the one-day calendar shift
that moved every analysis window and the retention of H = 49 where corrected execution of the
selection rule yields 50.

Data: LifeSnaps (Yfantidou et al., *Scientific Data* 2022; Zenodo 7229547, CC-BY 4.0).
