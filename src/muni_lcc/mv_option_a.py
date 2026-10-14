"""IPMVP Option A: retrofit isolation, key parameter measurement.

As defined in DOE FEMP M&V Guidelines v5.0 (September 2024), which apply
IPMVP Core Concepts 2022 (EVO 10000-1:2022).

Under Option A, the key performance parameter that defines the measure's
energy use (for example connected lighting kW) is measured before and after
the retrofit, and other parameters (for example annual operating hours) are
stipulated from documented estimates. FEMP M&V Guidelines v5.0 require the
M&V plan to say which parameters are measured and which are stipulated, and
to justify the stipulated values. This module records that distinction in
its output so it cannot be lost.

    Savings = (P_baseline - P_reporting) x H x IF

where P is the measured key parameter (mean of field readings), H is the
stipulated parameter, and IF is an optional interactive-effects factor
(1.0 when not applied).

Uncertainty is propagated by root-sum-square of relative standard errors on
the measured terms, at the requested confidence level. Stipulated values are
treated as exact here by design: their uncertainty is a matter of agreement,
not measurement, and the report flags them for that reason.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Dict, List, Optional

from .stats import t_critical


@dataclass
class MeasuredParameter:
    name: str
    readings: List[float]
    units: str

    @property
    def value(self) -> float:
        return mean(self.readings)

    @property
    def standard_error(self) -> float:
        if len(self.readings) < 2:
            return 0.0
        return stdev(self.readings) / math.sqrt(len(self.readings))


@dataclass
class StipulatedParameter:
    name: str
    value: float
    units: str
    basis: str   # documentation for the stipulation, required by FEMP v5.0

    def __post_init__(self):
        if not self.basis or not self.basis.strip():
            raise ValueError(f"stipulated parameter {self.name} needs a documented basis")


@dataclass
class OptionAMeasure:
    name: str
    baseline: MeasuredParameter
    reporting: MeasuredParameter
    stipulated: StipulatedParameter
    interactive_factor: float = 1.0
    savings_units: str = "kWh/yr"
    notes: List[str] = field(default_factory=list)


def savings(m: OptionAMeasure, confidence: float = 0.90) -> Dict[str, object]:
    pb, pr = m.baseline.value, m.reporting.value
    delta = pb - pr
    s = delta * m.stipulated.value * m.interactive_factor
    # Standard error of the difference of two independent means.
    se_delta = math.sqrt(m.baseline.standard_error ** 2 + m.reporting.standard_error ** 2)
    dof = max(len(m.baseline.readings) + len(m.reporting.readings) - 2, 1)
    t = t_critical(confidence, dof)
    abs_unc = abs(t * se_delta * m.stipulated.value * m.interactive_factor)
    rel_unc: Optional[float] = abs_unc / abs(s) if s != 0 else None
    return {
        "measure": m.name,
        "option": "A",
        "baseline_key_parameter": {"name": m.baseline.name, "mean": pb, "units": m.baseline.units,
                                    "n": len(m.baseline.readings)},
        "reporting_key_parameter": {"name": m.reporting.name, "mean": pr, "units": m.reporting.units,
                                     "n": len(m.reporting.readings)},
        "stipulated_parameter": {"name": m.stipulated.name, "value": m.stipulated.value,
                                 "units": m.stipulated.units, "basis": m.stipulated.basis},
        "interactive_factor": m.interactive_factor,
        "baseline_annual": pb * m.stipulated.value * m.interactive_factor,
        "reporting_annual": pr * m.stipulated.value * m.interactive_factor,
        "savings": s,
        "savings_units": m.savings_units,
        "confidence": confidence,
        "absolute_uncertainty": abs_unc,
        "relative_uncertainty": rel_unc,
        "uncertainty_note": "Measurement uncertainty only. Stipulated parameter treated as exact by agreement.",
    }
