"""Life-cycle cost analysis consistent with ASTM E917 and NIST Handbook 135.

All amounts are in constant (real) base-year dollars and are discounted with a
real discount rate. Cash flows use the end-of-year convention by default, as
in NIST Handbook 135; a mid-year convention is available for recurring costs.

Equations (d = real discount rate, t = year, n = study period in years):

    SPV(t, d)        = 1 / (1 + d) ** t
    UPV(n, d)        = (1 - (1 + d) ** -n) / d
    UPV*(n, d, e)    = sum_{t=1..n} ((1 + e) / (1 + d)) ** t
    LCC              = PV(initial) + PV(replacements) - PV(residual)
                       + PV(energy) + PV(water) + PV(OM&R)
    NS               = LCC_base - LCC_alt
    SIR              = (PV operational savings) / (PV added investment)
    AIRR             = (1 + d) * SIR ** (1 / n) - 1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

FEMP_2025 = {
    "real_discount_rate": 0.030,
    "nominal_discount_rate": 0.045,
    "implied_inflation_rate": 0.015,
    "max_study_period_years": 40,
    "source": "NIST IR 85-3273-40 (August 2025), Annual Supplement to NIST Handbook 135",
}


# ---------------------------------------------------------------- factors

def spv(t: float, d: float) -> float:
    """Single present value factor for an amount occurring at year t."""
    if d <= -1:
        raise ValueError("discount rate must be greater than -100 percent")
    return 1.0 / (1.0 + d) ** t


def upv(n: int, d: float) -> float:
    """Uniform present value factor for a constant annual amount, years 1..n."""
    if n < 0:
        raise ValueError("study period must be non-negative")
    if d == 0:
        return float(n)
    return (1.0 - (1.0 + d) ** -n) / d


def upv_star(n: int, d: float, e: float = 0.0, midyear: bool = False) -> float:
    """Modified UPV factor for an annual amount escalating at constant real rate e."""
    shift = 0.5 if midyear else 0.0
    return sum((1.0 + e) ** t / (1.0 + d) ** (t - shift) for t in range(1, n + 1))


def upv_index(indices: Sequence[float], d: float, midyear: bool = False) -> float:
    """Modified UPV factor from a year-by-year price index series.

    indices[0] is the multiplier for year 1, relative to base-year price 1.0.
    Use this with the FEMP/NIST energy price indices for a given region,
    sector, and fuel.
    """
    shift = 0.5 if midyear else 0.0
    return sum(idx / (1.0 + d) ** (t - shift) for t, idx in enumerate(indices, start=1))


# ---------------------------------------------------------------- inputs

@dataclass
class AnnualCost:
    """A cost that recurs every year of the study period after occupancy."""

    name: str
    amount: float                 # base-year dollars per year
    category: str = "omr"         # "energy", "water", or "omr"
    escalation: float = 0.0       # constant real escalation rate
    indices: Optional[List[float]] = None   # overrides escalation if given

    def present_value(self, n: int, d: float, midyear: bool = False) -> float:
        if self.indices is not None:
            idx = list(self.indices)[:n]
            if len(idx) < n:
                raise ValueError(f"{self.name}: price index series shorter than study period")
            return self.amount * upv_index(idx, d, midyear)
        return self.amount * upv_star(n, d, self.escalation, midyear)


@dataclass
class OneTimeCost:
    """A cost at a single year: replacement, non-annual OM&R, or residual value."""

    name: str
    amount: float
    year: float
    category: str = "replacement"   # "replacement", "omr", or "residual"

    def present_value(self, d: float) -> float:
        return self.amount * spv(self.year, d)


@dataclass
class Alternative:
    name: str
    initial_investment: float
    annual_costs: List[AnnualCost] = field(default_factory=list)
    one_time_costs: List[OneTimeCost] = field(default_factory=list)


@dataclass
class Study:
    study_period_years: int
    real_discount_rate: float = FEMP_2025["real_discount_rate"]
    midyear: bool = False

    def __post_init__(self):
        if not 1 <= self.study_period_years <= FEMP_2025["max_study_period_years"]:
            raise ValueError("study period must be between 1 and 40 years (FEMP maximum)")


# ---------------------------------------------------------------- results

def lcc(alt: Alternative, study: Study) -> Dict[str, float]:
    """Present-value breakdown and total LCC for one alternative."""
    n, d = study.study_period_years, study.real_discount_rate
    out = {"initial": float(alt.initial_investment), "replacement": 0.0, "residual": 0.0,
           "energy": 0.0, "water": 0.0, "omr": 0.0}
    for c in alt.annual_costs:
        if c.category not in ("energy", "water", "omr"):
            raise ValueError(f"{c.name}: unknown annual category {c.category}")
        out[c.category] += c.present_value(n, d, study.midyear)
    for c in alt.one_time_costs:
        if c.year > n:
            continue   # outside the study period
        if c.category == "residual":
            out["residual"] += c.present_value(d)
        elif c.category == "replacement":
            out["replacement"] += c.present_value(d)
        elif c.category == "omr":
            out["omr"] += c.present_value(d)
        else:
            raise ValueError(f"{c.name}: unknown one-time category {c.category}")
    out["investment_related"] = out["initial"] + out["replacement"] - out["residual"]
    out["operational"] = out["energy"] + out["water"] + out["omr"]
    out["total"] = out["investment_related"] + out["operational"]
    return out


def compare(base: Alternative, alt: Alternative, study: Study) -> Dict[str, Optional[float]]:
    """Supplementary measures for an alternative relative to a base case."""
    b, a = lcc(base, study), lcc(alt, study)
    n, d = study.study_period_years, study.real_discount_rate
    added_investment = a["investment_related"] - b["investment_related"]
    operational_savings = b["operational"] - a["operational"]
    ns = b["total"] - a["total"]
    sir = operational_savings / added_investment if added_investment > 0 else None
    airr = (1.0 + d) * sir ** (1.0 / n) - 1.0 if sir is not None and sir > 0 else None
    spb, dpb = _paybacks(base, alt, study)
    return {"lcc_base": b["total"], "lcc_alt": a["total"], "net_savings": ns,
            "added_investment_pv": added_investment, "operational_savings_pv": operational_savings,
            "sir": sir, "airr": airr, "simple_payback_years": spb,
            "discounted_payback_years": dpb, "cost_effective": ns > 0}


def _annual_operational(alt: Alternative, year: int) -> float:
    total = 0.0
    for c in alt.annual_costs:
        if c.indices is not None:
            total += c.amount * c.indices[year - 1]
        else:
            total += c.amount * (1.0 + c.escalation) ** year
    for c in alt.one_time_costs:
        if c.category in ("replacement", "omr") and int(round(c.year)) == year:
            total += c.amount
    return total


def _paybacks(base: Alternative, alt: Alternative, study: Study):
    """Simple and discounted payback in years, interpolated within the crossing year."""
    n, d = study.study_period_years, study.real_discount_rate
    invest = alt.initial_investment - base.initial_investment
    if invest <= 0:
        return 0.0, 0.0
    cum_s = cum_d = 0.0
    spb = dpb = None
    for t in range(1, n + 1):
        saving = _annual_operational(base, t) - _annual_operational(alt, t)
        if spb is None:
            prev = cum_s
            cum_s += saving
            if cum_s >= invest and saving > 0:
                spb = t - 1 + (invest - prev) / saving
        if dpb is None:
            disc = saving * spv(t, d)
            prev = cum_d
            cum_d += disc
            if cum_d >= invest and disc > 0:
                dpb = t - 1 + (invest - prev) / disc
    return spb, dpb


def alternative_from_dict(data: dict) -> Alternative:
    return Alternative(
        name=data["name"],
        initial_investment=float(data.get("initial_investment", 0.0)),
        annual_costs=[AnnualCost(**c) for c in data.get("annual_costs", [])],
        one_time_costs=[OneTimeCost(**c) for c in data.get("one_time_costs", [])],
    )
