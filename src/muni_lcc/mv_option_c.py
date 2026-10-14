"""IPMVP Option C: whole facility, utility-meter regression baseline.

As defined in DOE FEMP M&V Guidelines v5.0 (September 2024), which apply
IPMVP Core Concepts 2022 (EVO 10000-1:2022). Uncertainty uses the ASHRAE
Guideline 14 approximation, not the EVO 10100-1:2018 procedure FEMP cites;
see docs/METHODS.md.

Baseline model: energy use per day as a function of mean outdoor dry-bulb
temperature over each billing period, fitted by days-weighted least squares.
Candidate forms follow the inverse-modeling change-point family used in
ASHRAE Guideline 14 and FEMP practice:

    mean   E = b0
    2P     E = b0 + b1*T
    3PC    E = b0 + b1*max(T - cp, 0)                 cooling
    3PH    E = b0 + b1*max(cp - T, 0)                 heating
    4P     E = b0 + b1*min(T - cp, 0) + b2*max(T - cp, 0)
    5P     E = b0 + b1*max(cpH - T, 0) + b2*max(T - cpC, 0)

Change points are found by grid search. Models whose slopes have the wrong
physical sign are rejected. Among valid models, those whose slope
coefficients are all statistically significant (|t| > 2.0, the IPMVP value
quoted in FEMP v5.0 Section 5.3.4.1) are preferred; the selected model is the
preferred model with the lowest CV(RMSE). If no model has significant slopes,
the lowest CV(RMSE) valid model is selected and the acceptance check fails on
the t-statistic. The user can force a form.

Avoided energy use (FEMP v5.0, IPMVP):
    savings = sum(adjusted baseline over reporting period) - sum(reporting use)

Fit statistics on period totals, with p = number of model parameters
including change points:
    CV(RMSE) = sqrt(SSE / (n - p)) / mean(y)
    NMBE     = sum(y - yhat) / ((n - p) * mean(y))
    R2       = 1 - SSE / SST
    t_j      = b_j / se(b_j), se from the weighted least squares covariance
               s^2 (X'WX)^-1 with s^2 = sum(w r^2) / (n - p), conditional on the
               selected change points (slope coefficients only)

FEMP v5.0 Section 4.4 recommends baselines in whole-year sets (12, 24, 36,
or 48 months); the result flags a baseline that is not.

Fractional savings uncertainty, ASHRAE Guideline 14 approximation for
monthly data without autocorrelation correction:
    FSU = t * 1.26 * CV(RMSE) / F * sqrt((n + 2) / (n * m))
n baseline periods, m reporting periods, F fractional savings.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import numpy as np

from .stats import t_critical

MODEL_FORMS = ("mean", "2P", "3PC", "3PH", "4P", "5P")
N_PARAMS = {"mean": 1, "2P": 2, "3PC": 3, "3PH": 3, "4P": 4, "5P": 5}


@dataclass
class Period:
    label: str
    days: float
    energy: float          # total energy in the period
    mean_temp: float       # mean outdoor dry-bulb temperature

    @property
    def rate(self) -> float:
        return self.energy / self.days


def read_periods(path: str) -> List[Period]:
    """Read a CSV with columns: period, days, energy, mean_temp."""
    out = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.append(Period(row["period"], float(row["days"]), float(row["energy"]),
                              float(row["mean_temp"])))
    if not out:
        raise ValueError(f"{path}: no rows")
    return out


@dataclass
class Model:
    form: str
    coef: List[float]
    change_points: List[float]

    def design(self, T: np.ndarray) -> np.ndarray:
        one = np.ones_like(T)
        f, cp = self.form, self.change_points
        if f == "mean":
            cols = [one]
        elif f == "2P":
            cols = [one, T]
        elif f == "3PC":
            cols = [one, np.maximum(T - cp[0], 0)]
        elif f == "3PH":
            cols = [one, np.maximum(cp[0] - T, 0)]
        elif f == "4P":
            cols = [one, np.minimum(T - cp[0], 0), np.maximum(T - cp[0], 0)]
        elif f == "5P":
            cols = [one, np.maximum(cp[0] - T, 0), np.maximum(T - cp[1], 0)]
        else:
            raise ValueError(f"unknown model form {f}")
        return np.column_stack(cols)

    def predict_rate(self, T: Sequence[float]) -> np.ndarray:
        return self.design(np.asarray(T, dtype=float)) @ np.asarray(self.coef)

    def predict_energy(self, periods: Sequence[Period]) -> np.ndarray:
        T = np.array([p.mean_temp for p in periods])
        days = np.array([p.days for p in periods])
        return self.predict_rate(T) * days

    def equation(self) -> str:
        c, cp = [round(x, 4) for x in self.coef], [round(x, 2) for x in self.change_points]
        f = self.form
        if f == "mean":
            return f"E/day = {c[0]}"
        if f == "2P":
            return f"E/day = {c[0]} + {c[1]}*T"
        if f == "3PC":
            return f"E/day = {c[0]} + {c[1]}*max(T - {cp[0]}, 0)"
        if f == "3PH":
            return f"E/day = {c[0]} + {c[1]}*max({cp[0]} - T, 0)"
        if f == "4P":
            return f"E/day = {c[0]} + {c[1]}*min(T - {cp[0]}, 0) + {c[2]}*max(T - {cp[0]}, 0)"
        return f"E/day = {c[0]} + {c[1]}*max({cp[0]} - T, 0) + {c[2]}*max(T - {cp[1]}, 0)"


def _wls(X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return coef


def _valid(form: str, coef: np.ndarray) -> bool:
    if form == "3PC":
        return coef[1] > 0
    if form == "3PH":
        return coef[1] > 0
    if form == "4P":
        # heating side slope negative in T (energy falls as T rises) or cooling side positive
        return coef[1] < coef[2]
    if form == "5P":
        return coef[1] > 0 and coef[2] > 0
    return True


WHOLE_YEAR_PERIODS = (12, 24, 36, 48)


def slope_t_statistics(model: Model, periods: Sequence[Period]) -> List[float]:
    """t-statistics of the slope coefficients (all but the intercept)."""
    if len(model.coef) < 2:
        return []
    T = np.array([p.mean_temp for p in periods])
    y = np.array([p.rate for p in periods])
    w = np.array([p.days for p in periods])
    X = model.design(T)
    n, p = len(y), N_PARAMS[model.form]
    r = y - X @ np.asarray(model.coef)
    s2 = float((w * r * r).sum()) / (n - p)
    cov = s2 * np.linalg.inv(X.T @ (X * w[:, None]))
    se = np.sqrt(np.diag(cov))
    return [float(b / e) if e > 0 else math.inf for b, e in zip(model.coef[1:], se[1:])]


def fit_statistics(model: Model, periods: Sequence[Period]) -> Dict[str, object]:
    y = np.array([p.energy for p in periods])
    yhat = model.predict_energy(periods)
    n, p = len(y), N_PARAMS[model.form]
    if n <= p:
        raise ValueError("not enough baseline periods for this model form")
    resid = y - yhat
    sse, ybar = float(resid @ resid), float(y.mean())
    sst = float(((y - ybar) ** 2).sum())
    t = slope_t_statistics(model, periods)
    return {"n": n, "p": p,
            "cv_rmse": math.sqrt(sse / (n - p)) / ybar,
            "nmbe": float(resid.sum()) / ((n - p) * ybar),
            "r2": 1 - sse / sst if sst > 0 else 0.0,
            "slope_t": t,
            "min_abs_slope_t": min(abs(x) for x in t) if t else None,
            "whole_year_baseline": n in WHOLE_YEAR_PERIODS}


def _grid(T: np.ndarray, step: float) -> np.ndarray:
    lo, hi = np.percentile(T, 10), np.percentile(T, 90)
    return np.arange(math.floor(lo), math.ceil(hi) + step, step)


def fit_form(form: str, periods: Sequence[Period], step: float = 1.0) -> Optional[Model]:
    T = np.array([p.mean_temp for p in periods])
    y = np.array([p.rate for p in periods])
    w = np.array([p.days for p in periods])
    if form in ("mean", "2P"):
        m = Model(form, [], [])
        m.coef = list(_wls(m.design(T), y, w))
        return m
    best, best_sse = None, math.inf
    grid = _grid(T, step)
    candidates = ([[a, b] for a in grid for b in grid if b > a] if form == "5P"
                  else [[c] for c in grid])
    for cps in candidates:
        m = Model(form, [], cps)
        X = m.design(T)
        if np.linalg.matrix_rank(X) < X.shape[1]:
            continue
        coef = _wls(X, y, w)
        if not _valid(form, coef):
            continue
        r = y - X @ coef
        sse = float((w * r * r).sum())
        if sse < best_sse:
            best_sse, best = sse, Model(form, list(coef), cps)
    return best


def _significant(s: Dict[str, object], min_slope_t: float) -> bool:
    t = s["min_abs_slope_t"]
    return t is None or t > min_slope_t


def fit_baseline(periods: Sequence[Period], forms: Sequence[str] = MODEL_FORMS,
                 force: Optional[str] = None, min_slope_t: float = 2.0) -> Dict[str, object]:
    """Fit candidate forms; return the selected model and a comparison table.

    Preference order: models whose slopes are all significant (|t| > min_slope_t),
    then lowest CV(RMSE). The mean model has no slopes and counts as significant.
    """
    table, fits = [], []
    for form in ([force] if force else forms):
        if len(periods) <= N_PARAMS[form]:
            continue
        m = fit_form(form, periods)
        if m is None:
            continue
        s = fit_statistics(m, periods)
        s["slopes_significant"] = _significant(s, min_slope_t)
        table.append({"form": form, **s, "equation": m.equation()})
        fits.append((m, s))
    if not fits:
        raise ValueError("no valid baseline model could be fitted")
    pool = [f for f in fits if f[1]["slopes_significant"]] or fits
    selected = min(pool, key=lambda f: f[1]["cv_rmse"])
    return {"model": selected[0], "statistics": selected[1], "candidates": table}


def avoided_energy(model: Model, baseline: Sequence[Period], reporting: Sequence[Period],
                   confidence: float = 0.90) -> Dict[str, object]:
    stats = fit_statistics(model, baseline)
    adjusted = model.predict_energy(reporting)
    actual = np.array([p.energy for p in reporting])
    adj_total, act_total = float(adjusted.sum()), float(actual.sum())
    saved = adj_total - act_total
    F = saved / adj_total if adj_total else 0.0
    n, m = stats["n"], len(reporting)
    t = t_critical(confidence, n - stats["p"])
    fsu = (t * 1.26 * stats["cv_rmse"] / F * math.sqrt((n + 2) / (n * m))) if F > 0 else None
    return {
        "option": "C",
        "model_form": model.form,
        "model_equation": model.equation(),
        "baseline_statistics": stats,
        "reporting_periods": m,
        "reporting_days": float(sum(p.days for p in reporting)),
        "adjusted_baseline": adj_total,
        "reporting_actual": act_total,
        "avoided_energy": saved,
        "fractional_savings": F,
        "confidence": confidence,
        "fractional_savings_uncertainty": fsu,
        "absolute_uncertainty": abs(fsu * saved) if fsu is not None else None,
        "by_period": [{"period": p.label, "adjusted_baseline": float(a), "actual": p.energy,
                        "savings": float(a) - p.energy} for p, a in zip(reporting, adjusted)],
    }


def check_acceptance(result: Dict[str, object], criteria: Dict[str, object]) -> Dict[str, object]:
    """Compare a result with configurable acceptance criteria (see config/).

    Checks count toward all_pass. Warnings (whole-year baseline) do not, because
    FEMP v5.0 states it as good practice ("it is best to"), not a requirement.
    """
    s = result["baseline_statistics"]
    t = s.get("min_abs_slope_t")
    fsu = result.get("fractional_savings_uncertainty")
    checks = {
        "r2": s["r2"] >= criteria["min_r2"],
        "nmbe": abs(s["nmbe"]) <= criteria["max_abs_nmbe"],
        "slope_t": t is None or t > criteria["min_abs_slope_t"],
        "cv_rmse": s["cv_rmse"] <= criteria["max_cv_rmse"],
        "fsu": fsu is not None and fsu <= criteria["max_fsu"],
    }
    warnings = []
    if not s.get("whole_year_baseline", True):
        warnings.append(f"Baseline has {s['n']} periods; FEMP v5.0 Section 4.4 recommends "
                        "whole-year sets (12, 24, 36, or 48 months).")
    return {"checks": checks, "all_pass": all(checks.values()), "warnings": warnings,
            "criteria": {k: v for k, v in criteria.items() if not k.startswith("_")}}
