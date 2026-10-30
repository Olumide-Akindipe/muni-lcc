"""Write numbers.tex: every number quoted in the preprint, as LaTeX macros.

Plain-language header: the preprint text never types a result by hand. It
uses macros such as \\AvoidedTherms, which this script fills from the
toolkit's output files and the validation files. Re-run it after any change
and the paper's numbers follow.

    python preprint/analysis/make_numbers.py --repo . --data preprint/analysis/out --out preprint/numbers.tex
"""

from __future__ import annotations

import argparse
import json
import os


def _neg(s):
    return "$-$" + s[1:] if s.startswith("-") else s


def f0(x):
    s = f"{x:,.0f}"
    return "0" if s == "-0" else _neg(s)


def f1(x):
    return _neg(f"{x:,.1f}")


def f2(x):
    return _neg(f"{x:,.2f}")


def f3(x):
    return _neg(f"{x:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--before", required=True, help="validation outputs from v0.1.0")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    J = lambda p: json.load(open(p, encoding="utf-8"))  # noqa: E731
    S = J(os.path.join(a.repo, "examples/outputs/stats.json"))
    R = J(os.path.join(a.repo, "examples/outputs/results.json"))
    T = J(os.path.join(a.repo, "examples/data/TRUTH.json"))
    Z = J(os.path.join(a.data, "lcc_stats.json"))
    V = J(os.path.join(a.data, "validation_stats.json"))
    c, oa, lc = R["option_c"], R["option_a"][0], R["lcc"]
    cand = {x["form"]: x for x in c["candidates"]}
    m = {}

    # worked example
    m["ModelForm"] = c["model_form"]
    m["CvRmse"] = f1(c["baseline_statistics"]["cv_rmse"] * 100)
    m["RSq"] = f3(c["baseline_statistics"]["r2"])
    m["SlopeT"] = f1(c["baseline_statistics"]["min_abs_slope_t"])
    m["AdjBaseline"] = f0(c["adjusted_baseline"])
    m["ReportingUse"] = f0(c["reporting_actual"])
    m["AvoidedTherms"] = f0(c["avoided_energy"])
    m["FracSav"] = f1(c["fractional_savings"] * 100)
    m["FSU"] = f1(c["fractional_savings_uncertainty"] * 100)
    m["AbsUnc"] = f0(c["absolute_uncertainty"])
    m["TrueAvoided"] = f0(T["true_avoided_therms"])
    m["TrueAdjBaseline"] = f0(T["true_adjusted_baseline_therms"])
    m["ErrTherms"] = f0(c["avoided_energy"] - T["true_avoided_therms"])
    m["ErrPct"] = f1(100 * (c["avoided_energy"] - T["true_avoided_therms"]) / T["true_avoided_therms"])
    m["AdjBaseErrPct"] = f1(100 * (c["adjusted_baseline"] - T["true_adjusted_baseline_therms"])
                            / T["true_adjusted_baseline_therms"])
    import re
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", c["model_equation"])]
    m["EquationIntercept"], m["EquationSlope"], m["EquationCp"] = f2(nums[0]), f2(nums[1]), f"{nums[2]:.0f}"
    rep = J(os.path.join(a.repo, "examples/outputs/performance_report.json"))
    ob = {o["id"]: o for o in rep["objectives"]}
    m["OnePct"] = f1(ob["O1"]["percent_of_target"] * 100)
    m["TwoPct"] = f1(ob["O2"]["percent_of_target"] * 100)
    m["PlannedUnit"] = f2(rep["costs"]["planned_unit_cost"])
    m["ActualUnit"] = f2(rep["costs"]["actual_unit_cost"])
    m["UnitRatio"] = f1((rep["costs"]["actual_unit_cost"] / rep["costs"]["planned_unit_cost"] - 1) * 100)
    for k, x in cand.items():
        key = {"mean": "Mean", "2P": "TwoP", "3PH": "ThreePH", "4P": "FourP", "5P": "FiveP"}[k]
        m[f"Cv{key}"] = f1(x["cv_rmse"] * 100)
        m[f"Rsq{key}"] = f3(x["r2"])
        m[f"T{key}"] = "n/a" if x["min_abs_slope_t"] is None else f1(x["min_abs_slope_t"])
        m[f"Bic{key}"] = f1(x["bic"]) if "bic" in x else "n/a"
    m["OptASavings"] = f0(oa["savings"])
    m["OptAUnc"] = f0(oa["absolute_uncertainty"])
    m["OptARel"] = f1(oa["relative_uncertainty"] * 100)
    m["OptABase"] = f0(oa["baseline_annual"])
    m["OptARep"] = f0(oa["reporting_annual"])
    m["LccBase"] = f0(lc["lcc_base"])
    m["LccAlt"] = f0(lc["lcc_alt"])
    m["NetSavings"] = f0(lc["net_savings"])
    m["AddedInv"] = f0(lc["added_investment_pv"])
    m["OpSav"] = f0(lc["operational_savings_pv"])
    m["SIR"] = f2(lc["sir"])
    m["AIRR"] = f1(lc["airr"] * 100)
    m["SPB"] = f1(lc["simple_payback_years"])
    m["DPB"] = f1(lc["discounted_payback_years"])
    d = R["lcc_detail"]
    for side, key in (("base", "B"), ("alternative", "A")):
        for k in ("initial", "replacement", "residual", "energy", "omr", "total"):
            m[f"Lcc{key}{k.capitalize()}"] = f0(d[side][k])
    m["DueDate"] = S["report_due_date"]

    # LCC sensitivity
    m["NsLow"] = f0(Z["ns_low_both"])
    m["NsHigh"] = f0(Z["ns_high_both"])
    m["SirLow"] = f2(Z["sir_low_both"])
    m["SirHigh"] = f2(Z["sir_high_both"])
    m["BeRate"] = f1(Z["breakeven_rate"] * 100)
    m["NsZeroGas"] = f0(Z["ns_at_zero_gas_price"])
    m["NsPerTherm"] = f2(Z["ns_per_verified_therm"])
    m["BeYears"] = str(Z["breakeven_study_years"])
    m["GasSavPV"] = f0(Z["ns_per_verified_therm"] * c["avoided_energy"])

    # Monte Carlo
    ref = V["reference"]
    m["McReps"] = f0(ref["reps"])
    m["ScanReps"] = f0(V["frac_0.05"]["reps"])
    m["McMeanErr"] = f0(ref["mean_err"])
    m["McRmse"] = f0(ref["rmse"])
    m["McSdErr"] = f0(ref["sd_err"])
    m["McMeanTrue"] = f0(ref["mean_true"])
    m["McMeanUnc"] = f0(ref["mean_unc90"])
    m["McMedFsu"] = f1(ref["median_fsu90_pct"])
    m["McPass"] = f1(ref["pass_rate_pct"])
    m["McFsuOk"] = f1(ref["ok_fsu_pct"])
    m["McMaxNmbe"] = f"{ref['max_abs_nmbe'] * 100:.1e}".replace("e-", r"\times 10^{-") + "}"
    for cc in (80, 90, 95):
        m[f"McCov{ {80: 'Eighty', 90: 'Ninety', 95: 'NinetyFive'}[cc] }"] = f1(ref[f"coverage{cc}_pct"])
    for form, key in (("3PH", "ThreePH"), ("4P", "FourP"), ("5P", "FiveP"), ("2P", "TwoP")):
        m[f"McForm{key}"] = f1(ref["forms_pct"].get(form, 0.0))
    oa_mc = V["option_a"]
    m["OaReps"] = f0(oa_mc["reps"])
    m["OaSd"] = f2(oa_mc["reading_sd_kw"])
    m["OaCovEighty"] = f1(oa_mc["coverage80_pct"])
    m["OaCovNinety"] = f1(oa_mc["coverage90_pct"])
    m["OaCovNinetyFive"] = f1(oa_mc["coverage95_pct"])
    m["OaMedRel"] = f1(oa_mc["median_rel_unc90_pct"])

    lines = []

    # scan table rows
    import csv as _csv
    import math as _m

    def nonpos_pct(key, d=None):
        rows_ = list(_csv.DictReader(open(os.path.join(d or a.data, f"mc_{key}.csv"), encoding="utf-8")))
        return 100 * sum(float(x["est"]) <= 0 for x in rows_) / len(rows_)

    def undefined_pct(key, d):
        rows_ = list(_csv.DictReader(open(os.path.join(d, f"mc_{key}.csv"), encoding="utf-8")))
        return 100 * sum(_m.isnan(float(x["unc90"])) for x in rows_) / len(rows_)

    for key, mac in (("frac_0.05", "NonposFive"), ("frac_0.10", "NonposTen"), ("noise_36", "NonposNoise")):
        m[mac] = f1(nonpos_pct(key))

    # v0.1.0 versus v0.1.1
    B = J(os.path.join(a.before, "validation_stats.json"))
    U = J(os.path.join(a.data, "underfit_stats.json"))
    before_rows = []

    def cmp_row(label, b, v, fmt=f1):
        before_rows.append(f"{label} & {fmt(b)} & {fmt(v)} \\\\")

    for form in ("3PH", "4P", "5P"):
        cmp_row(f"Selects {form} (\\%)", B["reference"]["forms_pct"].get(form, 0.0), ref["forms_pct"].get(form, 0.0))
    cmp_row("Coverage at 90\\% (\\%)", B["reference"]["coverage90_pct"], ref["coverage90_pct"])
    cmp_row("RMSE (therms)", B["reference"]["rmse"], ref["rmse"], f0)
    before_rows.append(r"\multicolumn{3}{@{}l}{\emph{Weak or noisy savings, coverage at 90\% (\%)}} \\")
    cmp_row("$F_{\\rm true}=5\\%$", B["frac_0.05"]["coverage90_pct"], V["frac_0.05"]["coverage90_pct"])
    cmp_row("$\\sigma=36$", B["noise_36"]["coverage90_pct"], V["noise_36"]["coverage90_pct"])
    cmp_row("No uncertainty reported, $F_{\\rm true}=5\\%$ (\\%)", undefined_pct("frac_0.05", a.before),
            undefined_pct("frac_0.05", a.data))
    for truth in ("4P", "5P"):
        before_rows.append(r"\multicolumn{3}{@{}l}{\emph{True model " + truth + r", " + f"{300}" + r" replications}} \\")
        cmp_row(f"Selects {truth} (\\%)", U[truth]["v010"]["forms_pct"].get(truth, 0.0),
                U[truth]["v011"]["forms_pct"].get(truth, 0.0))
        cmp_row("Coverage at 90\\% (\\%)", U[truth]["v010"]["coverage90_pct"], U[truth]["v011"]["coverage90_pct"])
        cmp_row("RMSE (therms)", U[truth]["v010"]["rmse"], U[truth]["v011"]["rmse"], f0)
    lines.append("\\newcommand{\\BeforeAfterRows}{%\n" + "\n".join(before_rows) + "}")
    m["BeforeThreePH"] = f1(B["reference"]["forms_pct"].get("3PH", 0.0))
    m["BeforeNonThree"] = f1(100 - B["reference"]["forms_pct"].get("3PH", 0.0))
    m["AfterNonThree"] = f1(100 - ref["forms_pct"].get("3PH", 0.0))
    m["BeforeCovNinety"] = f1(B["reference"]["coverage90_pct"])
    m["BeforeRmse"] = f0(B["reference"]["rmse"])
    m["BeforeCovFive"] = f1(B["frac_0.05"]["coverage90_pct"])
    m["BeforeUndefFive"] = f1(undefined_pct("frac_0.05", a.before))
    m["BeforeCovNoise"] = f1(B["noise_36"]["coverage90_pct"])
    m["CovNoiseThirtySix"] = f1(V["noise_36"]["coverage90_pct"])
    m["UfFivePBefore"] = f1(U["5P"]["v010"]["forms_pct"].get("5P", 0.0))
    m["UfFivePAfter"] = f1(U["5P"]["v011"]["forms_pct"].get("5P", 0.0))
    m["UfFivePRmseChange"] = f1(100 * (U["5P"]["v011"]["rmse"] / U["5P"]["v010"]["rmse"] - 1))
    m["UfFourPRmseChange"] = f1(100 * (U["4P"]["v011"]["rmse"] / U["4P"]["v010"]["rmse"] - 1))
    m["UfFivePCovAfter"] = f1(U["5P"]["v011"]["coverage90_pct"])
    m["UfFivePCovBefore"] = f1(U["5P"]["v010"]["coverage90_pct"])
    m["McSeRef"] = f1(100 * _m.sqrt(0.9 * 0.1 / V["reference"]["reps"]))
    m["McSeScan"] = f1(100 * _m.sqrt(0.9 * 0.1 / V["frac_0.05"]["reps"]))
    m["McMedCv"] = f1(V["reference"]["median_cv_pct"])
    m["CovFrFive"] = f1(V["frac_0.05"]["coverage90_pct"])
    m["CovFrTwenty"] = f1(V["frac_0.20"]["coverage90_pct"])
    m["CovYrOne"] = f1(V["years_1"]["coverage90_pct"])
    m["CovYrThree"] = f1(V["years_3"]["coverage90_pct"])
    m["CovYrOneEighty"] = f1(V["years_1"]["coverage80_pct"])
    m["PassFrTen"] = f1(V["frac_0.10"]["pass_rate_pct"])
    m["PassFrTwenty"] = f1(V["frac_0.20"]["pass_rate_pct"])
    m["PassNoiseTwentyFour"] = f1(V["noise_24"]["pass_rate_pct"])
    m["CvOkNoiseThirtySix"] = f1(V["noise_36"]["ok_cv_rmse_pct"])
    m["MedFsuFive"] = f1(V["frac_0.05"]["median_fsu90_pct"])
    m["MedFsuThirty"] = f1(V["frac_0.30"]["median_fsu90_pct"])
    m["RmseYrOne"] = f0(V["years_1"]["rmse"])
    m["RmseYrThree"] = f0(V["years_3"]["rmse"])
    m["RmseNoiseSix"] = f0(V["noise_6"]["rmse"])
    m["RmseNoiseThirtySix"] = f0(V["noise_36"]["rmse"])

    refrows = list(_csv.DictReader(open(os.path.join(a.data, "mc_reference.csv"), encoding="utf-8")))
    for form, key in (("3PH", "ThreePH"), ("4P", "FourP"), ("5P", "FiveP")):
        sub = [x for x in refrows if x["form"] == form]
        e = [float(x["est"]) - float(x["true"]) for x in sub]
        m[f"CovForm{key}"] = f1(100 * sum(abs(v) <= float(x["unc90"]) for v, x in zip(e, sub)) / len(sub))
        m[f"RmseForm{key}"] = f0(_m.sqrt(sum(v * v for v in e) / len(e)))
        m[f"MeanErrForm{key}"] = f0(sum(e) / len(e))
        m[f"NForm{key}"] = f0(len(sub))

    def row(label, s, key):
        return (f"{label} & {f0(s['mean_err'])} & {f0(s['rmse'])} & {f1(s['median_fsu90_pct'])} & "
                f"{f1(s['coverage80_pct'])} & {f1(s['coverage90_pct'])} & {f1(s['coverage95_pct'])} & "
                f"{f1(s['pass_rate_pct'])} & {f1(nonpos_pct(key))} \\\\")
    rows = [row("Reference", ref, "reference")]
    rows += [r"\multicolumn{9}{l}{\emph{Savings fraction $F_{\rm true}$}} \\"]
    for k, lab in (("frac_0.05", "5\\%"), ("frac_0.10", "10\\%"), ("frac_0.20", "20\\%"), ("frac_0.30", "30\\%")):
        rows.append(row(lab, V[k], k))
    rows += [r"\multicolumn{9}{l}{\emph{Noise s.d. $\sigma$ (therms/day)}} \\"]
    for k, lab in (("noise_6", "6"), ("noise_24", "24"), ("noise_36", "36")):
        rows.append(row(lab, V[k], k))
    rows += [r"\multicolumn{9}{l}{\emph{Baseline length (months)}} \\"]
    for k, lab in (("years_1", "12"), ("years_3", "36")):
        rows.append(row(lab, V[k], k))
    lines.append("\\newcommand{\\ScanRows}{%\n" + "\n".join(rows) + "}")

    forms_rows = []
    for k, lab in (("reference", "Reference"), ("noise_6", "$\\sigma=6$"), ("noise_36", "$\\sigma=36$"),
                   ("years_1", "12-month baseline"), ("years_3", "36-month baseline")):
        fp = V[k]["forms_pct"]
        forms_rows.append(f"{lab} & {f1(fp.get('2P', 0))} & {f1(fp.get('3PH', 0))} & "
                          f"{f1(fp.get('4P', 0))} & {f1(fp.get('5P', 0))} \\\\")
    lines.append("\\newcommand{\\FormRows}{%\n" + "\n".join(forms_rows) + "}")
    head = ["% Generated by analysis/make_numbers.py. Do not edit by hand."]
    head += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in m.items()]
    lines = head + lines
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"{len(m)} macros written")


if __name__ == "__main__":
    main()
