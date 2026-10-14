# Your verification checklist

*Plain-language version: before MUNI-LCC goes public under your name, you check it. Every item names the file, the number, and what a match looks like. Total time: about 1.5 hours in one sitting. Tick each box and add the date.*

*The publish gate (`scripts/publish_gate.py`) checks the mechanical items automatically. These are yours.*

## Part 1: Make sure the results can be rebuilt (15 to 20 min)

Pick one:

- [ ] **Option A, run it yourself.** Open a terminal in the project folder and paste:
  ```
  pip install -e ".[test]"
  python -m pytest
  python examples/make_example_data.py
  python examples/run_example.py
  ```
  You should see `33 passed`, then a block of numbers that includes `"option_c_avoided_therms": 6879` and `"lcc_net_savings": 151675`.
- [x] **Option B, ask Claude.** In a new chat with Opus 5.5 or Fable 5, upload the project zip and say: "Install this package, run the tests and examples/run_example.py from scratch, and give me the headline numbers." They should be: 33 tests pass; avoided gas 6,879 therms; Option A 28,392 kWh; net savings $151,675; SIR 2.27.

Then:
- [x] Every number in `README.md` matches `examples/outputs/stats.json` (they are generated from it; spot check three).

*Part 1 result, 2026-10-14: clean install in a fresh environment, example data deleted and regenerated from seed 2026, 33 tests passed, regenerated data files and stats.json byte-identical to the package. Headline numbers: avoided gas 6,879 therms (true 6,629), Option A 28,392 kWh, net savings $151,675, SIR 2.27, R-squared 0.988, slope t 42.3, all acceptance criteria met. All README numbers checked against stats.json by script.*

*Parts 2 and 3 confirmed by the author, 2026-10-14. Part 2 note: no 2026 NIST supplement (NIST IR 85-3273-41) found as of 2026-10-14; the 2025 edition remains current.*

## Part 2: Check the method sources (15 min)

- [x] FEMP M&V Guidelines v5.0 opens: https://www.energy.gov/sites/default/files/2024-10/mv_guide_5_0.pdf. Confirm the cover says Version 5.0 and September 2024. Search the PDF for "Option A" and "Option C" and confirm the definitions match METHODS.md sections 2 and 3 in substance. Find footnote 1 and confirm it cites IPMVP Core Concepts, EVO 10000-1:2022.
- [x] 2 CFR 200.329 opens: https://www.ecfr.gov/current/title-2/section-200.329. Confirm paragraph (c)(1) still says 90 days for annual reports, 30 days for quarterly and semiannual, and 120 days (90 for subrecipients) for the final report.
- [x] NIST IR 85-3273-40 opens: https://nvlpubs.nist.gov/nistpubs/ir/2025/NIST.IR.85-3273-40.pdf. Confirm the FEMP real discount rate is 3.0 percent. Then search "NIST IR 85-3273-41" to see whether a 2026 edition has been published since August 2025. If it has, note its rate here: ___
- [x] All sources are public government documents except IPMVP, ASTM E917, and ASHRAE Guideline 14, which are cited but not reproduced.

## Part 3: Check numbers by hand (30 min)

Use a calculator. Each should match to the last whole number.

**Option A (lighting).** Open `examples/project.json`.
- [x] Baseline readings 14.4, 14.9, 14.5, 14.7, 14.5 average to 14.6 kW. Post readings 6.1, 6.3, 6.2, 6.0, 6.4 average to 6.2 kW.
- [x] (14.6 minus 6.2) x 3,380 hours = 28,392 kWh. The report says 28,392.

**Option C (gas).** Open `examples/outputs/performance_report.md` and `examples/data/gas_reporting.csv`.
- [x] The model is E/day = 43.0004 + 6.3688 x max(57 minus T, 0). For January 2025 (row 1: 31 days, 28.4 F): 57 minus 28.4 = 28.6; 6.3688 x 28.6 = 182.15; plus 43.00 = 225.15 per day; x 31 days = 6,980. `examples/outputs/results.json`, first `by_period` entry, says 6,979.55.
- [x] Avoided energy use = adjusted baseline 45,616.8 minus metered 38,737.4 = 6,879.4. The report shows 6,879 (it rounds each figure separately, so 45,617 minus 38,737 looks like 6,880).
- [x] The true savings stored in `examples/data/TRUTH.json` are 6,628.7 therms. The toolkit's 6,879 is 251 above it. The uncertainty band is plus or minus 2,352 therms. 251 is inside it.
- [x] Extremes: the highest baseline month is 2023-01 (8,397.5 therms at 20.0 F) and the lowest is 2024-09 (973.9 therms at 62.5 F) in `examples/data/gas_baseline.csv`. Both make physical sense for a gas-heated building.

**Life-cycle cost.**
- [x] UPV for 25 years at 3 percent: (1 minus 1.03^(minus 25)) / 0.03 = 17.413. Compare with the UPV table in the NIST Annual Supplement for 3.0 percent and 25 years.
- [x] The base case boiler replacement of $95,000 in year 8 is worth 95,000 / 1.03^8 = $74,994 today. `examples/outputs/results.json`, `lcc_detail`, `base`, `replacement` says 74,993.88.

**Due date.**
- [x] Reporting period ends 2025-12-31, annual report: 90 days later is 2026-03-31. The report says 2026-03-31.

## Part 4: Your decisions (15 min)

The build made these choices provisionally. Agree or change each one.

- [x] **Discount rate default.** Option A: keep 3.0 percent (FEMP 2025). Option B: switch to the 2026 edition rate if Part 2 found one. Recommended: B if it exists, otherwise A. Your choice: Option A 
- [x] **Option C acceptance thresholds.** Decided 2026-10-14 after checking FEMP v5.0. FEMP values adopted where FEMP states one (Section 5.3.4.1): R-squared at least 0.75, absolute NMBE at most 0.005 percent, slope t-statistic greater than 2.0. LBNL 2017 values kept where FEMP gives none, labeled as non-FEMP: CV(RMSE) at most 25 percent, FSU at most 50 percent. Whole-year baseline warning added (FEMP Section 4.4). Table 4-2 (CV(RMSE) 15 percent, MBE 5 percent) applies to calibrated simulation, Option D, and was not used. Your choice: adopted as above.
  - [x] Confirm in the PDF: Section 5.3.4.1 (printed page 47) says R2 0.75, bias 0.005%, and t greater than 2.0. Section 4.4 (printed page 27) says whole-year sets of 12, 24, 36, or 48 months. Choice: All confirmed
- [x] **Uncertainty formula form.** Decided 2026-10-14 after checking FEMP v5.0. FEMP gives no fractional savings uncertainty formula of its own; it points to ASHRAE Guideline 14-2023 Appendix B and EVO 10100-1:2018 (Section 4.1), combines independent error sources by root-sum-square (Equation 5-1, Section 5.3), and states that calculating savings uncertainty is not required for federal projects (Sections 5.3 and 5.3.1). Choice: keep the ASHRAE Guideline 14 approximation, FSU = t x 1.26 x CV / F x sqrt((n + 2)/(n x m)), for v0.1, documented as not yet checked against a licensed copy of ASHRAE 14-2023 Appendix B (current source: arXiv 1801.08175, Equation 4, a preprint). Add EVO 10100-1:2018 in v0.2.
  - [x] Confirm in the PDF: Section 4.1 (printed page 18) cites ASHRAE 14-2023 Appendix B and EVO 10100-1:2018; Section 5.3 (printed pages 43 to 44) has Equation 5-1 and says uncertainty is not required for federal projects.
  - [ ] Optional, later: if you get ASHRAE 14-2023 (Bard library or a colleague's copy), compare Appendix B with the formula above and tell Claude the result.
- [x] **Confidence level.** Decided 2026-10-14 after checking FEMP v5.0. FEMP leaves the confidence level to the customer (Table 3-1, item e, Section 3.2), sets sampling at "at least 80% confidence and 20% precision" (Section 5.3.2), and lists "90/10 or 80/20" in its measure-specific tables (Section 6). Choice: 90 percent by default, the stricter of FEMP's two listed levels; changeable per project with the `confidence` field; 80 percent is the FEMP minimum.
  - [x] Confirm in the PDF: Table 3-1 item e (printed page 16), Section 5.3.2 (printed page 46), and any Section 6 table showing 90/10 or 80/20.
- [x] **Wording of the claim.** Decided 2026-10-13. "Implements IPMVP Options A and C as defined in the DOE FEMP M&V Guidelines v5.0"; life-cycle cost "consistent with ASTM E917"; uncertainty "using the ASHRAE Guideline 14 approximation"; reporting content "aligned with 2 CFR 200.329." The README, paper, talk track, and publish guide already use this wording.
- [x] **Repository name and license.** `Olumide-Akindipe/muni-lcc`, code MIT, documentation CC BY 4.0. Recommended: keep. Your choice: Keep

## Part 5: Before it goes public (15 min)

- [x] The README opening paragraph and the paper Summary and Statement of need are rewritten in your own words. 
- [x] Name, ORCID, affiliation, and email are correct in `AUTHORS.json`.
- [x] You have read `docs/LIMITATIONS.md` and agree with it.
- [x] Claude regenerates outputs with `--final`, fills the release date (DOI added after Zenodo assigns it), and `python scripts/publish_gate.py . --allow-draft-in src tests scripts examples/run_example.py` passes.
- [ ] Evidence log row written on release day (`docs/EVIDENCE_LOG.csv`).

**When every box is ticked, reply to Claude in your own words that you have checked the package and approve publishing.**

## Part 6: Added after your verification (20 min)

These were added on 2026-10-14 to prepare for JOSS. They are statements in your name, so check each.

- [x] `paper/paper.md`, **State of the field**: each description of BLCC, E3, eemeter, nmecr, and RMV2.0 matches that tool's own page (links are in `paper/paper.bib`). The claim is only that none is *documented* as linking verified savings to life-cycle cost and federal reporting.
- [x] `paper/paper.md`, **Software design**: each bullet describes a choice you agree with and can explain.
- [x] `paper/paper.md`, **Research impact statement**: accurate as of release. Update it before any JOSS submission.
- [x] `paper/paper.md`, **Acknowledgements**: "No financial support was received for this work" is true. If any grant, employer time, or other support applied, tell Claude.
- [x] `paper/paper.md`, **AI usage disclosure**: every sentence is true, including what it says you did yourself.
- [x] `SUPPORT.md`: you accept the aim of acknowledging new issues within 14 days, or give Claude a different period.
- [x] `GOVERNANCE.md`: the decision rules and continuity plan are ones you will follow.
- [ ] After the first push, the GitHub **Actions** tab shows a green tick for the "tests" workflow.

**Author approval:** "I approve, publish" (Stephen Olumide Akindipe, 2026-10-14). Part 6 statements accepted with this approval.
