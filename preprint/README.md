# MUNI-LCC preprint: source and analysis

*Plain-language header: this folder holds everything needed to rebuild the MUNI-LCC preprint from scratch, including the extra tests run for it. You do not need to open the scripts. Charts are drawn in a Power BI report style.*

## Rebuild (from the repository root)

```bash
pip install -e ".[test,examples]"
# v0.1.1 results (current code), about 10 minutes on 2 cores
python preprint/analysis/validation.py --out preprint/analysis/out_v011
python preprint/analysis/underfit_check.py --out preprint/analysis/out_v011
python preprint/analysis/lcc_scans.py --repo . --out preprint/analysis/out_v011
# figures and every number in the text
python preprint/analysis/figures.py --repo . --data preprint/analysis/out_v011 --out preprint/figs
python preprint/analysis/make_numbers.py --repo . --data preprint/analysis/out_v011 \
       --before preprint/analysis/out_v010 --out preprint/numbers.tex
cd preprint && latexmk -pdf main.tex
```

`analysis/out_v010/` holds the same tests run on the v0.1.0 code (tag `v0.1.0`), used only for the version comparison table. To regenerate it, check out `v0.1.0` in a separate folder and run `validation.py` with that code on the path. All scripts use fixed seeds, so re-runs reproduce the stored outputs exactly.

## Files

| File | What it is |
|---|---|
| `main.tex`, `validation_section.tex` | Manuscript |
| `numbers.tex` | Every number in the manuscript, generated; never edit by hand |
| `refs.bib`, `main.bbl` | References (arXiv needs `main.bbl`) |
| `figs/` | Figures as PDF |
| `analysis/validation.py` | Monte Carlo coverage tests of Option C and Option A |
| `analysis/underfit_check.py` | Model selection under true 4P and 5P models, v0.1.0 rule versus v0.1.1 rule |
| `analysis/lcc_scans.py` | Life-cycle cost sensitivity scans |
| `analysis/figures.py` | All charts |
| `analysis/make_numbers.py` | Writes `numbers.tex` from the output files |
| `analysis/out_v011/`, `analysis/out_v010/` | Outputs of the scripts |
| `VERIFY_PREPRINT.md` | What the author must check before posting |

Code: MIT. Text and figures: CC BY 4.0. Synthetic data only.
