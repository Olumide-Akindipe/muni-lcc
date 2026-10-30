import pytest

from muni_lcc import report as R


@pytest.mark.parametrize("end,freq,sub,expected", [
    ("2026-06-30", "annual", False, "2026-09-28"),
    ("2026-03-31", "quarterly", False, "2026-04-30"),
    ("2026-06-30", "semiannual", False, "2026-07-30"),
    ("2026-12-31", "final", False, "2027-04-30"),
    ("2026-12-31", "final", True, "2027-03-31"),
])
def test_due_dates_200_329_c1(end, freq, sub, expected):
    assert R.due_date(end, freq, sub) == expected


def _cfg(reason="", explanation="", dev=None):
    return {
        "award": {"award_id": "X", "agency": "DOE", "recipient": "Town", "project": "P",
                  "period_of_performance_end": "2027-06-30",
                  "reporting_period": {"start": "2025-07-01", "end": "2026-06-30", "frequency": "annual"}},
        "objectives": [{"id": "O1", "description": "cut use", "metric": "avoided energy", "units": "kWh",
                        "target": 100.0, "actual_source": "value", "actual": 80.0,
                        "reason_not_met": reason}],
        "costs": {"budget": 1000.0, "actual_cost": 1200.0, "planned_units": 100.0, "unit": "kWh",
                  "unit_basis_source": "value", "explanation": explanation},
        "significant_developments": dev or [],
    }


def test_completeness_flags_missing_required_content():
    cfg = _cfg(dev=[{"type": "adverse", "summary": "chiller delay"}])
    # unit basis uses the "value" source which reads None; patch actual via objective path
    cfg["costs"]["unit_basis_source"] = "value"
    rep = R.build(cfg, {})
    text = " ".join(rep["completeness_issues"])
    assert "O1" in text and "Cost overrun" in text and "corrective action" in text
    assert rep["status"] == "DRAFT"


def test_complete_report_has_no_issues_and_renders():
    cfg = _cfg("contractor delay", "steel prices",
               [{"type": "adverse", "summary": "delay", "corrective_action": "rebid"}])
    rep = R.build(cfg, {}, final=True)
    assert rep["completeness_issues"] == []
    md = R.to_markdown(rep)
    assert "200.329(c)(2)" in md and "DRAFT" not in md
