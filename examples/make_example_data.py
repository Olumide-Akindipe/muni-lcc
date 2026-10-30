"""Generate the synthetic worked-example data. Deterministic (seed 2026).

SYNTHETIC DATA. Nothing here is a real building or a real utility bill. The
monthly temperatures are rounded, Albany-like illustrative values, not NOAA
normals. The point of synthetic data is that the true savings are known in
advance, so the toolkit's answer can be checked against the right answer.

Building: a hypothetical 40,000 sq ft municipal office ("Town Hall").
Natural gas meter (Option C): true baseline use per day
    40 therms + 6 therms per degree F below 58 F,
and the boiler and controls retrofit removes exactly 15 percent of use.
Lighting (Option A): fixture circuit kW spot readings before and after an
LED retrofit; operating hours stipulated from the posted building schedule.
"""

import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 2026
TRUE_SAVINGS_FRACTION = 0.15
DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
TEMPS = [22, 25, 34, 47, 58, 67, 72, 70, 62, 50, 39, 28]   # illustrative, F


def true_rate(t):
    return 40.0 + 6.0 * max(58.0 - t, 0.0)


def main():
    rng = np.random.default_rng(SEED)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)

    def write(name, years, scale, temp_shift_sd):
        rows, truth_base = [], 0.0
        for y in years:
            for i, m in enumerate(MONTHS):
                t = round(TEMPS[i] + rng.normal(0, temp_shift_sd), 1)
                base_rate = true_rate(t)
                rate = base_rate * scale + rng.normal(0, 12.0)
                rows.append({"period": f"{y}-{i + 1:02d}", "days": DAYS[i],
                             "energy": round(rate * DAYS[i], 1), "mean_temp": t})
                truth_base += base_rate * DAYS[i]
        with open(os.path.join(HERE, "data", name), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["period", "days", "energy", "mean_temp"])
            w.writeheader()
            w.writerows(rows)
        return truth_base

    write("gas_baseline.csv", [2023, 2024], 1.0, 2.5)
    true_adjusted = write("gas_reporting.csv", [2025], 1.0 - TRUE_SAVINGS_FRACTION, 2.5)

    truth = {"synthetic": True, "seed": SEED,
             "true_savings_fraction_option_c": TRUE_SAVINGS_FRACTION,
             "true_adjusted_baseline_therms": round(true_adjusted, 1),
             "true_avoided_therms": round(true_adjusted * TRUE_SAVINGS_FRACTION, 1),
             "true_lighting_kw_reduction": round(14.6 - 6.2, 2),
             "true_lighting_savings_kwh": round((14.6 - 6.2) * 3_380, 1)}
    with open(os.path.join(HERE, "data", "TRUTH.json"), "w", encoding="utf-8") as f:
        json.dump(truth, f, indent=2)
    print(json.dumps(truth, indent=2))


if __name__ == "__main__":
    main()
