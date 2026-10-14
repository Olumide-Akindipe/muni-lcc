# Build specification

*Plain-language header: this is the one-page plan the toolkit was built from. You do not need to open it unless you want to check that the build matches what was planned. The plain version is in START_HERE.md.*

```
PROJECT:        MUNI-LCC v0.1.0. Archetype: pipeline or tool (Python package),
                with a software paper (JOSS) stacked on top.

QUESTION:       Did a municipal energy project save what it promised, and was it
                worth the money over its life, reported in the form federal
                grant performance reports require?

SOURCES (methods, not data):
  1. DOE FEMP, M&V Guidelines: Measurement and Verification for Performance-Based
     Contracts, Version 5.0 (September 2024), prepared by PNNL.
     https://www.energy.gov/sites/default/files/2024-10/mv_guide_5_0.pdf
     Public domain (US Government work). Accessed 2026-10-12.
  2. EVO, International Performance Measurement and Verification Protocol (IPMVP),
     Core Concepts 2022 (EVO 10000-1:2022). FEMP v5.0 states it is a specific
     application of this edition. Options A and C implemented as defined in
     FEMP v5.0; no EVO text reproduced. FEMP v5.0 also cites EVO 10100-1:2018
     (Uncertainty Assessment) for savings uncertainty.
  3. ASTM E917-17(2023), Standard Practice for Measuring Life-Cycle Costs of
     Buildings and Building Systems. Paywalled standard. Equations implemented
     from the equivalent public formulation in NIST Handbook 135 (Fuller and
     Petersen, 1996) and its Annual Supplement.
  4. NIST IR 85-3273-40, Energy Price Indices and Discount Factors for Life-Cycle
     Cost Analysis, 2025 (August 2025). FEMP real discount rate 3.0 percent,
     nominal 4.5 percent, implied inflation 1.5 percent, maximum study period
     40 years. https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.85-3273-40.pdf
  5. 2 CFR 200.329, Monitoring and reporting program performance, as amended
     89 FR 30136 (April 22, 2024). eCFR current as of 2026-10-08.
     https://www.ecfr.gov/current/title-2/section-200.329
  6. ASHRAE Guideline 14-2023, Measurement of Energy, Demand, and Water Savings (edition cited by FEMP v5.0).
     Paywalled. Used only for the published fractional savings uncertainty
     approximation and model fit statistics; thresholds are user configurable.

UNIT:           One project (a facility measure or bundle of measures) per run.

MEASURES:
  LCC           Present value of initial, replacement, residual, energy, water,
                and OM&R costs over the study period (end-of-year convention,
                constant dollars, real discount rate).
  NS, SIR, AIRR, SPB, DPB   Supplementary measures versus a base case.
  Option A      Savings = (measured baseline key parameter minus measured
                post parameter) x stipulated parameter, with root-sum-square
                uncertainty.
  Option C      Whole-meter regression baseline (mean, 2P, 3PC, 3PH, 4P, 5P),
                avoided energy use = adjusted baseline minus reporting use,
                CV(RMSE), NMBE, R-squared, fractional savings uncertainty.
  Report        Accomplishments versus objectives, reasons for shortfalls,
                cost and unit-cost analysis, report due dates, per
                2 CFR 200.329(c)(1), (c)(2), and (e).

OUTPUTS:        src/muni_lcc (package), CLI `muni-lcc`, tests/, examples/ with a
                synthetic worked example, examples/outputs/stats.json,
                performance report in Markdown and JSON, docs/, paper/paper.md.

VENUES:         GitHub release, Zenodo DOI, then JOSS (after 6 months of public
                history, per JOSS norms), then PyPI.

VERIFY POINTS:  See docs/VERIFY_CHECKLIST.md Part 4: discount rate vintage,
                Option C acceptance thresholds, confidence level, timing
                convention, example data being synthetic.

LICENSE:        Code MIT. Documentation CC BY 4.0.

ASSUMPTIONS:    Author block taken from the author's stated ORCID and name form.
                No real utility data is published; the worked example is
                synthetic with a known injected savings value so the method
                can be checked against a known answer.
```
