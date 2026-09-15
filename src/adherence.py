"""Wearable adherence analysis on the LifeSnaps dataset.

Pure functions, no side effects, no printing. Every published number in the
write-up is produced by a function here and asserted in test_adherence.py.

Data: Yfantidou et al., Scientific Data 2022. doi:10.1038/s41597-022-01764-x
Zenodo record 7229547, CC-BY 4.0. Raw data is not committed to this repo.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

N_ENROLLED = 71   # participants in the released dataset
HORIZON = 63      # longest study day at which all 71 are still observed

# Pinned input fingerprints. A third party reruns against the same bytes or
# knows immediately that they did not.
EXPECTED_SHA256 = {
    "daily_fitbit_sema_df_unprocessed.csv":
        "82c84ee495be4b0ff636a8a44271ffb124e2358d9dd52012b529b897f3d54963",
    "hourly_fitbit_sema_df_unprocessed.csv":
        "99ecc8e2e0a5d7cfd766de835e97aef62b08d1ff767a73185f2d14fed0aed8fd",
}


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- loading

def load_daily(path: str | Path) -> pd.DataFrame:
    d = pd.read_csv(path, low_memory=False)
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values(["id", "date"]).reset_index(drop=True)
    d["study_day"] = d.groupby("id")["date"].transform(lambda s: (s - s.min()).dt.days)
    return d


def load_hourly(path: str | Path) -> pd.DataFrame:
    """Load the hourly file and de-duplicate (id, date, hour).

    One participant (621e301e...) carries a duplicated hour-0 row on 68 of
    their 244 days, giving those days 25 hourly rows. Left in place it inflates
    that participant's heart-rate coverage and can push days over a wear
    threshold spuriously. Found by test_known_hourly_duplicate_defect.
    """
    h = pd.read_csv(path, low_memory=False, usecols=["id", "date", "hour", "bpm", "steps"])
    h["date"] = pd.to_datetime(h["date"])
    return h.drop_duplicates(subset=["id", "date", "hour"], keep="first").reset_index(drop=True)


# ------------------------------------------------------- valid-day rules

def valid_day_flags(daily: pd.DataFrame) -> pd.DataFrame:
    """Three nested coverage definitions.

    The pre-registered 600-minute wear rule is NOT used: the activity-minute
    fields do not measure wear (48.8% of days sum to exactly 1440 because Fitbit
    fills the day). See CRITERIA.md amendment, 2026-09-12.

    Nesting is guaranteed by construction: strict implies primary implies loose.
    """
    out = pd.DataFrame(index=daily.index)
    out["loose"] = daily["steps"].notna()
    out["primary"] = out["loose"] & daily["resting_hr"].notna()
    out["strict"] = out["primary"] & daily["calories"].notna()
    return out


def hr_hours_per_day(hourly: pd.DataFrame) -> pd.DataFrame:
    """Hours per participant-day carrying a heart-rate reading.

    This is the field-standard Fitbit wear proxy (cf. NIH All of Us guidance:
    adherence from minute-level heart-rate coverage over 1440). Hourly
    granularity here, so the unit is hours out of 24.
    """
    return (hourly.groupby(["id", "date"])["bpm"]
                  .count().rename("hr_hours").reset_index())


def hr_valid_rate(hourly: pd.DataFrame, threshold_hours: int) -> float:
    g = hr_hours_per_day(hourly)
    return float((g["hr_hours"] >= threshold_hours).mean())


# -------------------------------------------------------------- outcomes

def adherence_curve(daily: pd.DataFrame, flags: pd.Series,
                    horizon: int = HORIZON, n_enrolled: int = N_ENROLLED) -> pd.Series:
    """Share of ALL enrolled contributing a valid day, by study day.

    Denominator is fixed at n_enrolled and never shrinks. A shrinking
    denominator hides the attrition this analysis exists to measure.
    """
    w = daily.loc[daily["study_day"] < horizon]
    counts = flags.loc[w.index].groupby(w["study_day"]).sum()
    return (counts.reindex(range(horizon), fill_value=0) / n_enrolled * 100.0)


def valid_days_per_participant(daily: pd.DataFrame, flags: pd.Series,
                               horizon: int = HORIZON) -> pd.Series:
    w = daily.loc[daily["study_day"] < horizon]
    return flags.loc[w.index].groupby(w["id"]).sum()


def enrollment_required(daily: pd.DataFrame, flags: pd.Series, required_valid_days: int,
                        target_completers: int = 50, horizon: int = HORIZON) -> dict:
    """How many to enroll to finish with `target_completers` who each reach
    `required_valid_days` inside `horizon` days.

    One cohort of 71 under one protocol on one device. A planning estimate,
    not a transferable constant.
    """
    per = valid_days_per_participant(daily, flags, horizon)
    frac = float((per >= required_valid_days).mean())
    need = None if frac == 0 else int(np.ceil(target_completers / frac))
    return {"required_valid_days": required_valid_days,
            "share_reaching": frac,
            "enroll_to_get_%d" % target_completers: need}


def missingness_concentration(daily: pd.DataFrame, flags: pd.Series,
                              horizon: int = HORIZON) -> dict:
    per = valid_days_per_participant(daily, flags, horizon)
    missing = (horizon - per).sort_values(ascending=False)
    total = float(missing.sum())
    n = len(per)
    share = lambda q: float(missing.head(int(np.ceil(q * n))).sum() / total)
    return {"total_missing_participant_days": total,
            "share_held_by_worst_10pct": share(0.10),
            "share_held_by_worst_25pct": share(0.25),
            "share_held_by_worst_50pct": share(0.50),
            "participants_with_zero_valid_days": int((per == 0).sum())}
