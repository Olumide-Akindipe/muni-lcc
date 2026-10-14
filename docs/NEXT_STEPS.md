# Next steps

*Plain-language header: what later versions add, so v0.1 is understood as a first release.*

* **v0.2:** Option B; EVO 10100-1:2018 uncertainty procedure alongside the ASHRAE Guideline 14 approximation, with a comparison on the same data; normalized savings; occupancy and calendar variables in Option C; NOAA degree-day import.
* **v0.3:** Validation against real municipal billing data (with permission), with results published as a short validation report; comparison with an established open M&V implementation on the same data.
* **v0.4:** Daily and hourly Option C models with autocorrelation-corrected uncertainty; FEMP energy price indices by census region loaded from the annual NIST supplement.
* **v0.5:** Integration with TE3 (planning) and the Verification Gap Ledger (program requirements), so a municipality can plan, verify, and report within one decision-support system.
* **Publication:** JOSS requires more than six months of public development history and evidence of research use (JOSS submission guidelines and January 2026 policy). Plan:
  1. Release month: v0.1.0 public on GitHub and Zenodo; continuous integration running.
  2. Months 1 to 3: apply MUNI-LCC to one real municipal facility with the owner's permission; publish a short validation report with its own DOI.
  3. Months 2 to 5: v0.2 with Option B, EVO 10100-1:2018 uncertainty, and a life-cycle cost comparison against NIST BLCC on the same case; steady, small public commits and issues.
  4. Month 6 or later: update the paper's Research impact statement with the validation DOI and any outside use; check the paper against the JOSS format current at that time; submit. PyPI release alongside.
