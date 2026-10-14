"""End to end: the synthetic example recovers its known answer."""

import json
import os

from muni_lcc import pipeline

ROOT = os.path.join(os.path.dirname(__file__), "..", "examples")


def test_example_recovers_truth():
    res = pipeline.run(os.path.join(ROOT, "project.json"))
    with open(os.path.join(ROOT, "data", "TRUTH.json"), encoding="utf-8") as f:
        truth = json.load(f)
    c = res["option_c"]
    assert abs(c["avoided_energy"] - truth["true_avoided_therms"]) <= c["absolute_uncertainty"]
    assert c["acceptance"]["all_pass"]
    assert round(res["option_a"][0]["savings"]) == round(truth["true_lighting_savings_kwh"])
    assert res["lcc"]["net_savings"] > 0
    assert res["report"]["completeness_issues"] == []
    assert res["report"]["due_date"] == "2026-03-31"
