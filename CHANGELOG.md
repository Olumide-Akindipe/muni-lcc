# Changelog

All notable changes to MUNI-LCC are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## 0.1.1 (2026-10-30)

### Changed
- Option C model selection uses the Schwarz information criterion (BIC) among physically valid fits with significant slopes, instead of lowest CV(RMSE). In Monte Carlo tests on the worked example's data-generating process, the CV(RMSE) rule selected a spurious 4P or 5P model in about 23 percent of replications, which lowered the coverage of the stated uncertainty in those cases. The worked example's selected model and every published number are unchanged.

### Fixed
- Option C now reports the absolute savings uncertainty when estimated savings are zero or negative. It is independent of the savings, so it is well defined; v0.1.0 returned no uncertainty in that case. FSU is still reported only for positive savings, and the FSU acceptance check fails otherwise.

### Added
- `preprint/`: manuscript source, validation and sensitivity scripts, and their outputs for the MUNI-LCC preprint.
- Tests for both changes.
- PyPI distribution: `pip install muni-lcc`. A GitHub Actions workflow publishes each GitHub release to PyPI.

### Fixed (packaging and CI)
- Package metadata uses an SPDX license expression, as current setuptools requires.
- Test workflow pinned to Ubuntu 24.04, because Python 3.9 builds are not published for the newer default runner; GitHub Actions updated to versions that run on Node.js 24.

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
