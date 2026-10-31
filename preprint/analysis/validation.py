"""Validation and sensitivity analyses for the MUNI-LCC v0.1.0 preprint.

Plain-language header: this script tests MUNI-LCC many times on synthetic
buildings whose true savings are known, and records how often the reported
uncertainty band contains the true answer. It also varies the life-cycle cost
inputs to show how the economic results move. Every number in the preprint's
validation section is read from the files this script writes.

Run from the repository root after `pip install -e .`:

    python preprint/analysis/validation.py --out preprint/analysis/out

The data-generating process is the one in examples/make_example_data.py
(seed 2026, true daily use 40 + 6 * max(58 - T, 0) therms, monthly noise
sd 12 therms/day, temperature jitter sd 2.5 F), with the savings fraction,
noise level, and baseline length made adjustable. Nothing here is real data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics as st
from multiprocessing import Pool

import numpy as np

from muni_lcc import mv_option_a as A
from muni_lcc import mv_option_c as C
from muni_lcc.stats import t_critical

DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
TEMPS = [22, 25, 34, 47, 58, 67, 72, 70, 62, 50, 39, 28]
CRIT = {"min_r2": 0.75, "max_abs_nmbe": 0.00005, "min_abs_slope_t": 2.0,
        "max_cv_rmse": 0.25, "max_fsu": 0.50}
CONFS = (0.80, 0.90, 0.95)


def true_rate(t):
    return 40.0 + 6.0 * max(58.0 - t, 0.0)


def synth(seed, frac=0.15, noise=12.0, base_years=2, temp_sd=2.5):
    rng = np.random.default_rng(seed)

    def block(nyears, scale):
        out, truth = [], 0.0
        for y in range(nyears):
            for i in range(12):
                t = round(TEMPS[i] + rng.normal(0, temp_sd), 1)
                r = true_rate(t)
                out.append(C.Period(f"{y}-{i + 1:02d}", DAYS[i],
                                    round((r * scale + rng.normal(0, noise)) * DAYS[i], 1), t))
                truth += r * DAYS[i]
        return out, truth

    base, _ = block(base_years, 1.0)
    rep, true_adj = block(1, 1.0 - frac)
    return base, rep, true_adj * frac


def one(args):
    seed, frac, noise, years = args
    base, rep, true_sav = synth(seed, frac, noise, years)
    fit = C.fit_baseline(base)
    res = C.avoided_energy(fit["model"], base, rep, 0.90)
    s = res["baseline_statistics"]
    acc = C.check_acceptance(res, CRIT)
    row = {"seed": seed, "frac": frac, "noise": noise, "years": years,
           "form": res["model_form"], "n": s["n"], "p": s["p"],
           "cv": s["cv_rmse"], "r2": s["r2"], "nmbe": s["nmbe"],
           "est": res["avoided_energy"], "true": true_sav, "F_est": res["fractional_savings"],
           "pass": acc["all_pass"],
           **{f"ok_{k}": v for k, v in acc["checks"].items()}}
    fsu90 = res["fractional_savings_uncertainty"]
    u90 = res["absolute_uncertainty"]   # None in v0.1.0 when savings <= 0; always defined in v0.1.1
    t90 = t_critical(0.90, s["n"] - s["p"])
    for c in CONFS:
        row[f"unc{int(c * 100)}"] = (math.nan if u90 is None
                                     else abs(u90) / t90 * t_critical(c, s["n"] - s["p"]))
    row["fsu90"] = fsu90 if fsu90 is not None else math.nan
    return row


def summarize(rows):
    err = [r["est"] - r["true"] for r in rows]
    out = {"reps": len(rows),
           "mean_true": st.mean(r["true"] for r in rows),
           "mean_err": st.mean(err),
           "rmse": math.sqrt(st.mean(e * e for e in err)),
           "mean_rel_err_pct": 100 * st.mean(e / r["true"] for e, r in zip(err, rows)),
           "sd_err": st.pstdev(err),
           "median_fsu90_pct": 100 * float(np.nanmedian([r["fsu90"] for r in rows])),
           "mean_unc90": float(np.nanmean([r["unc90"] for r in rows])),
           "pass_rate_pct": 100 * st.mean(1.0 if r["pass"] else 0.0 for r in rows),
           "median_cv_pct": 100 * st.median(r["cv"] for r in rows),
           "median_r2": st.median(r["r2"] for r in rows),
           "max_abs_nmbe": max(abs(r["nmbe"]) for r in rows)}
    for c in CONFS:
        k = f"unc{int(c * 100)}"
        out[f"coverage{int(c * 100)}_pct"] = 100 * st.mean(
            1.0 if abs(r["est"] - r["true"]) <= r[k] else 0.0 for r in rows)
    for k in ("r2", "nmbe", "slope_t", "cv_rmse", "fsu"):
        out[f"ok_{k}_pct"] = 100 * st.mean(1.0 if r[f"ok_{k}"] else 0.0 for r in rows)
    forms = {}
    for r in rows:
        forms[r["form"]] = forms.get(r["form"], 0) + 1
    out["forms_pct"] = {k: 100 * v / len(rows) for k, v in sorted(forms.items())}
    return out


def option_a_mc(reps=20000, sd=0.20, nread=5, seed=7):
    rng = np.random.default_rng(seed)
    H, true_delta = 3380.0, 14.6 - 6.2
    cov, rel = {c: 0 for c in CONFS}, []
    for _ in range(reps):
        b = list(rng.normal(14.6, sd, nread))
        r = list(rng.normal(6.2, sd, nread))
        m = A.OptionAMeasure("LED", A.MeasuredParameter("kW", b, "kW"),
                             A.MeasuredParameter("kW", r, "kW"),
                             A.StipulatedParameter("hours", H, "h/yr", "schedule"))
        for c in CONFS:
            res = A.savings(m, c)
            if abs(res["savings"] - true_delta * H) <= res["absolute_uncertainty"]:
                cov[c] += 1
        rel.append(A.savings(m, 0.90)["relative_uncertainty"])
    return {"reps": reps, "reading_sd_kw": sd, "readings_per_period": nread,
            **{f"coverage{int(c * 100)}_pct": 100 * cov[c] / reps for c in CONFS},
            "median_rel_unc90_pct": 100 * st.median(rel)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--scan-reps", type=int, default=500)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    jobs = {"reference": [(s, 0.15, 12.0, 2) for s in range(1, a.reps + 1)]}
    for f in (0.05, 0.10, 0.20, 0.30):
        jobs[f"frac_{f:.2f}"] = [(10000 + s, f, 12.0, 2) for s in range(a.scan_reps)]
    for nz in (6.0, 24.0, 36.0):
        jobs[f"noise_{nz:g}"] = [(20000 + s, 0.15, nz, 2) for s in range(a.scan_reps)]
    for y in (1, 3):
        jobs[f"years_{y}"] = [(30000 + s, 0.15, 12.0, y) for s in range(a.scan_reps)]

    stats = {}
    with Pool() as pool:
        for name, js in jobs.items():
            rows = pool.map(one, js, chunksize=20)
            stats[name] = summarize(rows)
            with open(os.path.join(a.out, f"mc_{name}.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                w.writeheader()
                w.writerows(rows)
            print(name, json.dumps({k: stats[name][k] for k in
                                    ("coverage90_pct", "mean_err", "median_fsu90_pct", "pass_rate_pct")}))
    stats["option_a"] = option_a_mc()
    with open(os.path.join(a.out, "validation_stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)


if __name__ == "__main__":
    main()
