import math

import pytest

from muni_lcc import lcc as L


def test_spv_upv_closed_form():
    assert L.spv(10, 0.03) == pytest.approx(0.744094, abs=1e-6)
    assert L.upv(10, 0.03) == pytest.approx(8.530203, abs=1e-6)
    assert L.upv(25, 0.03) == pytest.approx(17.413148, abs=1e-6)
    assert L.upv(5, 0.0) == 5


def test_upv_star_reduces_to_upv_and_to_n():
    assert L.upv_star(20, 0.03, 0.0) == pytest.approx(L.upv(20, 0.03))
    assert L.upv_star(20, 0.03, 0.03) == pytest.approx(20.0)


def test_upv_index_matches_constant_escalation():
    e, d, n = 0.01, 0.03, 15
    idx = [(1 + e) ** t for t in range(1, n + 1)]
    assert L.upv_index(idx, d) == pytest.approx(L.upv_star(n, d, e))


def test_lcc_hand_calculation():
    alt = L.Alternative("x", 10_000,
                        [L.AnnualCost("elec", 1_000, "energy"), L.AnnualCost("maint", 200, "omr")],
                        [L.OneTimeCost("lamp swap", 2_000, 10, "replacement"),
                         L.OneTimeCost("salvage", 500, 20, "residual")])
    r = L.lcc(alt, L.Study(20, 0.03))
    expected = (10_000 + 2_000 * L.spv(10, 0.03) - 500 * L.spv(20, 0.03)
                + 1_200 * L.upv(20, 0.03))
    assert r["total"] == pytest.approx(expected)


def test_compare_identities():
    base = L.Alternative("base", 0, [L.AnnualCost("elec", 5_000, "energy")])
    alt = L.Alternative("led", 10_000, [L.AnnualCost("elec", 2_500, "energy")])
    st = L.Study(15, 0.03)
    c = L.compare(base, alt, st)
    pv_sav = 2_500 * L.upv(15, 0.03)
    assert c["net_savings"] == pytest.approx(pv_sav - 10_000)
    assert c["sir"] == pytest.approx(pv_sav / 10_000)
    assert c["airr"] == pytest.approx(1.03 * c["sir"] ** (1 / 15) - 1)
    assert c["simple_payback_years"] == pytest.approx(4.0)
    # discounted payback is longer than simple payback when d > 0
    assert c["discounted_payback_years"] > 4.0
    # NS > 0 iff SIR > 1 iff AIRR > d
    assert (c["net_savings"] > 0) == (c["sir"] > 1) == (c["airr"] > 0.03)


def test_study_period_limit():
    with pytest.raises(ValueError):
        L.Study(41)


def test_cost_beyond_study_period_ignored():
    alt = L.Alternative("x", 0, [], [L.OneTimeCost("late", 1_000, 30, "replacement")])
    assert L.lcc(alt, L.Study(20, 0.03))["total"] == 0
