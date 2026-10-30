"""Life-cycle cost sensitivity scans on the MUNI-LCC v0.1.0 worked example.

Plain-language header: this script re-runs the worked example's life-cycle
cost study while changing one input at a time (discount rate, gas price,
study period, and the verified savings within their uncertainty band), and
writes the results the preprint's sensitivity tables and figure use.

    python preprint/analysis/lcc_scans.py --repo . --out preprint/analysis/out
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os

from muni_lcc import lcc as L
from muni_lcc.pipeline import resolve_quantity


def build(proj_lcc, results, rate=None, years=None, gas=None, gas_saving_shift=0.0,
          kwh_saving_shift=0.0):
    lc = copy.deepcopy(proj_lcc)
    for side in ("base", "alternative"):
        for c in lc[side]["annual_costs"]:
            if "quantity_source" in c:
                q = resolve_quantity(c.pop("quantity_source"), results)
                price = c.pop("unit_price")
                if c["name"] == "natural gas":
                    price = gas if gas is not None else price
                    if side == "alternative":
                        q -= gas_saving_shift
                if c["name"] == "lighting electricity" and side == "alternative":
                    q -= kwh_saving_shift
                c["amount"] = q * price
    study = L.Study(years or lc["study_period_years"],
                    lc["real_discount_rate"] if rate is None else rate, lc.get("midyear", False))
    return L.compare(L.alternative_from_dict(lc["base"]), L.alternative_from_dict(lc["alternative"]), study)


def bisect(f, lo, hi, tol=1e-7):
    flo = f(lo)
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.repo, "examples", "project.json"), encoding="utf-8") as f:
        proj = json.load(f)
    with open(os.path.join(a.repo, "examples", "outputs", "results.json"), encoding="utf-8") as f:
        res = json.load(f)
    pl = proj["lcc"]
    ref = build(pl, res)

    rows = []
    for i in range(0, 21):
        d = i * 0.005
        z = build(pl, res, rate=d)
        rows.append({"scan": "rate", "x": d, **{k: z[k] for k in ("net_savings", "sir", "airr",
                                                                  "simple_payback_years",
                                                                  "discounted_payback_years")}})
    for i in range(0, 13):
        g = 0.60 + 0.10 * i
        z = build(pl, res, gas=g)
        rows.append({"scan": "gas_price", "x": round(g, 2), **{k: z[k] for k in (
            "net_savings", "sir", "airr", "simple_payback_years", "discounted_payback_years")}})
    for n in (10, 15, 20, 25, 30, 35, 40):
        z = build(pl, res, years=n)
        rows.append({"scan": "years", "x": n, **{k: z[k] for k in (
            "net_savings", "sir", "airr", "simple_payback_years", "discounted_payback_years")}})
    with open(os.path.join(a.out, "lcc_scans.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    c, oa = res["option_c"], res["option_a"][0]
    u_c, u_a = c["absolute_uncertainty"], oa["absolute_uncertainty"]
    # gas_saving_shift > 0 raises verified savings; low case lowers both by their 90 percent band
    lo = build(pl, res, gas_saving_shift=-u_c, kwh_saving_shift=-u_a)
    hi = build(pl, res, gas_saving_shift=u_c, kwh_saving_shift=u_a)
    lo_c = build(pl, res, gas_saving_shift=-u_c)
    hi_c = build(pl, res, gas_saving_shift=u_c)

    d_be = bisect(lambda d: build(pl, res, rate=d)["net_savings"], 0.0, 0.5)
    # net savings are linear in gas price and in verified gas savings: solve directly
    ns0 = ref["net_savings"]
    ns_g0 = build(pl, res, gas=0.0)["net_savings"]
    g_be = None if ns_g0 > 0 else 1.20 * (0 - ns_g0) / (ns0 - ns_g0)
    ns_s = build(pl, res, gas_saving_shift=-1000.0)["net_savings"]
    per_therm = (ns0 - ns_s) / 1000.0
    s_be = c["avoided_energy"] - ns0 / per_therm
    n_be = None
    for n in range(1, 41):
        if build(pl, res, years=n)["net_savings"] > 0:
            n_be = n
            break

    out = {"reference": ref,
           "gas_savings_unc_therms": u_c, "lighting_savings_unc_kwh": u_a,
           "ns_low_both": lo["net_savings"], "ns_high_both": hi["net_savings"],
           "sir_low_both": lo["sir"], "sir_high_both": hi["sir"],
           "ns_low_gas_only": lo_c["net_savings"], "ns_high_gas_only": hi_c["net_savings"],
           "breakeven_rate": d_be, "breakeven_gas_price": g_be,
           "ns_at_zero_gas_price": ns_g0, "ns_per_verified_therm": per_therm,
           "breakeven_gas_savings_therms": s_be,
           "breakeven_study_years": n_be}
    with open(os.path.join(a.out, "lcc_stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
