---
title: 'MUNI-LCC: an open Python toolkit for life-cycle cost analysis, measurement and verification, and federal performance reporting of municipal energy projects'
tags:
  - Python
  - energy efficiency
  - measurement and verification
  - life-cycle cost analysis
  - public finance
  - performance reporting
authors:
  - name: Stephen Olumide Akindipe
    orcid: 0000-0002-1846-9662
    affiliation: 1
affiliations:
  - name: Independent Researcher, Albany, NY, USA
    index: 1
date: '14 October 2026'
bibliography: paper.bib
---

# Summary

MUNI-LCC is a Python package that applies the federal methods for verifying and valuing energy savings to projects conducted in small and mid-sized municipalities. It implements life-cycle cost analysis consistent with ASTM E917 and NIST Handbook 135 [@astm_e917; @fuller1996], Options A and C of the International Performance Measurement and Verification Protocol (IPMVP) as defined in the U.S. Department of Energy Federal Energy Management Program (FEMP) M&V Guidelines Version 5.0, which are based on IPMVP Core Concepts 2022 [@femp2024; @evo_ipmvp], and the program performance reporting elements of the federal Uniform Guidance at 2 CFR 200.329 as amended in 2024 [@cfr200329]. Verified quantities flow directly into the life-cycle cost analysis, so the cost-effectiveness reported to a project sponsor or funding agency is sourced from metered savings rather than estimated projections.

# Statement of need

Federal and state programs fund many energy upgrades in municipal buildings. Recipients must report project performance and accomplishments against award objectives, explain shortfalls, and analyze cost overruns and unit costs [@cfr200329]. Federal agencies satisfy comparable obligations through performance contracts with prescribed M&V [@femp2024]. Small and mid-sized municipalities often lack the qualified personnel and software to fulfill these obligations. As a result, they report engineering estimates instead of measured savings. Open tools exist for parts of this workflow, including whole-building regression baselines, but they do not connect verification to life-cycle cost metrics and to the content of a federal performance report. MUNI-LCC provides that connection in a compact, tested package with one input file and one command.

# State of the field

Four groups of open or freely available tools overlap with parts of this workflow. NIST's Building Life-Cycle Cost program (BLCC) compares the cost effectiveness of building alternatives under the FEMP life-cycle cost rules; NIST announced that its web version would replace the desktop application in spring 2026 [@blcc], and its Economic Evaluation Engine (E3) exposes life-cycle and benefit-cost analysis through an API and a public GitHub repository [@e3]. Neither is documented as estimating savings from metered data. OpenEEmeter (`eemeter`), an Apache-2.0 Python package, implements the CalTRACK daily, billing, and hourly methods and reports metered savings with error bands [@eemeter]. `nmecr`, an MIT-licensed R package from kW Labs, implements change-point, time-of-week-and-temperature, and degree-day models with ASHRAE Guideline 14-2014 uncertainty and normalized savings [@nmecr]. LBNL's `RMV2.0` is an R package with a browser interface for baseline modeling, savings estimation, and non-routine event screening on smart meter data [@rmv2]. None of these is documented as linking verified savings to life-cycle cost metrics or to the content of a federal performance report.

On build versus contribute: the gap MUNI-LCC fills sits between these tools rather than inside any one of them. The M&V packages target savings estimation and the cost tools target design-stage economics. Adding grant-reporting logic to an M&V library, or metered regression to a cost engine, would extend each beyond its stated scope. MUNI-LCC instead implements the FEMP v5.0 definitions of Options A and C directly, so each acceptance value can be traced to a section of that document, and keeps its interfaces small enough that a future version could call `eemeter` or E3 for the steps they cover.

# Software design

The design follows from the intended user, a municipal staff member without a statistics or software background, and from the audit trail a funder may ask for.

* **One input file, one command.** A project is a single JSON file; `muni-lcc run` writes results and the report. The only runtime dependency is NumPy.
* **Traceable thresholds.** Acceptance criteria live in a configuration file in which every value names its source: FEMP v5.0 Section 5.3.4.1 for R-squared (0.75), net determination bias (0.005 percent), and slope t-statistics (greater than 2.0), and LBNL guidance [@lbnl2017] for CV(RMSE) and fractional savings uncertainty, for which FEMP states no value. FEMP's calibration tolerances for Option D (Table 4-2) were deliberately not applied to Option C.
* **Physically constrained models.** Option C fits change-point models by days-weighted least squares, which makes net determination bias zero by construction. Change points are found by grid search, fits with implausible slope signs are rejected, and models whose slopes are all significant are preferred before CV(RMSE) is compared. In the worked example this rule rejects the four- and five-parameter fits, whose added slopes have t-statistics of 0.7 and 0.1.
* **Stipulations must be documented.** An Option A stipulated value without a written basis is refused, reflecting the FEMP requirement that the M&V plan justify stipulations.
* **Verified quantities drive cost.** Annual energy quantities in the life-cycle cost study can be drawn from Option A or Option C results instead of projections.
* **Reports that list what is missing.** The report module computes the 200.329(c)(1) due date, compares each objective with its verified result, and lists every explanation 200.329(c)(2) or (e) requires but the user has not supplied.
* **Text that cannot drift from results.** The README and this paper are rendered from a statistics file written by the worked example, and continuous integration fails if the example no longer reproduces those numbers.

Uncertainty uses the ASHRAE Guideline 14 approximation for monthly models [@ashrae14]. FEMP v5.0 also cites EVO 10100-1:2018 [@evo_uncertainty], which is planned for a later release; the documentation states this choice and its limits.

# Research impact statement

<!-- Update before submission: add the validation report DOI, any external users, issues, or citations. -->

MUNI-LCC is at an early stage of use. The evidence available at release is reproducibility rather than adoption. A synthetic worked example with a known injected savings value is included: the package recovers 6,879 therms of avoided gas use against a true value of 6,629 therms, within a fractional savings uncertainty of 34.2 percent at 90 percent confidence, using a 3PH baseline with CV(RMSE) of 7.9 percent. The 33 automated tests include closed-form checks of present-value factors, exact recovery of a known change-point model, and due dates for every reporting frequency. Every release is archived on Zenodo with a DOI. The package is a component of the author's broader work on decision support for municipal energy investment, alongside a planning tool and a public register of verification requirements in federal and New York State programs.

# AI usage disclosure

Generative AI was used in this work. The tool was Claude (Anthropic), model Claude Opus 5.5 (claude-opus-5-5), used through Anthropic's Claude application in October 2026. It was applied to: writing the Python source code, automated tests, and continuous integration workflow; drafting the documentation (README, methods, limitations, input reference, verification checklist, support and governance files); summarizing the public documentation of the tools compared in State of the field; and drafting this paper. The author selected the methods and their sources, made every analytic decision recorded in `docs/VERIFY_CHECKLIST.md` (including acceptance criteria checked against the FEMP v5.0 text), rewrote the Summary and Statement of need, re-ran the test suite and worked example, checked the worked-example results by hand against the source documents, and reviewed and validated all AI-generated code, documentation, and text before release.

# Acknowledgements

No financial support was received for this work.

# References
