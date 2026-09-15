"""Regenerate numbers.json and the derived tables under the frozen design
(WINDOW_RULE.md v2).

Every key carries its denominator. Nothing appears in any figure, table or
write-up that is not a key in this file.

Source paths are explicit arguments so this can be rebuilt into an empty
directory and compared against the committed artifacts. Nothing is read from
the output directory and nothing outside it is written.

CALENDAR-DAY CONVENTION (corrected 2026-09-14, see WINDOW_RULE.md 7.6)
---------------------------------------------------------------------
SEMA timestamps are BSON strings (type 0x02) holding naive local wall-clock
ISO text, e.g. '2021-12-15T15:16:00'. Fitbit daily rows carry naive local
calendar dates, e.g. '2021-05-24'. Both are already in the study's local
convention, so calendar dates are taken by truncating the SEMA wall clock to
midnight. No timezone conversion is applied and none would be justified: the
SEMA strings carry no offset, and converting one side only would move dates.

Study-day offsets and exposure spans are computed between calendar DATES, not
between a date and a wall-clock instant. Subtracting a 09:00 timestamp from a
midnight date yields a negative timedelta that floors to -1 day, which shifted
every window forward by one day in the 2026-09-14 02:31 build.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

H, K_PRIMARY, TARGET, B, SEED = 49, 21, 50, 10000, 20260914
RETENTION = 0.95
R1 = (pd.Timestamp('2021-05-24'), pd.Timestamp('2021-07-26'))
R2 = (pd.Timestamp('2021-11-15'), pd.Timestamp('2022-01-17'))

# BSON type bytes the SEMA/survey parse is allowed to encounter. Asserted, so a
# different dataset build that introduces a new type fails loudly instead of
# flowing through an untested branch of the hand-written reader.
ALLOWED_BSON_TYPES = {0x01, 0x02, 0x03, 0x07, 0x0A, 0x10}


def calendar_date(ts: pd.Series) -> pd.Series:
    """Local calendar date of a naive wall-clock timestamp, as midnight.

    The single place the date convention is applied. See module docstring.
    """
    if not pd.api.types.is_datetime64_any_dtype(ts):
        raise TypeError(f'calendar_date expects datetimes, got {ts.dtype}')
    if getattr(ts.dtype, 'tz', None) is not None:
        raise ValueError('timestamps are tz-aware; the source convention is naive local')
    return ts.dt.normalize()


def parse_ts(raw: pd.Series, field: str) -> pd.Series:
    """Parse SEMA wall-clock strings, refusing silent coercion.

    pd.to_datetime(errors='coerce') turns an unparseable string into NaT, which
    is indistinguishable downstream from a genuinely absent timestamp. Absent
    values here are BSON null and arrive as None; anything that is a string but
    fails to parse is an error, not a missing value.
    """
    out = pd.to_datetime(raw, errors='coerce')
    bad = out.isna() & raw.notna()
    if bad.any():
        raise ValueError(f'{field}: {int(bad.sum())} present values failed to parse, '
                         f'e.g. {raw[bad].head(3).tolist()}')
    return out


def build(data_dir: Path, sema_dir: Path, out_dir: Path, src_dir: Path) -> dict:
    # code lives next to src/, never in the output directory
    sys.path.insert(0, str(Path(src_dir).resolve()))
    sys.path.insert(0, str(Path(src_dir).resolve().parent / 'sema'))
    import adherence as A, minibson

    data_dir, out_dir = Path(data_dir), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    n: dict = {}

    # ---- raw-input contract: unchanged bytes, unchanged counts
    daily_csv = data_dir / 'daily_fitbit_sema_df_unprocessed.csv'
    n['input_sha256_daily'] = A.sha256(daily_csv)
    if n['input_sha256_daily'] != A.EXPECTED_SHA256[daily_csv.name]:
        raise SystemExit('daily CSV does not match the pinned hash')
    daily = A.load_daily(daily_csv)
    flags = A.valid_day_flags(daily)
    daily['loose'], daily['primary'] = flags['loose'].values, flags['primary'].values
    if daily.duplicated(['id', 'date']).any():
        raise SystemExit('daily file has duplicate (id, date) rows')
    n['raw_daily_rows_all_file'] = int(len(daily))
    n['raw_participants_in_fitbit_export'] = int(daily['id'].nunique())

    # ---- SEMA exposure
    sema_path = sema_dir / 'sema.bson'
    surv_path = sema_dir / 'surveys.bson'
    n['input_sha256_sema_bson'] = A.sha256(sema_path)
    n['input_sha256_surveys_bson'] = A.sha256(surv_path)
    for p in (sema_path, surv_path):
        seen = minibson.type_census(p)
        stray = set(seen) - ALLOWED_BSON_TYPES
        if stray:
            raise SystemExit(f'{p.name}: unexpected BSON types {[hex(t) for t in stray]}')
    n['bson_types_exercised'] = sorted(
        hex(t) for t in set(minibson.type_census(sema_path)) | set(minibson.type_census(surv_path)))

    sdocs = minibson.read(sema_path)
    s = pd.DataFrame([{'id': d['user_id'],
                       'sched': d['data'].get('SCHEDULED_TS'),
                       'comp':  d['data'].get('COMPLETED_TS'),
                       'exp':   d['data'].get('EXPIRED_TS')} for d in sdocs])
    for c in ('sched', 'comp', 'exp'):
        s[c] = parse_ts(s[c], c)
    n['sema_prompt_documents_total'] = int(len(s))
    n['sema_scheduled_prompts_total'] = int(s['sched'].notna().sum())
    n['sema_completed_prompts_total'] = int(s['comp'].notna().sum())
    n['sema_expired_and_not_completed_prompts'] = int((s['exp'].notna() & s['comp'].isna()).sum())
    n['sema_completed_and_not_expired_prompts'] = int((s['comp'].notna() & s['exp'].isna()).sum())
    n['sema_both_completed_and_expired_prompts'] = int((s['comp'].notna() & s['exp'].notna()).sum())
    n['sema_neither_completed_nor_expired_prompts'] = int((s['comp'].isna() & s['exp'].isna()).sum())
    n['sema_response_rate_pct_of_scheduled'] = round(
        100 * s['comp'].notna().sum() / s['sched'].notna().sum(), 1)

    # ---- exposure window, in CALENDAR DAYS (see module docstring)
    sc = s.dropna(subset=['sched']).copy()
    sc['sched_date'] = calendar_date(sc['sched'])
    ex = sc.groupby('id')['sched_date'].agg(first='min', last='max')
    ex['exposure'] = (ex['last'] - ex['first']).dt.days + 1
    n['participants_with_non_midnight_first_prompt'] = int(
        (sc.groupby('id')['sched'].min().dt.normalize()
         != sc.groupby('id')['sched'].min()).sum())

    # ---- SEMA prompts vs the published windows, SAME calendar boundaries
    s_in1 = (sc['sched_date'] >= R1[0]) & (sc['sched_date'] <= R1[1])
    s_in2 = (sc['sched_date'] >= R2[0]) & (sc['sched_date'] <= R2[1])
    s_out = ~(s_in1 | s_in2)
    n['sema_prompts_inside_published_rounds'] = int((s_in1 | s_in2).sum())
    n['sema_prompts_outside_published_rounds'] = int(s_out.sum())
    n['sema_prompts_outside_published_rounds_pct'] = round(100 * s_out.mean(), 1)
    n['sema_participants_with_any_prompt_outside_published_rounds'] = int(sc.loc[s_out, 'id'].nunique())
    n['sema_prompts_before_round1'] = int((sc['sched_date'] < R1[0]).sum())
    n['sema_prompts_between_rounds'] = int(((sc['sched_date'] > R1[1]) & (sc['sched_date'] < R2[0])).sum())
    n['sema_prompts_after_round2'] = int((sc['sched_date'] > R2[1]).sum())
    n['sema_earliest_prompt_date'] = str(sc['sched_date'].min().date())
    # SEMA aggregated to unique participant-DATES: the only unit directly
    # comparable to the Fitbit participant-day figures. The prompt-level counts
    # above weight each day by how many prompts it carried.
    spd = sc[['id', 'sched_date']].drop_duplicates()
    spd_out = ~(((spd['sched_date'] >= R1[0]) & (spd['sched_date'] <= R1[1])) |
                ((spd['sched_date'] >= R2[0]) & (spd['sched_date'] <= R2[1])))
    n['sema_participant_days_total'] = int(len(spd))
    n['sema_participant_days_outside_published_rounds'] = int(spd_out.sum())
    n['sema_participant_days_outside_published_rounds_pct'] = round(100 * spd_out.mean(), 1)

    # ---- cohorts
    n['provenance_cohort_n_participants'] = int(daily['id'].nunique())
    n['sema_anchored_cohort_n_participants'] = int(len(ex))
    co = ex[ex.exposure >= H]
    n['observation_horizon_H_days'] = H
    n['fixed_horizon_cohort_n_participants'] = int(len(co))
    n['excluded_no_sema_anchor_n_participants'] = int(daily['id'].nunique() - len(ex))
    n['excluded_exposure_below_H_n_participants'] = int(len(ex) - len(co))
    # cohort identity, not just size: sorted membership, hashed for comparison
    n['fixed_horizon_cohort_ids_sorted'] = sorted(co.index.tolist())
    n['sema_anchored_cohort_ids_sorted'] = sorted(ex.index.tolist())

    # H is FROZEN at 49. Re-executing the mechanical selection rule under the
    # corrected calendar convention is reported, not applied.
    need = int(np.ceil(RETENTION * len(ex)))
    feasible = [h for h in range(1, int(ex.exposure.max()) + 1) if int((ex.exposure >= h).sum()) >= need]
    n['H_rule_reexecuted_under_corrected_calendar'] = max(feasible)
    n['H_rule_min_participants_required'] = need
    n['H_frozen_value_retained'] = H

    # ---- provenance: how much of the export lies outside the published rounds
    inr1 = (daily['date'] >= R1[0]) & (daily['date'] <= R1[1])
    inr2 = (daily['date'] >= R2[0]) & (daily['date'] <= R2[1])
    outside = int((~(inr1 | inr2)).sum())
    n['fitbit_participant_days_total'] = int(len(daily))
    n['fitbit_participant_days_outside_published_rounds'] = outside
    n['fitbit_participant_days_outside_published_rounds_pct'] = round(100*outside/len(daily), 1)
    n['fitbit_participants_with_any_day_outside_published_rounds'] = int(
        daily.loc[~(inr1 | inr2), 'id'].nunique())

    # ---- provenance: cross-round IDs under each clock
    fb = daily.groupby('id')['date'].agg(first='min', last='max')
    n['cross_round_ids_under_fitbit_clock'] = int(((fb['first'] <= R1[1]) & (fb['last'] >= R2[0])).sum())
    n['cross_round_ids_under_sema_clock'] = int(((ex['first'] <= R1[1]) & (ex['last'] >= R2[0])).sum())
    n['published_repeat_participants'] = 1

    # ---- surveys
    sv = minibson.read(surv_path)
    v = pd.DataFrame([{'id': d['user_id'], 'submit': d.get('data', {}).get('submitdate')} for d in sv])
    v['dt'] = pd.to_datetime(v['submit'], format='%d/%m/%Y %H:%M', errors='coerce')
    unparsed = int((v['dt'].isna() & v['submit'].notna()).sum())
    n['survey_records_total'] = int(len(v))
    n['survey_records_submitdate_unparsed'] = unparsed
    n['survey_participants_n'] = int(v['id'].nunique())
    sent = v['dt'].notna() & (v['dt'] < pd.Timestamp('1990-01-01'))
    n['survey_records_with_pre1990_sentinel'] = int(sent.sum())
    n['survey_participants_with_at_least_one_pre1990_sentinel_record'] = int(v.loc[sent, 'id'].nunique())
    n['survey_sentinel_distinct_values'] = sorted(v.loc[sent, 'dt'].dt.strftime('%Y-%m-%d').unique().tolist())

    # ---- EXPLICIT expected-day grid: built first, observations joined onto it
    grid = pd.MultiIndex.from_product([co.index, range(H)], names=['id', 'sema_day']).to_frame(index=False)
    obs = daily.merge(co[['first']], left_on='id', right_index=True, how='inner')
    obs['sema_day'] = (obs['date'] - obs['first']).dt.days      # date minus date
    obs = obs[(obs.sema_day >= 0) & (obs.sema_day < H)][['id', 'sema_day', 'loose', 'primary']]
    if obs.duplicated(['id', 'sema_day']).any():
        raise SystemExit('observations are not unique on (id, sema_day)')
    g = grid.merge(obs, on=['id', 'sema_day'], how='left',
                   indicator='_merge', validate='one_to_one')
    if (g['_merge'] == 'right_only').any():
        raise SystemExit('an observation fell outside the expected-day grid')
    g['source_row_present'] = (g['_merge'] == 'both')
    g = g.drop(columns='_merge')
    # `== True` maps NaN to False directly; .fillna(False) on an object column
    # raises a pandas downcasting FutureWarning and will change behaviour.
    for _c in ('loose', 'primary'):
        g[_c] = (g[_c] == True)   # noqa: E712
    if (g.loc[~g['source_row_present'], ['loose', 'primary']].any(axis=None)):
        raise SystemExit('an absent day was scored valid')
    E = len(g); P = int(g['source_row_present'].sum())
    n['expected_participant_days_in_grid'] = E
    n['observed_participant_days_in_grid'] = P
    n['absent_participant_days_in_grid'] = E - P

    # ---- day-level yield under BOTH denominators, each named for its divisor
    for c in ('loose', 'primary'):
        valid = int(g[c].sum())
        n[f'valid_days_{c}_n'] = valid
        n[f'expected_day_yield_{c}_pct_of_{E}_expected_days'] = round(100 * valid / E, 2)
        n[f'observed_row_validity_{c}_pct_of_{P}_observed_rows'] = round(100 * valid / P, 2)

    # ---- participant-level attainment within H
    g.sort_values(['id', 'sema_day']).to_csv(out_dir / 'grid_H49.csv', index=False,
                                              lineterminator='\n')
    ex.sort_index().to_csv(out_dir / 'exposure_windows.csv', lineterminator='\n')
    u = g.groupby('id')[['loose', 'primary']].sum().reindex(co.index)
    u.sort_index().to_csv(out_dir / 'usable_days_H49.csv', lineterminator='\n')
    N = len(u)
    for c in ('loose', 'primary'):
        hit = int((u[c] >= K_PRIMARY).sum())
        n[f'reaching_K{K_PRIMARY}_{c}_n_of_{N}'] = hit
        n[f'reaching_K{K_PRIMARY}_{c}_pct_of_{N}_participants'] = round(100 * hit / N, 1)
        n[f'enroll_for_{TARGET}_at_K{K_PRIMARY}_{c}'] = int(np.ceil(TARGET / (hit / N)))
    curve = {}
    for K in range(7, H + 1):
        cnt = {c: int((u[c] >= K).sum()) for c in ('loose', 'primary')}
        e = {f'{c}_n': cnt[c] for c in ('loose', 'primary')}
        e.update({c: round(100 * cnt[c] / N, 1) for c in ('loose', 'primary')})
        # ratio computed from COUNTS, never from the rounded percentages
        e['ratio'] = round(cnt['primary'] / cnt['loose'], 4) if cnt['loose'] > 0 else None
        curve[str(K)] = e
    n['usable_day_curve_K7_to_K49'] = curve
    # monotonicity of the RATIO is an empirical question, not an assumption
    ratios = [curve[str(K)]['ratio'] for K in range(7, H + 1) if curve[str(K)]['ratio'] is not None]
    rises = [K for K, a, b in zip(range(7, H + 1), ratios, ratios[1:]) if b > a + 1e-12]
    n['ratio_curve_is_monotone_nonincreasing'] = not rises
    n['ratio_curve_K_values_where_ratio_rises'] = rises

    # ---- observed point estimates, computed from counts. These are NOT the
    # bootstrap medians and are reported separately from them.
    hitL = int((u['loose'] >= K_PRIMARY).sum()); hitP = int((u['primary'] >= K_PRIMARY).sum())
    eL = int(np.ceil(TARGET / (hitL / N))); eP = int(np.ceil(TARGET / (hitP / N)))
    n['observed_yield_ratio_primary_over_loose'] = round(hitP / hitL, 4)
    n['observed_enrollment_multiplier_primary_over_loose'] = round(eP / eL, 4)

    # ---- paired participant bootstrap (re-executed, never transcribed)
    rng = np.random.default_rng(SEED)
    ids = u.index.values; yld = []; mult = []
    for _ in range(B):
        smp = rng.choice(ids, size=N, replace=True)
        a = (u.loc[smp, 'primary'] >= K_PRIMARY).mean()
        b = (u.loc[smp, 'loose'] >= K_PRIMARY).mean()
        if a > 0 and b > 0:
            yld.append(a / b); mult.append(np.ceil(TARGET / a) / np.ceil(TARGET / b))
    yld = np.array(yld); mult = np.array(mult)
    n['bootstrap'] = {
        'seed': SEED, 'replicates_requested': B, 'replicates_used': int(len(yld)),
        'yield_ratio_primary_over_loose_median': float(np.median(yld)),
        'yield_ratio_ci_lo_unrounded': float(np.percentile(yld, 2.5)),
        'yield_ratio_ci_hi_unrounded': float(np.percentile(yld, 97.5)),
        'enrollment_multiplier_primary_over_loose_median': float(np.median(mult)),
        'enrollment_multiplier_ci_lo_unrounded': float(np.percentile(mult, 2.5)),
        'enrollment_multiplier_ci_hi_unrounded': float(np.percentile(mult, 97.5)),
        'share_replicates_yield_ratio_ge_1': float(np.mean(yld >= 1.0)),
        'share_replicates_yield_ratio_gt_1': float(np.mean(yld > 1.0)),
        'note': ('primary is a subset of loose, so the yield ratio is bounded above '
                 'by 1.0 by construction. The pre-specified test asks whether the interval '
                 'includes a parameter-space boundary, not an interior null. Recorded as a '
                 'defect of the specification; the verdict is unchanged.')}
    n['null_condition_2_fired'] = bool(
        n['bootstrap']['yield_ratio_ci_lo_unrounded'] <= 1.0 <= n['bootstrap']['yield_ratio_ci_hi_unrounded'])
    n['headline_criterion_met'] = not n['null_condition_2_fired']

    # explicit newline='\n': the default translates to CRLF on Windows, which
    # made the byte-identical rebuild claim platform-specific. Found when the
    # suite was first run on Windows, 2026-09-14.
    with open(out_dir / 'numbers.json', 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(n, indent=2, sort_keys=True) + '\n')
    return n


def main():
    p = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    p.add_argument('--data-dir', type=Path, default=here / 'data')
    # default alongside the Fitbit CSVs, so that after following VERIFY.md a bare
    # `python3 build_numbers.py` works. An absolute path elsewhere still works.
    p.add_argument('--sema-dir', type=Path, default=here / 'data')
    p.add_argument('--out-dir', type=Path, default=here)
    p.add_argument('--src-dir', type=Path, default=here / 'src')
    a = p.parse_args()
    n = build(a.data_dir, a.sema_dir, a.out_dir, a.src_dir)
    skip = {'usable_day_curve_K7_to_K49', 'fixed_horizon_cohort_ids_sorted',
            'sema_anchored_cohort_ids_sorted'}
    print(json.dumps({k: v for k, v in n.items() if k not in skip}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
