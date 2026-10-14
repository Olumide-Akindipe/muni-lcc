# Publish guide: MUNI-LCC v0.1.0

*Plain-language header: step-by-step instructions to put MUNI-LCC on GitHub and get its DOI from Zenodo. Do this only after your verification checklist is complete. Total time: about 25 minutes.*

## Copy-ready text

**Repository name:** `muni-lcc`

**Short description (GitHub "About"):**
Open life-cycle cost and M&V toolkit for municipal energy projects: IPMVP Options A and C as defined in FEMP M&V v5.0, life-cycle cost consistent with ASTM E917, 2 CFR 200.329 report content.

**Title (Zenodo):**
MUNI-LCC: open life-cycle cost and measurement-and-verification toolkit for municipal energy projects

**Creator (Zenodo):** Akindipe, Stephen Olumide. ORCID 0000-0002-1846-9662. Affiliation: Independent Researcher, Albany, NY, USA.

**Keywords:** life-cycle cost analysis; measurement and verification; IPMVP; FEMP; ASTM E917; municipal energy; Uniform Guidance; energy efficiency; performance reporting; 2 CFR 200.329

**Release notes (v0.1.0):**
First public release. Life-cycle cost analysis consistent with ASTM E917 and NIST Handbook 135; IPMVP Options A and C as defined in DOE FEMP M&V Guidelines v5.0 (September 2024, based on IPMVP Core Concepts 2022), with model statistics, slope t-statistics, fractional savings uncertainty, and acceptance criteria taken from FEMP v5.0 where it states them and LBNL guidance otherwise. Performance report content and due dates aligned with 2 CFR 200.329 as amended in 2024. Synthetic worked example with a known answer; 33 automated tests.


## 1. Connect Zenodo to GitHub first

Doing this before the first release means Zenodo mints the DOI automatically.

1. Log in at https://zenodo.org with **Log in with ORCID** or **Log in with GitHub**.
2. Click your name (top right), then **GitHub**. Click **Sync now**.
3. You will flip the switch for `muni-lcc` in step 2.4, once the repository exists.

## 2. Create the GitHub repository 

1. Go to https://github.com/new. Owner: `Olumide-Akindipe`. Repository name: `muni-lcc`. Paste the short description. Public. **Do not** tick "Add a README" (the project has one). Click **Create repository**.
2. Unzip `muni-lcc-v0.1.0.zip` on your computer. Open a terminal in the unzipped `muni-lcc` folder and paste, one line at a time:
   ```
   git init -b main
   git add -A
   git commit -m "MUNI-LCC v0.1.0"
   git remote add origin https://github.com/Olumide-Akindipe/muni-lcc.git
   git push -u origin main
   ```
   The last line asks for your GitHub username and, as the password, a personal access token: create one at https://github.com/settings/tokens/new with the **repo** and **workflow** boxes ticked (the **workflow** box is needed because the project includes a test workflow). Afterward the repository page shows the README and the figure.
   Then click the **Actions** tab. The "tests" run should finish with a green tick within a few minutes. If it shows a red cross, send Claude the log.
3. On the repository page, click the gear next to **About**, paste the keywords as Topics (`life-cycle-cost`, `measurement-and-verification`, `ipmvp`, `energy-efficiency`, `municipal`, `uniform-guidance`). Save.
4. Back on Zenodo's GitHub page, click **Sync now** and flip the switch next to `muni-lcc` to **On**.

## 3. Make the release, which mints the DOI (5 min)

1. On the repository page click **Releases**, then **Draft a new release**.
2. **Choose a tag:** type `v0.1.0`, click **Create new tag**. Release title: `MUNI-LCC v0.1.0`. Paste the release notes. Click **Publish release**.
3. Within about 5 minutes, Zenodo shows the record under **Upload**. Open it. Check the creator, title, and license; click **Edit** if anything needs fixing (paste from the copy-ready text). Note the two DOIs: the **concept DOI** (all versions) and the **version DOI** (v0.1.0).

## 4. Record the DOI everywhere (5 min)


1. Open `config/release.json`. Set `doi` to the concept DOI, `date_released` to today's date, and `status` to `Released v0.1.0`. Run `python scripts/render_docs.py`. This updates the README, CITATION.cff, the talk track, and the paper in one step. In `CHANGELOG.md`, change "## 0.1.0 (first public release)" to "## 0.1.0 (" followed by today's date and ")".
2. Commit and push: `git commit -am "Add DOI" && git push`.
3. Add a row to `docs/EVIDENCE_LOG.csv` the same day, and save PDFs of the GitHub release page and the Zenodo record. Publications not logged on release day are the ones that go missing later.

## 5. Later: JOSS (when the repository has history)

The Journal of Open Source Software reviews whether software shows sustained development and real use. JOSS requires more than six months of public history before submission, so the earliest date is six months after the repository goes public. Before submitting, complete the plan in `docs/NEXT_STEPS.md`, update the paper's Research impact statement, and check the paper against the JOSS paper format page. Steps: confirm `paper/paper.md` and `paper/paper.bib` are current, go to https://joss.theoj.org/papers/new, enter the repository URL and the version DOI, and submit. Review happens in a public GitHub issue. Keep the paper's "AI usage disclosure" section: JOSS requires it in every submission, naming the AI tool and version, where it was used, and confirming human review.
