# Changelog

All notable changes to MUNI-LCC are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## 0.1.0 (2026-10-14)

First public release.

### Added
- Life-cycle cost module consistent with ASTM E917, using NIST Handbook 135 factors: SPV, UPV, modified UPV with constant escalation or price index series; LCC by category; net savings, SIR, AIRR, simple and discounted payback.
- IPMVP Option A module as defined in FEMP M&V Guidelines v5.0: key parameter savings, mandatory documented basis for stipulated values, measurement uncertainty.
- IPMVP Option C module as defined in FEMP M&V Guidelines v5.0: mean, 2P, 3PC, 3PH, 4P, and 5P change-point baselines; CV(RMSE), NMBE, R-squared, slope t-statistics; avoided energy use; ASHRAE Guideline 14 fractional savings uncertainty approximation.
- Acceptance criteria file with a source for each value: FEMP v5.0 Section 5.3.4.1 for R-squared, net determination bias, and t-statistic; LBNL (2017) guidance for CV(RMSE) and FSU; whole-year baseline warning per FEMP v5.0 Section 4.4.
- Performance report content under 2 CFR 200.329(c)(1), (c)(2), and (e) as amended in April 2024, with a completeness check.
- Verified M&V quantities can feed the life-cycle cost analysis directly.
- Command line interface `muni-lcc`.
- Synthetic worked example with a known answer; automated tests; continuous integration that re-runs the example and checks the published numbers.
