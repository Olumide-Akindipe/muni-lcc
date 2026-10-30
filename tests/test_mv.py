import numpy as np
import pytest

from muni_lcc import mv_option_a as A
from muni_lcc import mv_option_c as C
from muni_lcc.stats import t_critical


@pytest.mark.parametrize("conf,dof,table", [
    (0.90, 1, 6.314), (0.90, 2, 2.920), (0.90, 5, 2.015), (0.90, 10, 1.812),
    (0.95, 20, 2.086), (0.80, 12, 1.356), (0.68, 30, 1.01),
])
def test_t_critical_against_tables(conf, dof, table):
    assert t_critical(conf, dof) == pytest.approx(table, abs=0.012)


def test_option_a_lighting():
    m = A.OptionAMeasure(
        "LED", A.MeasuredParameter("fixture kW", [10.0, 10.0, 10.0], "kW"),
        A.MeasuredParameter("fixture kW", [4.0, 4.0, 4.0], "kW"),
        A.StipulatedParameter("hours", 3_000, "h/yr", "posted schedule"))
    r = A.savings(m)
    assert r["savings"] == pytest.approx(18_000)
    assert r["absolute_uncertainty"] == 0


def test_option_a_requires_stipulation_basis():
    with pytest.raises(ValueError):
        A.StipulatedParameter("hours", 3_000, "h/yr", " ")


def _periods(T, rate_fn, days=30.0, scale=1.0, noise=None):
    out = []
    for i, t in enumerate(T):
        r = rate_fn(t) * scale + (noise[i] if noise is not None else 0.0)
        out.append(C.Period(f"p{i}", days, r * days, t))
    return out


TEMPS = [22, 25, 34, 47, 58, 67, 72, 70, 62, 50, 39, 28]


def heating(t):   # 3PH: base 1000 kWh/day, 40 kWh/day per degree below 55
    return 1000 + 40 * max(55 - t, 0)


def test_option_c_recovers_known_3ph_model():
    base = _periods(TEMPS, heating)
    fit = C.fit_baseline(base, forms=["3PH"])
    m = fit["model"]
    assert m.change_points[0] == pytest.approx(55)
    assert m.coef[0] == pytest.approx(1000, rel=1e-9)
    assert m.coef[1] == pytest.approx(40, rel=1e-9)
    assert fit["statistics"]["cv_rmse"] == pytest.approx(0, abs=1e-9)


def test_option_c_recovers_injected_savings_noiseless():
    base = _periods(TEMPS, heating)
    rep = _periods([t + 3 for t in TEMPS], heating, scale=0.88)
    fit = C.fit_baseline(base)
    res = C.avoided_energy(fit["model"], base, rep)
    assert res["fractional_savings"] == pytest.approx(0.12, abs=1e-6)


def test_option_c_noisy_savings_within_uncertainty():
    rng = np.random.default_rng(42)
    base = _periods(TEMPS + TEMPS, heating, noise=rng.normal(0, 25, 24))
    rep = _periods(TEMPS, heating, scale=0.88, noise=rng.normal(0, 25, 12))
    fit = C.fit_baseline(base)
    res = C.avoided_energy(fit["model"], base, rep, confidence=0.90)
    true_saving = 0.12 * sum(heating(t) * 30 for t in TEMPS)
    assert abs(res["avoided_energy"] - true_saving) <= res["absolute_uncertainty"]
    acc = C.check_acceptance(res, {"max_cv_rmse": 0.25, "max_abs_nmbe": 0.00005,
                                   "min_r2": 0.75, "min_abs_slope_t": 2.0, "max_fsu": 0.50})
    assert acc["all_pass"]


def test_nmbe_is_zero_for_weighted_fit_with_intercept():
    rng = np.random.default_rng(1)
    base = _periods(TEMPS, heating, noise=rng.normal(0, 30, 12))
    fit = C.fit_baseline(base)
    assert fit["statistics"]["nmbe"] == pytest.approx(0, abs=1e-9)


CRIT = {"min_r2": 0.75, "max_abs_nmbe": 0.00005, "min_abs_slope_t": 2.0,
        "max_cv_rmse": 0.25, "max_fsu": 0.50}


def test_slope_t_statistic_matches_unweighted_ols_textbook():
    # Equal weights reduce WLS to OLS; compare with the closed-form slope t.
    rng = np.random.default_rng(7)
    T = np.linspace(20, 70, 12)
    rate = 900 - 8 * T + rng.normal(0, 20, 12)
    periods = [C.Period(f"p{i}", 30.0, r * 30.0, t) for i, (t, r) in enumerate(zip(T, rate))]
    m = C.fit_form("2P", periods)
    t_ours = C.slope_t_statistics(m, periods)[0]
    resid = rate - (m.coef[0] + m.coef[1] * T)
    s2 = (resid @ resid) / (12 - 2)
    se = np.sqrt(s2 / ((T - T.mean()) ** 2).sum())
    assert t_ours == pytest.approx(m.coef[1] / se, rel=1e-9)


def test_insignificant_slope_fails_acceptance():
    rng = np.random.default_rng(3)
    flat = _periods(TEMPS + TEMPS, lambda t: 1000.0, noise=rng.normal(0, 60, 24))
    fit = C.fit_baseline(flat, forms=["2P"])
    res = C.avoided_energy(fit["model"], flat, _periods(TEMPS, lambda t: 900.0))
    acc = C.check_acceptance(res, CRIT)
    assert not acc["checks"]["slope_t"] and not acc["all_pass"]


def test_selection_prefers_significant_slopes():
    rng = np.random.default_rng(11)
    base = _periods(TEMPS + TEMPS, heating, noise=rng.normal(0, 25, 24))
    fit = C.fit_baseline(base)
    assert fit["statistics"]["slopes_significant"]


def test_whole_year_warning():
    rng = np.random.default_rng(5)
    base = _periods(TEMPS + TEMPS[:6], heating, noise=rng.normal(0, 25, 18))
    fit = C.fit_baseline(base)
    res = C.avoided_energy(fit["model"], base, _periods(TEMPS, heating, scale=0.9))
    acc = C.check_acceptance(res, CRIT)
    assert not fit["statistics"]["whole_year_baseline"]
    assert acc["warnings"] and "Section 4.4" in acc["warnings"][0]


def test_femp_r2_threshold_is_0_75():
    import json, os
    path = os.path.join(os.path.dirname(__file__), "..", "config", "acceptance_criteria.json")
    with open(path, encoding="utf-8") as f:
        c = json.load(f)
    assert c["min_r2"] == 0.75 and c["max_abs_nmbe"] == 0.00005 and c["min_abs_slope_t"] == 2.0
