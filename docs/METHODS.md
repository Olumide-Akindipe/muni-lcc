# Methods

*Plain-language header: this file lists every equation and convention the toolkit uses, with the source of each. Open it if a reviewer, auditor, or engineer asks exactly how a number was computed.*

## 1. Life-cycle cost (module `lcc`)

Consistent with ASTM E917-17(2023) and the federal formulation in NIST Handbook 135. All amounts are constant (real) base-year dollars discounted at a real rate `d`. Base date is year 0; the default convention places recurring costs at the end of each year, with an optional mid-year convention.

| Quantity | Equation |
|---|---|
| Single present value | SPV(t, d) = 1 / (1 + d)^t |
| Uniform present value | UPV(n, d) = (1 minus (1 + d)^(minus n)) / d |
| Modified UPV, constant escalation e | UPV*(n, d, e) = sum over t = 1..n of ((1 + e) / (1 + d))^t |
| Modified UPV, price index series | UPV* = sum over t of I_t / (1 + d)^t, where I_t is the year t index |
| Life-cycle cost | LCC = initial + PV(replacements) minus PV(residual) + PV(energy) + PV(water) + PV(OM&R) |
| Net savings | NS = LCC_base minus LCC_alternative |
| Savings-to-investment ratio | SIR = PV(operational savings) / PV(added investment) |
| Adjusted internal rate of return | AIRR = (1 + d) x SIR^(1/n) minus 1 |
| Simple payback | Years until cumulative undiscounted savings equal the added initial investment, interpolated within the year |
| Discounted payback | Same, with savings discounted by SPV |

Operational costs are energy, water, and OM&R. Investment-related costs are initial investment plus replacements minus residual value, as in NIST Handbook 135. Costs dated after the study period are excluded. The study period is limited to 40 years, the FEMP maximum under EISA section 441.

Default discount rate: 3.0 percent real, the FEMP rate in NIST IR 85-3273-40 (2025 edition). Municipalities are not bound by the FEMP rate; the rate is an input. `config/femp_discount_rates.json` records the edition used.

Annual cost quantities can be drawn from verified M&V results (`quantity_source` in the project file), so an ex post life-cycle analysis uses measured rather than projected savings.

## IPMVP basis

Options A and C are implemented as defined in the DOE FEMP M&V Guidelines v5.0 (September 2024, prepared by PNNL). FEMP v5.0 describes itself as a specific application of the IPMVP, cites IPMVP Core Concepts 2022 (EVO 10000-1:2022), and states its procedures are fully compatible and consistent with the IPMVP. FEMP federal contract requirements (ESPC deliverables, risk and responsibility matrices, government witnessing) are outside the toolkit's scope. IPMVP adherence is a property of a project's M&V plan and report; the toolkit performs the calculations those documents rely on.

**Confidence level.** Every uncertainty in the toolkit uses the project file's `confidence` value, 90 percent by default. FEMP v5.0 leaves the confidence level to the customer (Table 3-1, item e), sets sampling at a minimum of 80 percent confidence with 20 percent precision (Section 5.3.2), and lists 90/10 or 80/20 in its measure-specific tables (Section 6). The default is the stricter of the two.

## 2. IPMVP Option A (module `mv_option_a`)

Savings = (P_baseline minus P_reporting) x H x IF

* P is the key parameter, the mean of field measurements in each period.
* H is the stipulated parameter. A documented basis is mandatory; the code refuses a stipulation without one, reflecting the FEMP v5.0 requirement that the M&V plan justify stipulated values.
* IF is an optional interactive-effects factor (default 1.0).

Uncertainty: standard error of the difference of two independent means, times the two-sided Student t value at the chosen confidence with n_baseline plus n_reporting minus 2 degrees of freedom, times H x IF. The two standard errors are combined by root-sum-square, the same rule as FEMP v5.0 Equation 5-1 (Section 5.3) for independent error sources. The stipulated parameter is treated as exact by agreement, and the output says so.

## 3. IPMVP Option C (module `mv_option_c`)

**Model.** Energy use per day versus mean outdoor dry-bulb temperature for each billing period, fitted by least squares weighted by period length in days. Forms:

| Form | Equation (E = energy per day, T = mean temperature) | Parameters p |
|---|---|---|
| mean | E = b0 | 1 |
| 2P | E = b0 + b1 T | 2 |
| 3PC | E = b0 + b1 max(T minus cp, 0), b1 > 0 | 3 |
| 3PH | E = b0 + b1 max(cp minus T, 0), b1 > 0 | 3 |
| 4P | E = b0 + b1 min(T minus cp, 0) + b2 max(T minus cp, 0), b1 < b2 | 4 |
| 5P | E = b0 + b1 max(cpH minus T, 0) + b2 max(T minus cpC, 0), b1, b2 > 0 | 5 |

Change points are searched on a 1 degree grid between the 10th and 90th percentiles of baseline temperatures. Fits with physically implausible slope signs are rejected. The selected model is the valid form with the lowest CV(RMSE), unless the project file forces a form (`force_model`), which is the right choice when the M&V plan specifies one.

**Statistics**, computed on period totals with n periods and p parameters:

* CV(RMSE) = sqrt(SSE / (n minus p)) / mean(y)
* NMBE = sum(y minus y_hat) / ((n minus p) x mean(y))
* R-squared = 1 minus SSE / SST
* Slope t-statistic t_j = b_j / se(b_j), from the weighted least squares covariance s^2 (X'WX)^(minus 1), with s^2 = sum(w r^2) / (n minus p). Computed for slope coefficients only, conditional on the selected change points.

**Model selection.** Among physically valid fits, models whose slopes all have |t| greater than the t threshold are preferred, and the lowest CV(RMSE) among them is selected. If none qualify, the lowest CV(RMSE) valid fit is selected and the acceptance check fails on the t-statistic.

**Avoided energy use.** Adjusted baseline = model applied to reporting-period temperatures and period lengths. Avoided energy use = adjusted baseline minus metered reporting-period use. This is the FEMP and IPMVP definition; normalized savings are not computed in v0.1.

**Uncertainty.** FEMP v5.0 cites EVO 10100-1:2018, *Uncertainty Assessment for IPMVP*, for quantifying savings uncertainty. MUNI-LCC v0.1 uses the ASHRAE Guideline 14 fractional savings uncertainty approximation instead, because it is the method most often used for monthly whole-building regression baselines and it needs only the baseline fit statistics and period counts. Both are recognized approaches; a project's M&V plan decides which applies. FEMP v5.0 gives no formula of its own, pointing to ASHRAE Guideline 14-2023 Appendix B and EVO 10100-1:2018 (Section 4.1), and states that calculating savings uncertainty is not required for federal projects (Sections 5.3 and 5.3.1). The 1.26 form below is taken from its reproduction in arXiv 1801.08175 (Equation 4) and has not yet been checked against a licensed copy of ASHRAE Guideline 14-2023. Comparing the two on the same data is listed in NEXT_STEPS.md. The ASHRAE Guideline 14 approximation for monthly models without autocorrelation is:

FSU = t x 1.26 x CV(RMSE) / F x sqrt((n + 2) / (n x m))

with F the fractional savings, n baseline periods, m reporting periods, and t at n minus p degrees of freedom. Absolute uncertainty = FSU x avoided energy use.

**Acceptance criteria.** Configurable in `config/acceptance_criteria.json`, each with its source. FEMP M&V Guidelines v5.0 values are used where FEMP states one:

| Criterion | Default | Source |
|---|---|---|
| R-squared | at least 0.75 | FEMP v5.0 Section 5.3.4.1 (IPMVP minimum) |
| Absolute NMBE (net determination bias) | at most 0.005 percent | FEMP v5.0 Section 5.3.4.1 (ASHRAE Guideline 14) |
| Slope t-statistic | greater than 2.0 | FEMP v5.0 Section 5.3.4.1 (IPMVP) |
| CV(RMSE) | at most 25 percent | LBNL (2017) guidance; FEMP v5.0 states no Option C value |
| Fractional savings uncertainty | at most 50 percent | LBNL (2017) guidance; FEMP v5.0 states no value |

FEMP v5.0 Table 4-2 (monthly CV(RMSE) 15 percent, MBE plus or minus 5 percent) applies to calibrated simulation under Option D and is not used for Option C. A baseline that is not 12, 24, 36, or 48 months produces a warning, following FEMP v5.0 Section 4.4, but does not fail acceptance. FEMP v5.0 Section 4.4 requires the project M&V plan to specify statistical validation targets; the plan's values replace these defaults.

## 4. Performance report (module `report`)

Implements the 2 CFR 200.329 elements a toolkit can support, as amended at 89 FR 30136 (April 22, 2024):

* **Due date, (c)(1).** Annual: 90 calendar days after the reporting period ends. Quarterly or semiannual: 30 days. Final: 120 days after the period of performance ends for a recipient, 90 days for a subrecipient. Extensions granted by the agency are not modeled.
* **Content, (c)(2).** Each objective's target versus verified actual, with the source of the actual (Option A measure, Option C, LCC result, or a reported value); the reason for each objective not met; budget versus actual cost; planned versus actual unit cost on a verified basis, with a configurable tolerance for "high unit cost"; and the required explanation when either applies.
* **Significant developments, (e).** Beneficial and adverse developments, with the corrective action plan required for adverse ones.
* **Completeness check.** The report lists every required explanation that is missing. A report with open items is not ready to submit.

## 5. Statistics helper

Two-sided Student t critical values use the exact closed forms for 1 and 2 degrees of freedom and a Cornish-Fisher expansion otherwise. Tests compare against published table values to within 0.012.

## 6. Verification of the implementation

* Closed-form checks of SPV and UPV factors, escalation identities, and a hand-computed LCC.
* Identities among NS, SIR, and AIRR (NS > 0 if and only if SIR > 1 if and only if AIRR > d).
* Exact recovery of a known change-point model from noiseless data.
* Recovery of a known injected savings fraction, noiseless and noisy, within the reported uncertainty.
* Due dates for every reporting frequency.
* An end-to-end test on the synthetic example against its stored true answer.
