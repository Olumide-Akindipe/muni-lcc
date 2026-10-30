"""Performance report content aligned with 2 CFR 200.329 (as amended April 2024).

What this module does:
  * computes the report due date from 200.329(c)(1): annual reports 90 days
    after the reporting period ends; quarterly or semiannual reports 30 days
    after; the final report 120 days after the period of performance ends for
    a recipient and 90 days for a subrecipient;
  * assembles the content elements of 200.329(c)(2): a comparison of actual
    accomplishments with the objectives of the award, the reasons objectives
    were not met where applicable, and analysis and explanation of cost
    overruns or high unit costs;
  * carries any significant developments under 200.329(e), including the
    corrective action plan required for adverse developments.

What it does not do: it does not replace the OMB-approved common form the
awarding agency prescribes (for example the RPPR or an agency-specific
form). Its output is the verified content that goes into that form.
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Dict, List, Optional

FREQ_DAYS = {"annual": 90, "semiannual": 30, "quarterly": 30}


def due_date(period_end: str, frequency: str, is_subrecipient: bool = False) -> str:
    end = dt.date.fromisoformat(period_end)
    if frequency == "final":
        days = 90 if is_subrecipient else 120
    elif frequency in FREQ_DAYS:
        days = FREQ_DAYS[frequency]
    else:
        raise ValueError("frequency must be annual, semiannual, quarterly, or final")
    return (end + dt.timedelta(days=days)).isoformat()


def _actual_for(obj: dict, results: dict) -> Optional[float]:
    src = obj.get("actual_source", "value")
    if src == "value":
        return obj.get("actual")
    if src == "option_c":
        return results["option_c"]["avoided_energy"]
    if src.startswith("option_a:"):
        name = src.split(":", 1)[1]
        for r in results.get("option_a", []):
            if r["measure"] == name:
                return r["savings"]
        raise KeyError(f"no Option A measure named {name}")
    if src == "lcc:net_savings":
        return results["lcc"]["net_savings"]
    raise ValueError(f"unknown actual_source {src}")


def build(config: dict, results: dict, final: bool = False) -> Dict[str, object]:
    award, period = config["award"], config["award"]["reporting_period"]
    issues: List[str] = []

    objectives = []
    for obj in config["objectives"]:
        actual = _actual_for(obj, results)
        target = obj["target"]
        met = actual is not None and actual >= target
        row = {"id": obj["id"], "description": obj["description"], "metric": obj["metric"],
               "units": obj["units"], "target": target, "actual": actual,
               "percent_of_target": (actual / target if actual is not None and target else None),
               "met": met, "reason_not_met": obj.get("reason_not_met", "")}
        if not met and not row["reason_not_met"].strip():
            issues.append(f"Objective {obj['id']} not met: 200.329(c)(2) requires the reasons.")
        objectives.append(row)

    cost = config["costs"]
    verified = _actual_for({"actual_source": cost["unit_basis_source"]}, results)
    planned_unit = cost["budget"] / cost["planned_units"] if cost["planned_units"] else None
    actual_unit = cost["actual_cost"] / verified if verified else None
    overrun = cost["actual_cost"] > cost["budget"]
    high_unit = (planned_unit is not None and actual_unit is not None
                 and actual_unit > planned_unit * (1 + cost.get("unit_cost_tolerance", 0.10)))
    cost_block = {"budget": cost["budget"], "actual_cost": cost["actual_cost"],
                  "variance": cost["actual_cost"] - cost["budget"],
                  "unit": cost["unit"], "planned_unit_cost": planned_unit,
                  "actual_unit_cost": actual_unit, "cost_overrun": overrun,
                  "high_unit_cost": high_unit, "explanation": cost.get("explanation", "")}
    if (overrun or high_unit) and not cost_block["explanation"].strip():
        issues.append("Cost overrun or high unit cost: 200.329(c)(2) requires analysis and explanation.")

    developments = config.get("significant_developments", [])
    for d in developments:
        if d.get("type") == "adverse" and not d.get("corrective_action", "").strip():
            issues.append(f"Adverse development '{d['summary']}': 200.329(e) requires a corrective action plan.")

    return {
        "status": "FINAL" if final else "DRAFT",
        "generated": dt.date.today().isoformat(),
        "regulation": "2 CFR 200.329 as amended 89 FR 30136 (April 22, 2024)",
        "award": {k: award[k] for k in ("award_id", "agency", "recipient", "project") if k in award},
        "reporting_period": period,
        "due_date": due_date(period["end"] if period["frequency"] != "final"
                             else award["period_of_performance_end"],
                             period["frequency"], award.get("is_subrecipient", False)),
        "objectives": objectives,
        "costs": cost_block,
        "significant_developments": developments,
        "mv_summary": _mv_summary(results),
        "lcc_summary": results.get("lcc"),
        "completeness_issues": issues,
    }


def _mv_summary(results: dict) -> Dict[str, object]:
    out = {}
    if "option_c" in results:
        c = results["option_c"]
        out["option_c"] = {k: c[k] for k in ("model_form", "model_equation", "adjusted_baseline",
                                              "reporting_actual", "avoided_energy",
                                              "fractional_savings", "fractional_savings_uncertainty",
                                              "confidence")}
        out["option_c"]["baseline_statistics"] = c["baseline_statistics"]
        if "acceptance" in c:
            out["option_c"]["acceptance"] = c["acceptance"]
    if "option_a" in results:
        out["option_a"] = [{k: r[k] for k in ("measure", "savings", "savings_units",
                                              "relative_uncertainty", "stipulated_parameter")}
                           for r in results["option_a"]]
    return out


# ------------------------------------------------------------ rendering

def _f(x, nd=0, pct=False):
    if x is None:
        return "n/a"
    if pct:
        return f"{x * 100:.1f}%"
    return f"{x:,.{nd}f}"


def to_markdown(rep: dict) -> str:
    L = []
    if rep["status"] == "DRAFT":
        L.append("> **DRAFT. Not verified by the recipient. Do not submit.**\n")
    a = rep["award"]
    L.append(f"# Program performance report: {a.get('project', '')}\n")
    L.append(f"Prepared under {rep['regulation']}. Content for entry into the awarding agency's "
             "OMB-approved performance reporting form.\n")
    L.append("| Item | Value |\n|---|---|")
    for k, label in (("award_id", "Award"), ("agency", "Agency"), ("recipient", "Recipient")):
        L.append(f"| {label} | {a.get(k, '')} |")
    p = rep["reporting_period"]
    L.append(f"| Reporting period | {p['start']} to {p['end']} ({p['frequency']}) |")
    L.append(f"| Due date, 200.329(c)(1) | {rep['due_date']} |\n")

    L.append("## 1. Accomplishments compared with objectives, 200.329(c)(2)\n")
    L.append("| Objective | Metric | Target | Verified actual | Percent of target | Met |\n|---|---|---|---|---|---|")
    for o in rep["objectives"]:
        L.append(f"| {o['id']}: {o['description']} | {o['metric']} ({o['units']}) | {_f(o['target'])} | "
                 f"{_f(o['actual'])} | {_f(o['percent_of_target'], pct=True)} | {'Yes' if o['met'] else 'No'} |")
    unmet = [o for o in rep["objectives"] if not o["met"]]
    if unmet:
        L.append("\n**Reasons objectives were not met**\n")
        for o in unmet:
            L.append(f"* {o['id']}: {o['reason_not_met'] or 'REQUIRED, not yet provided.'}")
    L.append("")

    L.append("## 2. Verification basis\n")
    mv = rep["mv_summary"]
    if "option_c" in mv:
        c, s = mv["option_c"], mv["option_c"]["baseline_statistics"]
        L.append("**IPMVP Option C, whole facility (FEMP M&V Guidelines v5.0).** "
                 f"Baseline model {c['model_form']}: `{c['model_equation']}`, n = {s['n']} periods.\n")
        L.append("| Statistic | Value |\n|---|---|")
        L.append(f"| CV(RMSE) | {_f(s['cv_rmse'], pct=True)} |")
        L.append(f"| R-squared | {s['r2']:.3f} |")
        L.append(f"| NMBE (net determination bias) | {abs(s['nmbe']) * 100:.4f}% |")
        if s.get("slope_t"):
            ts = ", ".join(f"{x:.1f}" for x in s["slope_t"])
            L.append(f"| Slope t-statistics | {ts} |")
        L.append(f"| Baseline in whole-year set (FEMP v5.0 4.4) | {'Yes' if s.get('whole_year_baseline') else 'No'} ({s['n']} periods) |")
        L.append(f"| Adjusted baseline | {_f(c['adjusted_baseline'])} |")
        L.append(f"| Reporting period use | {_f(c['reporting_actual'])} |")
        L.append(f"| Avoided energy use | {_f(c['avoided_energy'])} |")
        L.append(f"| Fractional savings | {_f(c['fractional_savings'], pct=True)} |")
        L.append(f"| Fractional savings uncertainty at {int(c['confidence'] * 100)}% confidence | "
                 f"{_f(c['fractional_savings_uncertainty'], pct=True)} |")
        if "acceptance" in c:
            res = c["acceptance"]
            L.append(f"| Meets acceptance criteria | {'Yes' if res['all_pass'] else 'No'} |")
        L.append("")
        if "acceptance" in c:
            res, cr = c["acceptance"], c["acceptance"]["criteria"]
            src = cr.get("sources", {})
            rows = [("R-squared", f"at least {cr['min_r2']}", "r2", "min_r2"),
                    ("Absolute NMBE", f"at most {cr['max_abs_nmbe'] * 100:.3f}%", "nmbe", "max_abs_nmbe"),
                    ("Slope t-statistic", f"greater than {cr['min_abs_slope_t']}", "slope_t", "min_abs_slope_t"),
                    ("CV(RMSE)", f"at most {cr['max_cv_rmse'] * 100:.0f}%", "cv_rmse", "max_cv_rmse"),
                    ("Fractional savings uncertainty", f"at most {cr['max_fsu'] * 100:.0f}%", "fsu", "max_fsu")]
            L.append("**Acceptance criteria.** The project M&V plan governs; these are the values applied.\n")
            L.append("| Criterion | Threshold | Pass | Source |\n|---|---|---|---|")
            for label, thr, key, skey in rows:
                L.append(f"| {label} | {thr} | {'Yes' if res['checks'][key] else 'No'} | {src.get(skey, '')} |")
            for w in res.get("warnings", []):
                L.append(f"\nWarning: {w}")
        L.append("")
    for r in mv.get("option_a", []):
        sp = r["stipulated_parameter"]
        L.append(f"**IPMVP Option A, {r['measure']}.** Savings {_f(r['savings'])} {r['savings_units']}, "
                 f"relative measurement uncertainty {_f(r['relative_uncertainty'], pct=True)}. "
                 f"Stipulated: {sp['name']} = {_f(sp['value'])} {sp['units']} ({sp['basis']}).\n")

    L.append("## 3. Cost analysis, 200.329(c)(2)\n")
    c = rep["costs"]
    L.append("| Item | Value |\n|---|---|")
    L.append(f"| Budget | ${_f(c['budget'])} |")
    L.append(f"| Actual cost | ${_f(c['actual_cost'])} |")
    L.append(f"| Variance (actual minus budget) | ${_f(c['variance'])} |")
    L.append(f"| Planned unit cost | ${_f(c['planned_unit_cost'], 3)} per {c['unit']} |")
    L.append(f"| Actual unit cost, verified basis | ${_f(c['actual_unit_cost'], 3)} per {c['unit']} |")
    L.append(f"| Cost overrun | {'Yes' if c['cost_overrun'] else 'No'} |")
    L.append(f"| High unit cost | {'Yes' if c['high_unit_cost'] else 'No'} |\n")
    if c["cost_overrun"] or c["high_unit_cost"]:
        L.append(f"**Explanation.** {c['explanation'] or 'REQUIRED, not yet provided.'}\n")

    if rep.get("lcc_summary"):
        z = rep["lcc_summary"]
        L.append("## 4. Life-cycle cost effectiveness (ASTM E917 method)\n")
        L.append("| Measure | Value |\n|---|---|")
        L.append(f"| Net savings, present value | ${_f(z['net_savings'])} |")
        L.append(f"| Savings-to-investment ratio | {_f(z['sir'], 2)} |")
        L.append(f"| Adjusted internal rate of return | {_f(z['airr'], pct=True)} |")
        L.append(f"| Simple payback | {_f(z['simple_payback_years'], 1)} years |")
        L.append(f"| Discounted payback | {_f(z['discounted_payback_years'], 1)} years |\n")

    L.append("## 5. Significant developments, 200.329(e)\n")
    devs = rep["significant_developments"]
    if not devs:
        L.append("None reported for this period.\n")
    for d in devs:
        L.append(f"* **{d.get('type', 'note').title()}:** {d['summary']}")
        if d.get("corrective_action"):
            L.append(f"  Corrective action: {d['corrective_action']}")
        if d.get("assistance_needed"):
            L.append(f"  Assistance needed: {d['assistance_needed']}")
    L.append("")

    if rep["completeness_issues"]:
        L.append("## Completeness check\n")
        for i in rep["completeness_issues"]:
            L.append(f"* {i}")
        L.append("")
    L.append(f"Generated {rep['generated']} by MUNI-LCC.")
    return "\n".join(L) + "\n"


def to_json(rep: dict) -> str:
    return json.dumps(rep, indent=2, default=float)
