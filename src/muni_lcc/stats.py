"""Small statistics helpers with no dependency beyond the standard library.

t_critical returns the two-sided Student t critical value. It uses a
Cornish-Fisher expansion of the normal quantile, accurate to about 0.01 for
3 or more degrees of freedom, which is well inside M&V reporting precision.
Tests compare it with published table values.
"""

from __future__ import annotations

import math
from statistics import NormalDist


def t_critical(confidence: float, dof: int) -> float:
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    if dof < 1:
        raise ValueError("degrees of freedom must be at least 1")
    p = 1 - (1 - confidence) / 2
    z = NormalDist().inv_cdf(p)
    if dof == 1:
        return math.tan(math.pi * (p - 0.5))
    if dof == 2:
        a = 2 * p - 1
        return a * math.sqrt(2 / (1 - a * a))
    n = dof
    g1 = (z ** 3 + z) / 4
    g2 = (5 * z ** 5 + 16 * z ** 3 + 3 * z) / 96
    g3 = (3 * z ** 7 + 19 * z ** 5 + 17 * z ** 3 - 15 * z) / 384
    g4 = (79 * z ** 9 + 776 * z ** 7 + 1482 * z ** 5 - 1920 * z ** 3 - 945 * z) / 92160
    return z + g1 / n + g2 / n ** 2 + g3 / n ** 3 + g4 / n ** 4
