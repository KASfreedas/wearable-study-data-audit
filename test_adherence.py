"""Test suite, re-pinned to the frozen design (WINDOW_RULE.md v2) after the
calendar-day correction of 2026-09-14.

Thirteen contracts, kept separate on purpose. The raw-input contract is
physically apart from everything derived: the input bytes did not change when
the date convention did, and conflating the two is how a stale contract hides
a live change.

Three contracts are new in this revision:
  3.  calendar-day convention  - the defect that shifted every window by a day
  12. isolated rebuild         - source -> artifact, into empty directories
  13. execution                - proof the suite ran at all

Run with:  python3 run_tests.py
"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/"src")); sys.path.insert(0, str(HERE/"sema"))
import adherence as A, minibson
import build_numbers as BN

DATA = HERE/"data"
DAILY = DATA/"daily_fitbit_sema_df_unprocessed.csv"
HOURLY = DATA/"hourly_fitbit_sema_df_unprocessed.csv"
MONGO = DATA          # VERIFY.md stages every raw input into data/
SEMA, SURV = MONGO/"sema.bson", MONGO/"surveys.bson"
H, K, TARGET, N_COHORT = 49, 21, 50, 60
_T0 = max((HERE/f"figure{n}_{m}.png").stat().st_mtime
          for n in (1, 2) for m in ("light", "dark")
          if (HERE/f"figure{n}_{m}.png").exists()) if list(HERE.glob("figure*.png")) else 0
E_DAYS, O_DAYS = 2940, 2922

pytestmark = pytest.mark.skipif(not DAILY.exists(), reason="raw data not present; see VERIFY.md")

def _png_size(path):
    """Width and height from the PNG IHDR chunk, no image library needed."""
    d = Path(path).read_bytes()
    assert d[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")


@pytest.fixture(scope="session")
def N(): return json.loads((HERE/"numbers.json").read_text())
@pytest.fixture(scope="session")
def grid(): return pd.read_csv(HERE/"grid_H49.csv")


# ========================= 1. RAW-INPUT CONTRACT =========================

def test_raw_input_hashes_unchanged():
    for p in (DAILY, HOURLY):
        assert A.sha256(p) == A.EXPECTED_SHA256[p.name], f"{p.name} is not the pinned file"

def test_raw_daily_counts_unchanged(N):
    d = pd.read_csv(DAILY, low_memory=False)
    assert len(d) == 7410 == N["raw_daily_rows_all_file"]
    assert d["id"].nunique() == 71 == N["raw_participants_in_fitbit_export"]

def test_raw_hourly_counts_and_known_defect_unchanged():
    raw = pd.read_csv(HOURLY, low_memory=False, usecols=["id","date","hour"])
    assert len(raw) == 159508
    over = raw.groupby(["id","date"]).size()
    assert int((over > 24).sum()) == 68 and over.max() == 25
    assert len(A.load_hourly(HOURLY)) == 159438, "70 duplicate (id,date,hour) rows are removed"


# ===================== 2. PARSER / SOURCE CONTRACT ======================

def test_only_covered_bson_types_are_exercised(N):
    """The hand-written reader is the single point of failure for every
    SEMA-derived number. Assert the files contain ONLY types the fixture
    covers, so a new type fails loudly instead of taking an untested branch."""
    seen = minibson.type_census(SEMA) | minibson.type_census(SURV)
    assert seen <= BN.ALLOWED_BSON_TYPES, f"uncovered types {[hex(t) for t in seen - BN.ALLOWED_BSON_TYPES]}"
    assert sorted(hex(t) for t in seen) == N["bson_types_exercised"]
    assert 0x09 not in seen, "no BSON datetimes: the utcfromtimestamp path is never used here"

def test_sema_timestamps_are_strings_not_bson_datetimes():
    """Recorded because it settles the timezone question: the timestamps are
    naive local wall-clock text, so no conversion is applied (WINDOW_RULE 7.6)."""
    d = minibson.read(SEMA, limit=1)[0]
    assert isinstance(d["data"]["SCHEDULED_TS"], str)
    assert "T" in d["data"]["SCHEDULED_TS"] and "+" not in d["data"]["SCHEDULED_TS"]

def test_prompt_counts_agree_with_an_independent_type_census(N):
    """Outside check on the parser: counting BSON type bytes for COMPLETED_TS
    and EXPIRED_TS must reproduce the prompt categories without using the
    parsed values at all."""
    import struct, collections
    b = SEMA.read_bytes(); cnt = collections.Counter(); i = 0
    def walk(b, start):
        n = struct.unpack_from('<i', b, start)[0]; i = start+4
        while b[i] != 0:
            t = b[i]; i += 1
            j = b.index(b'\x00', i); k = b[i:j].decode(); i = j+1
            if k in ("COMPLETED_TS", "EXPIRED_TS"): cnt[(k, t)] += 1
            if t in (0x03, 0x04): walk(b, i)
            _, i = minibson._val(b, i, t)
        return start + n
    while i < len(b): i = walk(b, i)
    assert cnt[("COMPLETED_TS", 0x02)] == N["sema_completed_prompts_total"] == 6959
    assert cnt[("EXPIRED_TS", 0x02)] == 8357
    assert cnt[("COMPLETED_TS", 0x0A)] + cnt[("COMPLETED_TS", 0x02)] == 15380

def test_sema_source_shape(N):
    docs = minibson.read(SEMA)
    assert len(docs) == 15380 == N["sema_prompt_documents_total"]
    assert len({d["user_id"] for d in docs}) == 63

def test_surveys_source_shape(N):
    docs = minibson.read(SURV)
    assert len(docs) == 935 == N["survey_records_total"]
    assert len({d["user_id"] for d in docs}) == 67 == N["survey_participants_n"]

def test_present_timestamps_never_coerce_silently(N):
    """errors='coerce' turns an unparseable string into NaT, indistinguishable
    from an absent value. parse_ts refuses that; prove it raises."""
    bad = pd.Series(["2021-05-24T09:00:00", "not-a-timestamp"])
    try:
        BN.parse_ts(bad, "fixture")
    except ValueError as e:
        assert "failed to parse" in str(e)
    else:
        raise AssertionError("parse_ts accepted an unparseable present value")
    assert N["survey_records_submitdate_unparsed"] == 0


# ==================== 3. CALENDAR-DAY CONTRACT (NEW) ====================
# The 2026-09-14 02:31 build subtracted a wall-clock instant from a midnight
# date. For a 09:00 first prompt that floors to -1, so day zero landed on the
# day AFTER the first prompt's calendar date, shifting every window forward.

def test_non_midnight_first_prompt_puts_day_zero_on_its_own_calendar_date():
    first = pd.Series([pd.Timestamp("2021-05-24 20:19:00")])
    first_date = BN.calendar_date(first).iloc[0]
    assert first_date == pd.Timestamp("2021-05-24"), "day zero is the DATE of the first prompt"
    dates = pd.Series(pd.date_range("2021-05-24", periods=H+2, freq="D"))
    day = (dates - first_date).dt.days
    assert day.iloc[0] == 0, "the first prompt's own calendar date is day 0"
    assert dates[day == H-1].iloc[0] == pd.Timestamp("2021-07-11"), "last included date is day 48"
    assert int(((day >= 0) & (day < H)).sum()) == H

def test_the_uncorrected_expression_reproduces_the_defect():
    """Pin the bug itself, so a regression is recognisable rather than merely wrong."""
    first_ts = pd.Timestamp("2021-05-24 09:00:00")
    dates = pd.Series([pd.Timestamp("2021-05-24")])
    assert (dates - first_ts).dt.days.iloc[0] == -1, "negative timedeltas floor, they do not truncate"
    assert (dates - first_ts.normalize()).dt.days.iloc[0] == 0

def test_every_participant_is_affected_not_a_corner_case(N):
    assert N["participants_with_non_midnight_first_prompt"] == 63 == \
        N["sema_anchored_cohort_n_participants"], "all 63, so the shift was universal"

def test_exposure_spans_calendar_dates(N):
    ex = pd.read_csv(HERE/"exposure_windows.csv", parse_dates=["first","last"], index_col="id")
    assert (ex["first"].dt.normalize() == ex["first"]).all(), "windows are stored as dates"
    assert (ex["last"].dt.normalize() == ex["last"]).all()
    assert (ex["exposure"] == (ex["last"] - ex["first"]).dt.days + 1).all()


# ========================= 4. COHORT CONTRACT ===========================

def test_cohort_cascade(N):
    assert N["provenance_cohort_n_participants"] == 71
    assert N["sema_anchored_cohort_n_participants"] == 63
    assert N["fixed_horizon_cohort_n_participants"] == N_COHORT == 60
    assert N["observation_horizon_H_days"] == H

def test_exclusions_account_for_every_participant(N):
    assert N["excluded_no_sema_anchor_n_participants"] == 8
    assert N["excluded_exposure_below_H_n_participants"] == 3
    assert (N["fixed_horizon_cohort_n_participants"]
            + N["excluded_exposure_below_H_n_participants"]
            + N["excluded_no_sema_anchor_n_participants"]) == 71

def test_cohort_identity_not_merely_its_size(N, grid):
    """Same count can hide a swapped member. Pin the set."""
    ids = N["fixed_horizon_cohort_ids_sorted"]
    assert len(ids) == 60 == len(set(ids))
    assert sorted(grid["id"].unique()) == ids
    assert set(ids) <= set(N["sema_anchored_cohort_ids_sorted"])

def test_H_is_frozen_at_49_and_the_rule_now_yields_50(N):
    """H was chosen mechanically under the defective date arithmetic. Under the
    corrected convention the same rule yields 50. H stays 49 because it was
    pre-committed; the discrepancy is recorded, not silently absorbed."""
    ex = pd.read_csv(HERE/"exposure_windows.csv", parse_dates=["first","last"])
    exp = ex["exposure"]
    need = int(np.ceil(0.95*len(exp)))
    assert need == N["H_rule_min_participants_required"] == 60
    assert int((exp >= 49).sum()) >= need
    assert int((exp >= 50).sum()) >= need, "the rule now admits 50"
    assert int((exp >= 51).sum()) < need
    assert N["H_rule_reexecuted_under_corrected_calendar"] == 50
    assert N["H_frozen_value_retained"] == 49 == N["observation_horizon_H_days"]


# ========================== 5. GRID CONTRACT ============================

def test_grid_is_exactly_the_expected_day_product(grid, N):
    assert len(grid) == 60*H == E_DAYS == N["expected_participant_days_in_grid"]
    assert not grid.duplicated(subset=["id","sema_day"]).any()
    assert grid["id"].nunique() == 60
    assert (grid.groupby("id").size() == H).all(), "every participant needs exactly 49 rows"
    assert set(grid["sema_day"]) == set(range(H))

def test_observed_and_absent_split(grid, N):
    assert int(grid["source_row_present"].sum()) == O_DAYS == N["observed_participant_days_in_grid"]
    assert int((~grid["source_row_present"]).sum()) == E_DAYS-O_DAYS == N["absent_participant_days_in_grid"]

def test_join_is_one_to_one_and_loses_no_observation():
    """validate='one_to_one' and indicator= are the provenance guarantees: no
    fan-out, and no observed row silently falling outside the grid."""
    daily = A.load_daily(DAILY)
    f = A.valid_day_flags(daily)
    daily["loose"], daily["primary"] = f["loose"].values, f["primary"].values
    ex = pd.read_csv(HERE/"exposure_windows.csv", parse_dates=["first","last"], index_col="id")
    co = ex[ex["exposure"] >= H]
    obs = daily.merge(co[["first"]], left_on="id", right_index=True, how="inner")
    obs["sema_day"] = (obs["date"] - obs["first"]).dt.days
    obs = obs[(obs.sema_day >= 0) & (obs.sema_day < H)]
    assert not obs.duplicated(["id","sema_day"]).any()
    g = pd.MultiIndex.from_product([co.index, range(H)], names=["id","sema_day"]).to_frame(index=False)
    m = g.merge(obs[["id","sema_day"]].assign(seen=True), on=["id","sema_day"],
                how="left", indicator=True, validate="one_to_one")
    assert (m["_merge"] == "right_only").sum() == 0, "an observation escaped the grid"
    assert int((m["_merge"] == "both").sum()) == O_DAYS


# ====================== 6. MISSING-DAY INVARIANT ========================

def test_absent_source_rows_are_invalid_under_both_definitions(grid):
    absent = grid[~grid["source_row_present"]]
    assert len(absent) == E_DAYS - O_DAYS == 18
    assert not absent["loose"].any() and not absent["primary"].any()


# ===================== 7. SIGNAL NESTING INVARIANT ======================

def test_primary_is_a_strict_subset_of_loose(grid):
    """The bootstrap-boundary explanation depends on this. If it ever fails,
    the claim that the yield ratio is capped at 1.0 fails with it."""
    assert (grid["primary"] <= grid["loose"]).all()

def test_every_primary_completer_is_a_loose_completer(grid):
    u = grid.groupby("id")[["loose","primary"]].sum()
    assert set(u.index[u["primary"] >= K]) <= set(u.index[u["loose"] >= K])


# ============ 8. EXPECTED-DAY vs OBSERVED-ROW DENOMINATORS ==============

def test_both_denominators_pinned_and_distinct(N, grid):
    assert N["valid_days_loose_n"] == 2357 == int(grid["loose"].sum())
    assert N["valid_days_primary_n"] == 2217 == int(grid["primary"].sum())
    assert N[f"expected_day_yield_loose_pct_of_{E_DAYS}_expected_days"] == 80.17
    assert N[f"observed_row_validity_loose_pct_of_{O_DAYS}_observed_rows"] == 80.66
    assert N[f"expected_day_yield_primary_pct_of_{E_DAYS}_expected_days"] == 75.41
    assert N[f"observed_row_validity_primary_pct_of_{O_DAYS}_observed_rows"] == 75.87
    assert round(100*2357/E_DAYS, 2) == 80.17 and round(100*2357/O_DAYS, 2) == 80.66
    assert E_DAYS != O_DAYS, "the two denominators must stay distinct"


# ======================= 9. SEMA PROMPT SEMANTICS =======================

def test_prompt_outcome_categories_are_exhaustive_and_disjoint(N):
    assert N["sema_expired_and_not_completed_prompts"] == 8357
    assert N["sema_both_completed_and_expired_prompts"] == 0, "categories must be disjoint"
    assert N["sema_neither_completed_nor_expired_prompts"] == 64
    assert (N["sema_completed_and_not_expired_prompts"]
            + N["sema_expired_and_not_completed_prompts"]
            + N["sema_both_completed_and_expired_prompts"]
            + N["sema_neither_completed_nor_expired_prompts"]) == 15380


# ======================== 10. PROVENANCE FINDINGS =======================

def test_cross_round_counts_are_derived_not_transcribed(N):
    R1e, R2s = pd.Timestamp("2021-07-26"), pd.Timestamp("2021-11-15")
    d = A.load_daily(DAILY)
    fb = d.groupby("id")["date"].agg(first="min", last="max")
    assert int(((fb["first"] <= R1e) & (fb["last"] >= R2s)).sum()) == 9 == N["cross_round_ids_under_fitbit_clock"]
    ex = pd.read_csv(HERE/"exposure_windows.csv", parse_dates=["first","last"], index_col="id")
    assert int(((ex["first"] <= R1e) & (ex["last"] >= R2s)).sum()) == 1 == N["cross_round_ids_under_sema_clock"]
    assert N["published_repeat_participants"] == 1

def test_survey_sentinel_claim_is_no_stronger_than_the_evidence(N):
    """'at least one record carrying the sentinel' - not 'timestamps invalid'."""
    assert N["survey_records_with_pre1990_sentinel"] == 66
    assert N["survey_participants_with_at_least_one_pre1990_sentinel_record"] == 66
    assert N["survey_sentinel_distinct_values"] == ["1980-01-01"], "one sentinel value, stated exactly"

def test_ratio_curve_monotonicity_is_measured_not_assumed(N):
    """A previous write-up asserted the ratio declines monotonically. It does
    not. Each attainment curve is non-increasing; their ratio need not be."""
    c = N["usable_day_curve_K7_to_K49"]
    for c_name in ("loose", "primary"):
        vals = [c[str(k)][c_name] for k in range(7, H+1)]
        assert all(b <= a + 1e-12 for a, b in zip(vals, vals[1:])), "each curve IS non-increasing"
    # ratios come from COUNTS, never from the rounded percentages
    for k in range(7, H+1):
        e = c[str(k)]
        assert e["ratio"] == round(e["primary_n"]/e["loose_n"], 4)
        assert e["primary_n"] <= e["loose_n"], "nesting must hold at every K"
    r = [c[str(k)]["ratio"] for k in range(7, H+1)]
    rises = [k for k, a, b in zip(range(7, H+1), r, r[1:]) if b > a + 1e-12]
    assert rises == N["ratio_curve_K_values_where_ratio_rises"]
    assert rises, "the ratio is NOT monotone; the retracted claim stays retracted"
    assert N["ratio_curve_is_monotone_nonincreasing"] is False


def test_observed_estimates_equal_their_own_counts(N):
    """An earlier draft reported the bootstrap medians as if they were the
    observed values. Each quantity is checked against its OWN independent
    computation; whether the two happen to differ is incidental to this
    dataset and is not asserted."""
    assert N["observed_yield_ratio_primary_over_loose"] == round(
        N["reaching_K21_primary_n_of_60"] / N["reaching_K21_loose_n_of_60"], 4) == 0.9623
    assert N["observed_enrollment_multiplier_primary_over_loose"] == round(
        N["enroll_for_50_at_K21_primary"] / N["enroll_for_50_at_K21_loose"], 4) == 1.0351
    # the bootstrap median is verified separately, by re-running the resample,
    # in test_bootstrap_is_reexecuted_not_transcribed


def test_sema_prompts_are_not_confined_to_the_published_windows(N):
    """The figure showed prompts before round 1; an earlier caption said the
    prompts were confined to the windows. Pin the actual counts."""
    inside = N["sema_prompts_inside_published_rounds"]
    outside = N["sema_prompts_outside_published_rounds"]
    assert inside + outside == N["sema_scheduled_prompts_total"] == 15380
    assert outside == 238 > 0, "not confined; 'largely concentrated within' is the claim"
    assert N["sema_participants_with_any_prompt_outside_published_rounds"] == 2
    assert N["sema_prompts_before_round1"] == outside, "all of them precede round 1"
    assert N["sema_prompts_between_rounds"] == 0 and N["sema_prompts_after_round2"] == 0
    # participant-days are the only unit comparable to the Fitbit figures;
    # prompt counts weight each day by how many prompts it carried
    assert N["sema_participant_days_outside_published_rounds"] == 70
    assert N["sema_participant_days_total"] == 3886
    assert N["sema_participant_days_outside_published_rounds_pct"] == 1.8
    assert N["sema_participant_days_total"] != N["sema_scheduled_prompts_total"], \
        "the two denominators are different units and must not be conflated"
    # like-for-like: participant-days against participant-days
    assert N["fitbit_participant_days_outside_published_rounds_pct"] > \
        N["sema_participant_days_outside_published_rounds_pct"]


def test_figure2_regenerates_and_asserts_its_own_caption(tmp_path):
    """figure2.py refuses to write if any caption number disagrees with
    numbers.json, or if nesting fails at any K it draws."""
    r = subprocess.run([sys.executable, str(HERE/"figure2.py"), "--out-dir", str(tmp_path)],
                       capture_output=True, text=True, cwd=str(HERE))
    assert r.returncode == 0, r.stderr[-2000:]
    for m in ("light", "dark"):
        fresh, committed = tmp_path/f"figure2_{m}.png", HERE/f"figure2_{m}.png"
        assert fresh.exists() and fresh.stat().st_size > 50_000, f"{fresh.name} did not render"
        # Pixel dimensions come from figsize x dpi and are deterministic. The
        # BYTES are not: matplotlib output depends on the installed fonts,
        # FreeType and libpng, so a render on another machine is legitimately
        # different. An earlier version compared bytes and failed on Windows
        # while the figure was correct. The substantive guarantee is the
        # returncode above: figure2.py asserts every caption number
        # against numbers.json and refuses to write if any disagrees.
        assert _png_size(fresh) == _png_size(committed), \
            f"{committed.name} render size changed: {_png_size(fresh)} vs {_png_size(committed)}"
    # the committed PNGs must be untouched by this test
    assert not any((HERE/f"figure2_{m}.png").stat().st_mtime > _T0 for m in ("light", "dark")), \
        "the test wrote to a committed figure"


def test_figure2_generated_caption_states_the_criterion_was_not_met(N):
    """Assert the caption ACTUALLY HANDED TO THE RENDERER, not the source file.

    Searching figure2.py for "not met" would also match a comment or an unused
    literal, which is not the same guarantee. build_caption() returns exactly
    what draw() renders, so check that, together with its numbers."""
    import figure2
    cap = figure2.build_caption(N)
    text = " ".join(f"{lab} {body}" for lab, body in cap)
    assert "not met" in text.lower(), "the caption must say the criterion was not met"
    assert "not a finding of no difference" in text
    assert "no significance is claimed at any k" in text.lower()
    # and the numbers in that generated text must be the committed ones
    c = N["usable_day_curve_K7_to_K49"]["21"]
    assert f"{c['loose_n']} of 60" in text and f"{c['primary_n']} of 60" in text
    assert str(N["observed_yield_ratio_primary_over_loose"]) in text
    assert f"{N['bootstrap']['yield_ratio_ci_lo_unrounded']:.4f}" in text
    assert f"{N['bootstrap']['yield_ratio_ci_hi_unrounded']:.4f}" in text
    assert str(N["H_rule_reexecuted_under_corrected_calendar"]) in text
    assert N["headline_criterion_met"] is False


def test_figure1_generated_caption_carries_its_numbers(N):
    """Same guarantee for Figure 1: check the generated strings, not the file."""
    import figure1
    text = " ".join(f"{lab} {body}" for lab, body in figure1.build_caption(N))
    assert f"{N['fitbit_participant_days_outside_published_rounds']:,}" in text
    assert f"{N['fitbit_participant_days_outside_published_rounds_pct']}%" in text
    assert f"{N['sema_participant_days_outside_published_rounds']} of" in text
    assert "should not be treated as a verified participant-specific exposure window" in text
    assert "not a controlled comparison on identical participants" in text


def test_nesting_permits_equality_at_every_K(N):
    """STRUCTURAL: the subset relation gives primary_n <= loose_n at every K and
    permits equality. True of any dataset under these definitions."""
    c = N["usable_day_curve_K7_to_K49"]
    for k in range(7, H+1):
        assert c[str(k)]["primary_n"] <= c[str(k)]["loose_n"], f"nesting fails at K={k}"
        assert 0.0 <= c[str(k)]["ratio"] <= 1.0, f"ratio out of bounds at K={k}"


def test_where_equality_actually_occurs_in_this_dataset(N):
    """DATASET RESULT, kept separate from the structural test above: in this
    cohort the two counts coincide at K = 7-11. Pinned so a change is visible,
    not offered as the reason equality is permitted."""
    c = N["usable_day_curve_K7_to_K49"]
    equal_at = [k for k in range(7, H+1) if c[str(k)]["primary_n"] == c[str(k)]["loose_n"]]
    assert equal_at == [7, 8, 9, 10, 11], f"equality now occurs at {equal_at}"
    assert all(c[str(k)]["ratio"] == 1.0 for k in equal_at)


def test_figure2_caption_describes_nesting_correctly(N):
    """Verify the intended statement is present, rather than forbidding a word:
    the caption must describe a subset relation and say what it implies for the
    curve. A caption that merely omits 'strict' has not said anything."""
    import figure2
    text = " ".join(b for _, b in figure2.build_caption(N)).lower()
    assert "subset of loose" in text, "the caption must state the subset relation"
    assert "never sit above" in text, "and what that implies for the curve"
    assert "equality permitted" in text, "and that equality is permitted"


def test_figure1_regenerates_and_asserts_its_own_caption(tmp_path):
    """figure1.py refuses to write if any caption number disagrees with
    numbers.json. Run it and require both renders."""
    r = subprocess.run([sys.executable, str(HERE/"figure1.py"), "--out-dir", str(tmp_path)],
                       capture_output=True, text=True, cwd=str(HERE))
    assert r.returncode == 0, r.stderr[-2000:]
    for m in ("light", "dark"):
        fresh, committed = tmp_path/f"figure1_{m}.png", HERE/f"figure1_{m}.png"
        assert fresh.exists() and fresh.stat().st_size > 50_000, f"{fresh.name} did not render"
        # Pixel dimensions come from figsize x dpi and are deterministic. The
        # BYTES are not: matplotlib output depends on the installed fonts,
        # FreeType and libpng, so a render on another machine is legitimately
        # different. An earlier version compared bytes and failed on Windows
        # while the figure was correct. The substantive guarantee is the
        # returncode above: figure1.py asserts every caption number
        # against numbers.json and refuses to write if any disagrees.
        assert _png_size(fresh) == _png_size(committed), \
            f"{committed.name} render size changed: {_png_size(fresh)} vs {_png_size(committed)}"
    # the committed PNGs must be untouched by this test
    assert not any((HERE/f"figure1_{m}.png").stat().st_mtime > _T0 for m in ("light", "dark")), \
        "the test wrote to a committed figure"


# ======================== 11. BOOTSTRAP CONTRACT ========================

def test_bootstrap_is_reexecuted_not_transcribed(N):
    """Rerun the resample from the committed usable-day table under the same
    seed and require it to reproduce numbers.json. Comparing stored values to
    themselves proves nothing."""
    u = pd.read_csv(HERE/"usable_days_H49.csv", index_col="id").sort_index()
    assert len(u) == 60
    rng = np.random.default_rng(N["bootstrap"]["seed"])
    ids = u.index.values; yld = []
    for _ in range(N["bootstrap"]["replicates_requested"]):
        smp = rng.choice(ids, size=len(ids), replace=True)
        a = (u.loc[smp,"primary"] >= K).mean(); b = (u.loc[smp,"loose"] >= K).mean()
        if a > 0 and b > 0: yld.append(a/b)
    yld = np.array(yld)
    assert len(yld) == N["bootstrap"]["replicates_used"]
    assert abs(float(np.percentile(yld, 2.5)) - N["bootstrap"]["yield_ratio_ci_lo_unrounded"]) < 1e-12
    assert abs(float(np.percentile(yld, 97.5)) - N["bootstrap"]["yield_ratio_ci_hi_unrounded"]) < 1e-12
    assert abs(float(np.median(yld)) - N["bootstrap"]["yield_ratio_primary_over_loose_median"]) < 1e-12

def test_bootstrap_interval_sits_against_the_parameter_boundary(N):
    b = N["bootstrap"]
    assert b["share_replicates_yield_ratio_gt_1"] == 0.0, "ratio is capped at 1 by nesting"
    assert b["yield_ratio_ci_hi_unrounded"] == 1.0, "boundary, not a rounding artifact"
    assert b["share_replicates_yield_ratio_ge_1"] > 0, "the cap is attained, so the CI touches it"
    assert "boundary" in b["note"], "the specification defect stays on the record"

def test_null_condition_two_fired_and_headline_not_claimed(N):
    b = N["bootstrap"]
    assert b["yield_ratio_ci_lo_unrounded"] <= 1.0 <= b["yield_ratio_ci_hi_unrounded"]
    assert N["null_condition_2_fired"] is True
    assert N["headline_criterion_met"] is False


# ================= 12. ISOLATED REBUILD CONTRACT (NEW) ==================

def test_committed_artifacts_use_lf_line_endings():
    """The byte-identical rebuild only holds across platforms if the writers
    force LF. Python's write_text and pandas to_csv translate to CRLF on
    Windows, so a Windows rebuild produced identical VALUES and different
    BYTES. Found the first time the suite ran on Windows, 2026-09-14."""
    for name in ("numbers.json", "grid_H49.csv", "exposure_windows.csv",
                 "usable_days_H49.csv"):
        data = (HERE/name).read_bytes()
        assert b"\r\n" not in data, f"{name} contains CRLF; the rebuild will not match on Linux"


def test_source_to_artifact_rebuild_into_empty_dirs_is_exact(tmp_path):
    """The freeze gate. Rebuild from source into two empty directories with
    paths supplied explicitly; require the full parsed JSON and every table to
    match the committed artifacts, and the two runs to match each other.
    Committed artifacts are never written during this test."""
    outs = []
    for name in ("a", "b"):
        d = tmp_path/name; d.mkdir()
        r = subprocess.run([sys.executable, str(HERE/"build_numbers.py"),
                            "--data-dir", str(DATA), "--sema-dir", str(MONGO),
                            "--src-dir", str(HERE/"src"), "--out-dir", str(d)],
                           capture_output=True, text=True, cwd=str(tmp_path))
        assert r.returncode == 0, r.stderr[-2000:]
        outs.append(d)

    committed = json.loads((HERE/"numbers.json").read_text())
    for d in outs:
        assert json.loads((d/"numbers.json").read_text()) == committed, \
            f"rebuilt numbers.json differs from the committed one ({d.name})"
    for f in ("numbers.json", "grid_H49.csv", "exposure_windows.csv", "usable_days_H49.csv"):
        assert (outs[0]/f).read_bytes() == (outs[1]/f).read_bytes(), f"{f} is not deterministic"
        a = (outs[0]/f).read_bytes(); c = (HERE/f).read_bytes()
        assert a == c, f"{f} does not reproduce the committed artifact"

def test_build_does_not_read_from_its_own_output_directory(tmp_path):
    """An output directory that already holds stale artifacts must not change
    the result; if it did, the build would be reading its own output."""
    d = tmp_path/"dirty"; d.mkdir()
    (d/"numbers.json").write_text('{"sabotage": true}\n')
    (d/"grid_H49.csv").write_text("id,sema_day\nx,0\n")
    r = subprocess.run([sys.executable, str(HERE/"build_numbers.py"),
                        "--data-dir", str(DATA), "--sema-dir", str(MONGO),
                        "--src-dir", str(HERE/"src"), "--out-dir", str(d)],
                       capture_output=True, text=True, cwd=str(tmp_path))
    assert r.returncode == 0, r.stderr[-2000:]
    assert json.loads((d/"numbers.json").read_text()) == json.loads((HERE/"numbers.json").read_text())


# ==================== 13. EXECUTION CONTRACT (NEW) ======================

def test_every_published_key_is_emitted_by_the_build(N):
    """Nothing may be quoted anywhere that the build does not emit."""
    for key in ("observation_horizon_H_days", "fixed_horizon_cohort_n_participants",
                "expected_participant_days_in_grid", "absent_participant_days_in_grid",
                f"expected_day_yield_loose_pct_of_{E_DAYS}_expected_days",
                f"observed_row_validity_loose_pct_of_{O_DAYS}_observed_rows",
                "reaching_K21_primary_n_of_60", "cross_round_ids_under_sema_clock",
                "H_rule_reexecuted_under_corrected_calendar",
                "participants_with_non_midnight_first_prompt",
                "ratio_curve_is_monotone_nonincreasing",
                "bootstrap", "null_condition_2_fired", "headline_criterion_met"):
        assert key in N, f"build_numbers.py did not emit {key}"

def test_runner_reports_a_skipped_suite_as_incomplete_not_green(tmp_path):
    """Found while packaging: with the gitignored data absent, 35 of 39 tests
    skipped and the runner still printed failed=0, which reads as a pass. A
    skipped suite is not a verification, so it must not exit 0."""
    # mirror the packaged repo exactly: some tests run, others skip because
    # the gitignored raw data is absent. executed>0, so exit 2 does not apply.
    (tmp_path/"test_needs_data.py").write_text(
        "import pytest\n"
        "pytestmark = pytest.mark.skipif(True, reason='data absent')\n"
        "def test_needs_the_csv():\n    assert False\n")
    (tmp_path/"test_runs_anyway.py").write_text("def test_pure():\n    assert True\n")
    r = subprocess.run([sys.executable, str(HERE/"run_tests.py"), "--self-check-empty",
                        str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 3, f"skipped suite must exit 3, got {r.returncode}: {r.stdout[-500:]}"
    assert "INCOMPLETE" in r.stdout and "gate is exit 0" in r.stdout


def test_runner_installs_its_shim_even_when_real_pytest_is_present(tmp_path):
    """Found by running the suite on a machine that had pytest installed.

    The runner used to defer to real pytest when it was importable. Real
    pytest's @fixture leaves none of the markers this runner looks for, so
    every fixture-taking test died with KeyError: no fixture named 'N' -- 37
    of 49 failures, none of them real. Reproduced here with a stand-in pytest
    on the path: the run must still resolve fixtures and pass."""
    fake = tmp_path/"fake"; fake.mkdir()
    (fake/"pytest.py").write_text(
        "def fixture(func=None, **kw):\n"
        "    def wrap(f): return f\n"
        "    return wrap(func) if func else wrap\n"
        "class _M:\n"
        "    def skipif(self, c, reason=''):\n"
        "        def d(f): return f\n"
        "        return d\n"
        "mark = _M()\n"
        "def skip(reason=''): raise Exception('skipped')\n")
    suite = tmp_path/"suite"; suite.mkdir()
    (suite/"test_uses_a_fixture.py").write_text(
        "import pytest\n"
        "@pytest.fixture(scope='session')\n"
        "def thing(): return 7\n"
        "def test_it(thing): assert thing == 7\n")
    env = dict(os.environ, PYTHONPATH=str(fake))
    r = subprocess.run([sys.executable, str(HERE/"run_tests.py"), "--self-check-empty",
                        str(suite)], capture_output=True, text=True, env=env)
    assert "no fixture named" not in (r.stdout + r.stderr), \
        "the runner deferred to real pytest and could not resolve fixtures"
    assert r.returncode == 0, r.stdout[-800:]


def test_runner_fails_when_no_tests_execute(tmp_path):
    """The suite must be able to tell 'everything passed' from 'nothing ran'."""
    (tmp_path/"test_empty_suite.py").write_text("x = 1\n")
    r = subprocess.run([sys.executable, str(HERE/"run_tests.py"), "--self-check-empty",
                        str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 2, f"empty suite must exit 2, got {r.returncode}: {r.stdout[-500:]}"
    assert "zero tests executed" in r.stdout
