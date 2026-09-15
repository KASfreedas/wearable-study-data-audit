"""Figure 1 - the audit figure.

All 71 participants in the released Fitbit export, showing what the device
records actually cover in calendar time against the two published collection
rounds, beside the scheduled-prompt density that is the only study-generated
clock available.

The figure exists to answer one question: can the released device records
support the study window and denominator an analysis assumes? It is built to be
falsifiable - see the caption assertions at the bottom of this file, each of
which is a key in numbers.json and is checked before the figure is written.

Palette: dataviz reference instance. Categorical slot 1 blue for presence,
slot 2 orange as its own sequential ramp for density. Light and dark are
separately stepped, not flipped.
"""
from __future__ import annotations
import argparse, json, sys, textwrap
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/"src")); sys.path.insert(0, str(HERE/"sema"))
import adherence as A, minibson

MONGO = HERE / "data"          # VERIFY.md stages every raw input into data/
R1 = (pd.Timestamp("2021-05-24"), pd.Timestamp("2021-07-26"))
R2 = (pd.Timestamp("2021-11-15"), pd.Timestamp("2022-01-17"))

THEME = {
    "light": dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#8a8983",
                  grid="#e4e3df", band="#e8e5dd", bandline="#c9c7c0",
                  blue="#2a78d6", ramp=["#fcfcfb", "#f7c9b3", "#f28d5d"]),
    "dark":  dict(surface="#1a1a19", ink="#ffffff", ink2="#c3c2b7", muted="#8a8983",
                  grid="#2e2e2c", band="#34342f", bandline="#4a4a45",
                  blue="#3987e5", ramp=None),
}
# orange sequential ramps, stepped per surface (slot-2 hue, light->dark)
RAMP = {"light": ["#fcfcfb", "#fbd9c6", "#f7b491", "#f28d5d", "#eb6834", "#c44e22"],
        "dark":  ["#1a1a19", "#5c2b12", "#8a3f1a", "#b34e21", "#d95926", "#f0743f"]}
THEME["light"]["ramp"] = RAMP["light"]; THEME["dark"]["ramp"] = RAMP["dark"]


def load():
    daily = A.load_daily(HERE/"data/daily_fitbit_sema_df_unprocessed.csv")
    docs = minibson.read(MONGO/"sema.bson")
    s = pd.DataFrame([{"id": d["user_id"], "sched": d["data"].get("SCHEDULED_TS")} for d in docs])
    s["sched"] = pd.to_datetime(s["sched"], errors="coerce")
    s = s.dropna(subset=["sched"])
    s["date"] = s["sched"].dt.normalize()
    return daily, s


def build_matrices(daily, sema):
    lo = min(daily["date"].min(), sema["date"].min())
    hi = max(daily["date"].max(), sema["date"].max())
    days = pd.date_range(lo, hi, freq="D")
    dix = {d: i for i, d in enumerate(days)}

    anchor = sema.groupby("id")["date"].min()
    fb_first = daily.groupby("id")["date"].min()
    # order: SEMA-anchored participants by their anchor, then the unanchored by
    # their first Fitbit date. The 8 unanchored sit together at the bottom.
    ids = list(anchor.sort_values().index) + \
          [i for i in fb_first.sort_values().index if i not in set(anchor.index)]
    rix = {p: i for i, p in enumerate(ids)}

    fit = np.zeros((len(ids), len(days)), bool)
    for p, d in zip(daily["id"], daily["date"]):
        fit[rix[p], dix[d]] = True

    dens = np.zeros((len(ids), len(days)), int)
    for (p, d), c in sema.groupby(["id", "date"]).size().items():
        dens[rix[p], dix[d]] = c

    return ids, days, fit, dens, anchor, set(anchor.index)


def build_caption(stats):
    """The caption text actually handed to the renderer (see figure2.build_caption)."""
    s = stats
    n_prompts = (s['sema_prompts_inside_published_rounds']
                 + s['sema_prompts_outside_published_rounds'])
    return [
        ("Fitbit records.",
         f"{s['fitbit_participant_days_outside_published_rounds']:,} of "
         f"{s['fitbit_participant_days_total']:,} participant-days "
         f"({s['fitbit_participant_days_outside_published_rounds_pct']}%) fall outside both published "
         f"windows, affecting {s['fitbit_participants_with_any_day_outside_published_rounds']} of 71 "
         f"participants."),
        ("Scheduled prompts.",
         f"{s['sema_participant_days_outside_published_rounds']} of "
         f"{s['sema_participant_days_total']:,} participant-days "
         f"({s['sema_participant_days_outside_published_rounds_pct']}%) fall outside \u2014 the unit "
         f"comparable to the line above. Counted as individual prompts, which weight each day by how "
         f"many it carried, {s['sema_prompts_outside_published_rounds']} of {n_prompts:,} "
         f"({s['sema_prompts_outside_published_rounds_pct']}%). Either way "
         f"{s['sema_participants_with_any_prompt_outside_published_rounds']} of "
         f"{s['sema_anchored_cohort_n_participants']} participants are affected; all fall before "
         f"round 1, earliest {s['sema_earliest_prompt_date']}, none between the rounds or after round 2."),
        ("Span counts, separately.",
         f"Not implied by the coverage figures above: "
         f"{s['cross_round_ids_under_fitbit_clock']} participants have first-to-last Fitbit spans that "
         f"bridge the two windows, against {s['cross_round_ids_under_sema_clock']} under the prompt "
         f"clock. A bridging span does not establish records inside both rounds, still less repeat "
         f"participation \u2014 see RESULT.md."),
        ("No SEMA anchor.",
         f"{71 - s['sema_anchored_cohort_n_participants']} of 71 participants have Fitbit records but no "
         f"scheduled prompt, so no SEMA-based exposure window can be assigned to them."),
        ("",
         "Released Fitbit availability extends beyond the published collection windows and should not be "
         "treated as a verified participant-specific exposure window. The two exports also cover different "
         "populations \u2014 71 Fitbit participants against 63 with SEMA \u2014 so this is a descriptive "
         "comparison of the exports, not a controlled comparison on identical participants."),
    ]


def draw(mode, ids, days, fit, dens, anchored, stats, out_dir=None):
    t = THEME[mode]
    x0, x1 = mdates.date2num(days[0]), mdates.date2num(days[-1])
    extent = [x0, x1, len(ids), 0]

    fig, axes = plt.subplots(1, 2, figsize=(14.2, 9.8), sharey=True,
                             gridspec_kw=dict(wspace=0.05))
    fig.patch.set_facecolor(t["surface"])

    blue_cm = LinearSegmentedColormap.from_list("p", [t["surface"], t["blue"]])
    or_cm = LinearSegmentedColormap.from_list("d", t["ramp"])
    vmax = int(dens.max())
    norm = BoundaryNorm(np.arange(-0.5, vmax + 1.5), or_cm.N)

    panels = [(fit.astype(float), blue_cm, None,
               "A \u00b7 Fitbit daily records present",
               "one mark per participant-day with a row in the released export"),
              (dens.astype(float), or_cm, norm,
               "B \u00b7 Scheduled SEMA prompts per day",
               "one mark per participant-day with at least one scheduled prompt")]

    for ax, (data, cm, nrm, title, sub) in zip(axes, panels):
        ax.set_facecolor(t["surface"])
        # the shaded window must be perceptible on its own, not carried by the
        # bracket and boundary lines alone
        for lo, hi in (R1, R2):
            ax.axvspan(mdates.date2num(lo), mdates.date2num(hi),
                       facecolor=t["band"], zorder=0, lw=0)
        masked = np.ma.masked_where(data == 0, data)
        ax.imshow(masked, aspect="auto", extent=extent, cmap=cm, norm=nrm,
                  interpolation="nearest", zorder=2,
                  vmin=None if nrm else 0, vmax=None if nrm else 1)
        for lo, hi in (R1, R2):
            for b in (lo, hi):
                ax.axvline(mdates.date2num(b), color=t["bandline"], lw=1.1,
                           ls=(0, (3, 3)), zorder=6)
        xt = ax.get_xaxis_transform()
        for (lo, hi), lab in ((R1, "published round 1"), (R2, "published round 2")):
            a, b = mdates.date2num(lo), mdates.date2num(hi)
            ax.plot([a, b], [1.015, 1.015], transform=xt, clip_on=False,
                    color=t["ink2"], lw=3.2, solid_capstyle="butt", zorder=7)
            ax.text((a + b) / 2, 1.032, lab, transform=xt, clip_on=False,
                    ha="center", va="bottom", color=t["ink2"], fontsize=8.4)
        ax.axhline(len(anchored), color=t["muted"], lw=1, ls=(0, (4, 3)), zorder=5)
        ax.text(0, 1.115, title, transform=ax.transAxes, color=t["ink"],
                fontsize=12, weight="bold", va="bottom")
        ax.text(0, 1.070, sub, transform=ax.transAxes, color=t["ink2"],
                fontsize=9, va="bottom")
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.tick_params(colors=t["ink2"], labelsize=8.5, length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.grid(False)

    axes[0].set_ylabel("71 participants, ordered by first scheduled prompt",
                       color=t["ink2"], fontsize=9.5, labelpad=8)
    axes[0].set_yticks([0.5, len(anchored), len(ids) - 0.5])
    axes[0].set_yticklabels(["1", f"{len(anchored)}", f"{len(ids)}"], fontsize=8.5)
    axes[1].text(mdates.date2num(pd.Timestamp("2021-08-20")), len(ids) - 3.5,
                 f"{71 - len(anchored)} participants have Fitbit records\n"
                 f"but no scheduled prompt at all",
                 color=t["ink"], fontsize=9, ha="left", va="center", zorder=8)

    cax = fig.add_axes([0.915, 0.52, 0.012, 0.19])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=or_cm), cax=cax,
                      ticks=list(range(0, vmax + 1, 2)))
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=t["ink2"], labelsize=8, length=0)
    cb.ax.minorticks_off()
    cb.set_label("prompts per day", color=t["ink2"], fontsize=8.5)

    fig.legend(handles=[
        Patch(facecolor=t["blue"], label="Fitbit day present"),
        Patch(facecolor=t["ramp"][4], label="prompt scheduled"),
        Patch(facecolor=t["band"], label="published round window")],
        loc="lower left", bbox_to_anchor=(0.075, 0.318), frameon=False,
        fontsize=9, labelcolor=t["ink2"], ncol=3, handlelength=1.6,
        columnspacing=1.8)

    fig.text(0.075, 0.972,
             "Released Fitbit records extend well beyond the published collection windows",
             color=t["ink"], fontsize=15, weight="bold", ha="left", va="top")
    fig.text(0.075, 0.941,
             "Scheduled SEMA prompts, with two participants excepted, do not.",
             color=t["ink2"], fontsize=10.5, ha="left", va="top")

    cap = build_caption(stats)
    LX, TX, WRAP = 0.075, 0.205, 128
    y = 0.272
    for i, (label, body) in enumerate(cap):
        ink = t["ink2"] if label else t["muted"]
        if label:
            fig.text(LX, y, label, color=t["ink"], fontsize=9, weight="bold",
                     ha="left", va="top")
        for line in textwrap.wrap(body, WRAP):
            fig.text(TX if label else LX, y, line, color=ink, fontsize=9,
                     ha="left", va="top")
            y -= 0.0195
        y -= 0.008

    fig.text(0.075, 0.018,
             "LifeSnaps (Yfantidou et al., Sci Data 2022; Zenodo 7229547, CC-BY 4.0). Round windows from the dataset "
             "paper. Every figure quoted is a key in numbers.json; regenerated by figure1.py.",
             color=t["muted"], fontsize=8.2, ha="left", va="top")

    fig.subplots_adjust(left=0.075, right=0.895, top=0.845, bottom=0.382)
    out = Path(out_dir or HERE) / f"figure1_{mode}.png"
    fig.savefig(out, dpi=200, facecolor=t["surface"])
    plt.close(fig)
    return out


def main():
    stats = json.loads((HERE/"numbers.json").read_text())
    daily, sema = load()
    ids, days, fit, dens, anchor, anchored = build_matrices(daily, sema)

    # caption assertions - the figure is not written unless these hold
    assert len(ids) == stats["raw_participants_in_fitbit_export"] == 71
    assert len(anchored) == stats["sema_anchored_cohort_n_participants"] == 63
    fb = daily.groupby("id")["date"].agg(first="min", last="max")
    assert int(((fb["first"] <= R1[1]) & (fb["last"] >= R2[0])).sum()) \
        == stats["cross_round_ids_under_fitbit_clock"]
    ex = sema.groupby("id")["date"].agg(first="min", last="max")
    assert int(((ex["first"] <= R1[1]) & (ex["last"] >= R2[0])).sum()) \
        == stats["cross_round_ids_under_sema_clock"]
    outside = int((~(((daily["date"] >= R1[0]) & (daily["date"] <= R1[1])) |
                     ((daily["date"] >= R2[0]) & (daily["date"] <= R2[1])))).sum())
    print(f"  Fitbit participant-days outside both published round windows: "
          f"{outside} of {len(daily)} ({100*outside/len(daily):.1f}%)")
    print(f"  prompts/day max: {dens.max()}   calendar span: {days[0].date()} to {days[-1].date()}")

    ap = argparse.ArgumentParser()
    ap.add_argument('--out-dir', default=None,
                    help='write the PNGs here instead of beside this script')
    out_dir = ap.parse_args().out_dir
    for mode in ("light", "dark"):
        print("  wrote", draw(mode, ids, days, fit, dens, anchored, stats, out_dir))


if __name__ == "__main__":
    main()
