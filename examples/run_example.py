"""Run the synthetic worked example, compare with the known truth, write stats and figure.

    python examples/make_example_data.py     # regenerate data (seed 2026)
    python examples/run_example.py           # outputs with draft markings
    python examples/run_example.py --final   # after the author's verification

Writes examples/outputs/: results.json, performance_report.md and .json,
stats.json (every number quoted in the docs), and fig_option_c.png.
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from muni_lcc import pipeline, report as R  # noqa: E402

OUT = os.path.join(HERE, "outputs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)

    res = pipeline.run(os.path.join(HERE, "project.json"), final=args.final)
    rep = res.pop("report")
    with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, default=float)
    with open(os.path.join(OUT, "performance_report.md"), "w", encoding="utf-8") as f:
        f.write(R.to_markdown(rep))
    with open(os.path.join(OUT, "performance_report.json"), "w", encoding="utf-8") as f:
        f.write(R.to_json(rep))

    with open(os.path.join(HERE, "data", "TRUTH.json"), encoding="utf-8") as f:
        truth = json.load(f)
    c, a, z = res["option_c"], res["option_a"][0], res["lcc"]
    s = c["baseline_statistics"]
    stats = {
        "synthetic": True,
        "option_c_model": c["model_form"],
        "option_c_equation": c["model_equation"],
        "option_c_n_baseline": s["n"],
        "option_c_m_reporting": c["reporting_periods"],
        "option_c_cv_rmse_pct": round(s["cv_rmse"] * 100, 1),
        "option_c_nmbe_pct": round(abs(s["nmbe"]) * 100, 2),
        "option_c_r2": round(s["r2"], 3),
        "option_c_min_slope_t": round(s["min_abs_slope_t"], 1),
        "option_c_acceptance_pass": c["acceptance"]["all_pass"],
        "option_c_avoided_therms": round(c["avoided_energy"]),
        "option_c_fraction_pct": round(c["fractional_savings"] * 100, 1),
        "option_c_fsu_pct_90": round(c["fractional_savings_uncertainty"] * 100, 1),
        "option_c_abs_unc_therms": round(c["absolute_uncertainty"]),
        "true_fraction_pct": round(truth["true_savings_fraction_option_c"] * 100, 1),
        "true_avoided_therms": round(truth["true_avoided_therms"]),
        "option_c_error_therms": round(c["avoided_energy"] - truth["true_avoided_therms"]),
        "option_c_within_uncertainty": abs(c["avoided_energy"] - truth["true_avoided_therms"])
                                       <= c["absolute_uncertainty"],
        "option_a_savings_kwh": round(a["savings"]),
        "option_a_rel_unc_pct": round(a["relative_uncertainty"] * 100, 1),
        "true_option_a_kwh": round(truth["true_lighting_savings_kwh"]),
        "lcc_study_years": z["study_period_years"],
        "lcc_rate_pct": round(z["real_discount_rate"] * 100, 1),
        "lcc_net_savings": round(z["net_savings"]),
        "lcc_sir": round(z["sir"], 2),
        "lcc_airr_pct": round(z["airr"] * 100, 1),
        "lcc_spb": round(z["simple_payback_years"], 1),
        "lcc_dpb": round(z["discounted_payback_years"], 1),
        "report_due_date": rep["due_date"],
        "report_issues": len(rep["completeness_issues"]),
    }
    with open(os.path.join(OUT, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    figure(c, final=args.final)
    print(json.dumps(stats, indent=2))


def figure(c, final=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = c["by_period"]
    x = list(range(len(rows)))
    labels = [r["period"][-2:] for r in rows]
    base = [r["adjusted_baseline"] for r in rows]
    act = [r["actual"] for r in rows]
    surface, ink, muted, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    s1, s2 = "#2a78d6", "#eb6834"

    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)
    ax.fill_between(x, act, base, color=s1, alpha=0.12, linewidth=0)
    ax.plot(x, base, color=s1, lw=2, marker="o", ms=4, label="Adjusted baseline (model)")
    ax.plot(x, act, color=s2, lw=2, marker="s", ms=4, label="Reporting period (metered)")
    ax.annotate("Adjusted baseline", (x[-1], base[-1]), xytext=(-8, 0), textcoords="offset points",
                color=muted, fontsize=8, ha="right", va="center")
    ax.annotate("Metered", (x[-1], act[-1]), xytext=(-8, -2), textcoords="offset points",
                color=muted, fontsize=8, ha="right", va="top")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Reporting month", color=muted, fontsize=9)
    ax.set_ylabel("Natural gas (therms per month)", color=muted, fontsize=9)
    ax.tick_params(colors=muted, labelsize=8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_color(grid)
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_ylim(0, None)
    ax.legend(frameon=False, fontsize=8, labelcolor=ink, loc="upper center")
    ax.set_title(f"Avoided energy use, IPMVP Option C: {c['avoided_energy']:,.0f} therms "
                 f"({c['fractional_savings'] * 100:.1f}%)", color=ink, fontsize=10, loc="left")
    fig.text(0.01, 0.01, "Synthetic example data (seed 2026). Shaded area = avoided energy use.",
             color=muted, fontsize=7)
    if not final:
        fig.text(0.98, 0.95, "DRAFT", color="#b0afa9", fontsize=14, ha="right", va="top", weight="bold")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "fig_option_c.png"), facecolor=surface)
    plt.close(fig)


if __name__ == "__main__":
    main()
