"""Figures for the MUNI-LCC preprint, drawn in a Power BI report style.

Plain-language header: draws every chart in the preprint from the toolkit's
own outputs (examples/outputs) and from the validation files. Each chart is a
"visual card" as in a Power BI report page: white card, thin border, bold title
at top left, legend under the title, light horizontal gridlines, no chart
borders, and Power BI default theme colors (blue #118DFF, orange #E66C37,
purple #744EC2), which pass the colorblind and contrast checks. Inter is used
as a stand-in for Segoe UI. Synthetic data only.

    python preprint/analysis/figures.py --repo . --data preprint/analysis/out --out preprint/figs
"""

from __future__ import annotations

import argparse
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from muni_lcc import mv_option_c as C  # noqa: E402

# Power BI report palette
BLUE, ORANGE, PURPLE = "#118DFF", "#E66C37", "#744EC2"
TITLE, TEXT, MUTED = "#252423", "#605E5C", "#8A8886"
GRID, BORDER, CARD = "#EDEBE9", "#D2D0CE", "#FFFFFF"

plt.rcParams.update({
    "font.family": "Inter", "font.size": 7, "text.color": TEXT,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT, "axes.labelsize": 7,
    "xtick.color": TEXT, "ytick.color": TEXT, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.7,
    "grid.linestyle": (0, (2, 2)), "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.frameon": False, "savefig.dpi": 300, "pdf.fonttype": 3,
})
W1, W2 = 3.35, 7.0


def card(fig, title, subtitle=None):
    """Draw the Power BI visual card: border, title, optional subtitle."""
    fig.patch.set_facecolor(CARD)
    fig.patches.append(FancyBboxPatch((0.004, 0.006), 0.992, 0.988, transform=fig.transFigure,
                                      boxstyle="round,pad=0,rounding_size=0.012", fill=False,
                                      edgecolor=BORDER, linewidth=0.8, zorder=-10))
    fig.text(0.025, 0.955, title, fontsize=8.5, fontweight="semibold", color=TITLE, va="top")
    if subtitle:
        fig.text(0.025, 0.885, subtitle, fontsize=6.3, color=MUTED, va="top")


def legend_top(fig, handles, labels, y=0.83, x=0.025):
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(x, y), ncol=len(labels),
               fontsize=6.3, handlelength=1.0, handletextpad=0.4, columnspacing=1.2,
               labelcolor=TEXT, borderaxespad=0)


def dot(color, marker="o"):
    return plt.Line2D([], [], marker=marker, color=color, lw=0, ms=5)


def comma(ax, axis="y"):
    f = mt.FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(f)


def fig_baseline(repo, out):
    base = C.read_periods(os.path.join(repo, "examples/data/gas_baseline.csv"))
    rep = C.read_periods(os.path.join(repo, "examples/data/gas_reporting.csv"))
    m = C.fit_baseline(base)["model"]
    two_p = C.fit_form("2P", base)
    T = np.linspace(15, 78, 300)
    fig = plt.figure(figsize=(W1, 2.75))
    card(fig, "Daily gas use by billing-period temperature", "Synthetic town hall, 24 baseline and 12 reporting months")
    ax = fig.add_axes([0.13, 0.15, 0.83, 0.56])
    ax.plot(T, two_p.predict_rate(T), color=MUTED, lw=1, ls=(0, (4, 2)))
    ax.plot(T, m.predict_rate(T), color=BLUE, lw=2)
    ax.scatter([p.mean_temp for p in base], [p.rate for p in base], s=16, color=BLUE,
               edgecolor="white", linewidth=0.7, zorder=3)
    ax.scatter([p.mean_temp for p in rep], [p.rate for p in rep], s=16, color=ORANGE,
               edgecolor="white", linewidth=0.7, zorder=3)
    cp = m.change_points[0]
    ax.axvline(cp, color=BORDER, lw=0.8, zorder=0)
    ax.text(cp + 1, 285, f"Change point {cp:.0f} F", fontsize=6, color=TEXT)
    ax.set_xlabel("Mean outdoor temperature (F)")
    ax.set_ylabel("Therms per day")
    ax.set_ylim(0, 320)
    legend_top(fig, [dot(BLUE), dot(ORANGE), plt.Line2D([], [], color=BLUE, lw=2),
                     plt.Line2D([], [], color=MUTED, lw=1, ls=(0, (4, 2)))],
               ["Baseline", "Reporting", f"{m.form} model", "2P model"])
    fig.savefig(os.path.join(out, "fig_baseline.pdf"))
    plt.close(fig)


def fig_monthly(repo, out):
    with open(os.path.join(repo, "examples/outputs/results.json"), encoding="utf-8") as f:
        c = json.load(f)["option_c"]
    rows = c["by_period"]
    x = np.arange(len(rows))
    base = np.array([r["adjusted_baseline"] for r in rows])
    act = np.array([r["actual"] for r in rows])
    fig = plt.figure(figsize=(W1, 2.75))
    card(fig, "Adjusted baseline and metered gas use by month",
         f"Reporting year 2025 (synthetic). Avoided use {c['avoided_energy']:,.0f} therms")
    ax = fig.add_axes([0.14, 0.13, 0.83, 0.58])
    w = 0.38
    ax.bar(x - w / 2 - 0.01, base, w, color=BLUE, zorder=2)
    ax.bar(x + w / 2 + 0.01, act, w, color=ORANGE, zorder=2)
    ax.set_xticks(x, ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.tick_params(axis="x", labelsize=5.8)
    ax.set_ylabel("Therms per month")
    comma(ax)
    ax.set_ylim(0, 9000)
    i = int(np.argmax(base - act))
    ax.annotate(f"{base[i] - act[i]:,.0f} saved", (x[i], base[i]), xytext=(-2, 4),
                textcoords="offset points", ha="right", fontsize=6, color=TEXT)
    legend_top(fig, [dot(BLUE, "s"), dot(ORANGE, "s")], ["Adjusted baseline (model)", "Metered"])
    fig.savefig(os.path.join(out, "fig_monthly.pdf"))
    plt.close(fig)


def fig_lcc(data, out):
    rows = list(csv.DictReader(open(os.path.join(data, "lcc_scans.csv"), encoding="utf-8")))
    with open(os.path.join(data, "lcc_stats.json"), encoding="utf-8") as f:
        z = json.load(f)
    ref_ns = z["reference"]["net_savings"] / 1000
    panels = [("rate", "Real discount rate (%)", 100, 3.0, "{:.0f}%"),
              ("gas_price", "Natural gas price ($ per therm)", 1, 1.20, "${:.2f}"),
              ("years", "Study period (years)", 1, 25, "{:.0f} y")]
    fig = plt.figure(figsize=(W2, 2.45))
    card(fig, "Net savings sensitivity, worked example",
         "Present value in thousand dollars. One input varied at a time; marker shows the reference case")
    lefts = [0.065, 0.385, 0.705]
    for j, ((scan, label, k, ref, fmt), left) in enumerate(zip(panels, lefts)):
        ax = fig.add_axes([left, 0.17, 0.27, 0.56])
        r = [q for q in rows if q["scan"] == scan]
        xs = np.array([float(q["x"]) * k for q in r])
        ys = np.array([float(q["net_savings"]) / 1000 for q in r])
        ax.plot(xs, ys, color=BLUE, lw=2)
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.scatter([ref], [ref_ns], s=26, color=ORANGE, edgecolor="white", linewidth=0.8, zorder=4)
        ax.annotate(f"{ref_ns:,.0f}", (ref, ref_ns), xytext=(-6, -12) if j == 0 else (-6, 7), textcoords="offset points",
                    ha="right", fontsize=6.3, color=TITLE, fontweight="semibold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
        ax.set_xlabel(label)
        ax.set_ylim(-30, 320)
        ax.text(0.0, 1.04, "abc"[j].join("()") + "  " + ["Discount rate", "Gas price", "Study period"][j],
                transform=ax.transAxes, fontsize=6.8, color=TITLE, fontweight="semibold")
        if j == 0:
            ax.set_ylabel("Net savings ($ thousand)")
            be = z["breakeven_rate"] * 100
            ax.axvline(be, color=PURPLE, lw=1, ls=(0, (2, 2)))
            ax.text(be - 0.2, 150, f"Break-even\n{be:.1f}%", ha="right", fontsize=6, color=PURPLE)
    fig.savefig(os.path.join(out, "fig_lcc.pdf"))
    plt.close(fig)


def fig_mc(data, out):
    rows = list(csv.DictReader(open(os.path.join(data, "mc_reference.csv"), encoding="utf-8")))
    err = np.array([float(r["est"]) - float(r["true"]) for r in rows])
    unc = np.array([float(r["unc90"]) for r in rows])
    with open(os.path.join(data, "validation_stats.json"), encoding="utf-8") as f:
        V = json.load(f)
    fig = plt.figure(figsize=(W2, 2.55))
    card(fig, "Monte Carlo evaluation of the Option C uncertainty",
         f"{len(rows):,} replications of the reference process for (a); 500 per baseline length in (b)")
    ax = fig.add_axes([0.065, 0.16, 0.43, 0.56])
    bins = np.arange(-6000, 6001, 500)
    ax.hist(np.clip(err, -6000, 6000), bins=bins, color=BLUE, rwidth=0.88, zorder=2)
    u = float(np.median(unc))
    for s in (-u, u):
        ax.axvline(s, color=ORANGE, lw=1.2, ls=(0, (3, 2)))
    ax.text(u + 150, ax.get_ylim()[1] * 0.88, f"Median 90% band\n±{u:,.0f}", fontsize=6, color=ORANGE)
    ax.set_xlabel("Estimated minus true avoided use (therms)")
    ax.set_ylabel("Replications")
    comma(ax, "x")
    ax.text(0.0, 1.04, "(a)  Estimation error", transform=ax.transAxes, fontsize=6.8,
            color=TITLE, fontweight="semibold")

    ax = fig.add_axes([0.6, 0.16, 0.37, 0.56])
    nominal = [80, 90, 95]
    ax.plot(nominal, nominal, color=MUTED, lw=1, ls=(0, (4, 2)), zorder=1)
    cases = [("years_1", "12-month", ORANGE), ("reference", "24-month", BLUE), ("years_3", "36-month", PURPLE)]
    for key, lab, col in cases:
        ys = [V[key][f"coverage{c}_pct"] for c in nominal]
        ax.plot(nominal, ys, color=col, lw=2, marker="o", ms=4.5, markeredgecolor="white",
                markeredgewidth=0.7, zorder=3)
        ax.annotate(f"{ys[1]:.1f}%", (90, ys[1]), xytext=(-6, 6) if key != "years_1" else (6, -10),
                    textcoords="offset points", ha="right" if key != "years_1" else "left",
                    fontsize=6, color=col, fontweight="semibold",
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"), zorder=5)
    ax.set_xticks(nominal, [f"{c}%" for c in nominal])
    ax.yaxis.set_major_formatter(mt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlim(78, 97)
    ax.set_ylim(60, 100)
    ax.set_xlabel("Nominal confidence level")
    ax.set_ylabel("Empirical coverage")
    ax.text(0.0, 1.04, "(b)  Coverage by baseline length", transform=ax.transAxes, fontsize=6.8,
            color=TITLE, fontweight="semibold")
    ax.legend([dot(ORANGE), dot(BLUE), dot(PURPLE), plt.Line2D([], [], color=MUTED, lw=1, ls=(0, (4, 2)))],
              ["12-month baseline", "24-month baseline", "36-month baseline", "Nominal"], loc="lower right",
              fontsize=6.1, handlelength=1.0, handletextpad=0.4, labelcolor=TEXT,
              facecolor="white", framealpha=1, frameon=True, edgecolor="white")
    fig.savefig(os.path.join(out, "fig_mc.pdf"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fig_baseline(a.repo, a.out)
    fig_monthly(a.repo, a.out)
    fig_lcc(a.data, a.out)
    if os.path.exists(os.path.join(a.data, "validation_stats.json")):
        fig_mc(a.data, a.out)


if __name__ == "__main__":
    main()
