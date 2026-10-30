"""Check that the v0.1.1 selection rule does not underfit when the truth is 4P or 5P.

Plain-language header: the v0.1.1 change makes model selection stricter about
extra parameters. This script checks the other side: when the true building
really does have a cooling slope (4P or 5P), does the stricter rule still find
it? It runs the same synthetic tests under the v0.1.0 rule (lowest CV(RMSE))
and the v0.1.1 rule (lowest BIC), on identical data.

    PYTHONPATH=<v0.1.1 src> python preprint/analysis/underfit_check.py --out preprint/analysis/out_v011
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics as st

import numpy as np

from muni_lcc import mv_option_c as C

DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
TEMPS = [22, 25, 34, 47, 58, 67, 72, 70, 62, 50, 39, 28]
TRUTHS = {
    "4P": lambda t: 40.0 + 6.0 * max(58.0 - t, 0.0) + 2.0 * max(t - 58.0, 0.0),
    "5P": lambda t: 40.0 + 6.0 * max(55.0 - t, 0.0) + 5.0 * max(t - 63.0, 0.0),
}


def synth(rate, seed, frac=0.15, noise=12.0):
    rng = np.random.default_rng(seed)

    def block(ny, scale):
        out, truth = [], 0.0
        for y in range(ny):
            for i in range(12):
                t = round(TEMPS[i] + rng.normal(0, 2.5), 1)
                r = rate(t)
                out.append(C.Period(f"{y}-{i}", DAYS[i], round((r * scale + rng.normal(0, noise)) * DAYS[i], 1), t))
                truth += r * DAYS[i]
        return out, truth

    b, _ = block(2, 1.0)
    r, adj = block(1, 1.0 - frac)
    return b, r, adj * frac


def select(fits, rule):
    pool = [f for f in fits if f[1]["slopes_significant"]] or fits
    key = (lambda f: f[1]["cv_rmse"]) if rule == "v010" else (lambda f: (f[1]["bic"], f[1]["p"]))
    return min(pool, key=key)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=300)
    a = ap.parse_args()
    out = {}
    for name, rate in TRUTHS.items():
        res = {"v010": [], "v011": []}
        for s in range(a.reps):
            b, r, true_sav = synth(rate, 50000 + s)
            fits = []
            for form in C.MODEL_FORMS:
                m = C.fit_form(form, b)
                if m is None:
                    continue
                stt = C.fit_statistics(m, b)
                stt["slopes_significant"] = stt["min_abs_slope_t"] is None or stt["min_abs_slope_t"] > 2.0
                fits.append((m, stt))
            for rule in ("v010", "v011"):
                m, _ = select(fits, rule)
                e = C.avoided_energy(m, b, r, 0.90)
                res[rule].append((m.form, e["avoided_energy"] - true_sav, e["absolute_uncertainty"]))
        out[name] = {}
        for rule, rows in res.items():
            forms = {}
            for f, _, _ in rows:
                forms[f] = forms.get(f, 0) + 1
            out[name][rule] = {
                "forms_pct": {k: 100 * v / len(rows) for k, v in sorted(forms.items())},
                "rmse": math.sqrt(st.mean(e * e for _, e, _ in rows)),
                "coverage90_pct": 100 * st.mean(1.0 if abs(e) <= u else 0.0 for _, e, u in rows),
            }
        print(name, json.dumps(out[name]))
    with open(os.path.join(a.out, "underfit_stats.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
