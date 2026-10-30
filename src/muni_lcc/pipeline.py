"""Run a full project: Option A measures, Option C baseline and savings, LCC, report.

A project is described by one JSON file. Relative paths inside it are
resolved against the JSON file's folder. See examples/project.json.
"""

from __future__ import annotations

import json
import os
from typing import Dict

from . import lcc as lccmod
from . import mv_option_a as A
from . import mv_option_c as C
from . import report as R


def _p(base: str, path: str) -> str:
    return path if os.path.isabs(path) else os.path.join(base, path)


def resolve_quantity(ref: str, results: Dict[str, object]) -> float:
    """Resolve an annual quantity from verified results, so LCC uses verified savings.

    Forms: "option_c:adjusted_baseline" and "option_c:reporting_actual", scaled to
    a 365-day year by the reporting period length in days; "option_a:<measure>:baseline_annual"
    and "option_a:<measure>:reporting_annual".
    """
    parts = ref.split(":")
    if parts[0] == "option_c":
        c = results["option_c"]
        per_year = 365.0 / c["reporting_days"]
        return c[parts[1]] * per_year
    if parts[0] == "option_a":
        for r in results["option_a"]:
            if r["measure"] == parts[1]:
                return r[parts[2]]
        raise KeyError(f"no Option A measure named {parts[1]}")
    raise ValueError(f"unknown quantity_source {ref}")


def run(project_path: str, final: bool = False) -> Dict[str, object]:
    with open(project_path, encoding="utf-8") as f:
        cfg = json.load(f)
    base = os.path.dirname(os.path.abspath(project_path))
    confidence = cfg.get("confidence", 0.90)
    results: Dict[str, object] = {}

    if "option_a" in cfg:
        results["option_a"] = []
        for m in cfg["option_a"]:
            measure = A.OptionAMeasure(
                name=m["name"],
                baseline=A.MeasuredParameter(**m["baseline"]),
                reporting=A.MeasuredParameter(**m["reporting"]),
                stipulated=A.StipulatedParameter(**m["stipulated"]),
                interactive_factor=m.get("interactive_factor", 1.0),
                savings_units=m.get("savings_units", "kWh/yr"),
            )
            results["option_a"].append(A.savings(measure, confidence))

    if "option_c" in cfg:
        oc = cfg["option_c"]
        baseline = C.read_periods(_p(base, oc["baseline_csv"]))
        reporting = C.read_periods(_p(base, oc["reporting_csv"]))
        criteria = None
        crit_path = oc.get("acceptance_criteria")
        if crit_path:
            with open(_p(base, crit_path), encoding="utf-8") as f:
                criteria = json.load(f)
        min_t = criteria["min_abs_slope_t"] if criteria else 2.0
        fit = C.fit_baseline(baseline, force=oc.get("force_model"), min_slope_t=min_t)
        res = C.avoided_energy(fit["model"], baseline, reporting, confidence)
        res["candidates"] = fit["candidates"]
        res["energy_units"] = oc.get("energy_units", "kWh")
        if criteria:
            res["acceptance"] = C.check_acceptance(res, criteria)
        results["option_c"] = res

    if "lcc" in cfg:
        lc = cfg["lcc"]
        for side in ("base", "alternative"):
            for c in lc[side].get("annual_costs", []):
                if "quantity_source" in c:
                    c["amount"] = resolve_quantity(c.pop("quantity_source"), results) * c.pop("unit_price")
        study = lccmod.Study(lc["study_period_years"], lc.get("real_discount_rate",
                             lccmod.FEMP_2025["real_discount_rate"]), lc.get("midyear", False))
        b = lccmod.alternative_from_dict(lc["base"])
        a = lccmod.alternative_from_dict(lc["alternative"])
        results["lcc"] = lccmod.compare(b, a, study)
        results["lcc"]["study_period_years"] = study.study_period_years
        results["lcc"]["real_discount_rate"] = study.real_discount_rate
        results["lcc_detail"] = {"base": lccmod.lcc(b, study), "alternative": lccmod.lcc(a, study)}

    if "award" in cfg:
        results["report"] = R.build(cfg, results, final=final)
    return results
