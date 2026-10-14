# Start here: MUNI-LCC in plain language

## What you are building, in one sentence

A free, open toolkit that lets a small city or town check whether an energy project actually saved what it promised, whether it was worth the money over its whole life, and write that up the way federal grant reports require.

## Why it matters

Small and mid-sized municipalities receive federal and state money for building upgrades, LED lighting, boilers, and controls. The grant rules (2 CFR 200.329) require them to report what they accomplished against what they promised. Large federal agencies do this with expensive consultants and paid software. A town with one facilities manager usually cannot. So savings get estimated, not verified, and the report says little the funder can rely on. MUNI-LCC puts the federal methods into free software a town can run.

A comparison: it is like a tax-preparation program for energy projects. The rules exist and are public, but they are hard to apply by hand. The software applies them the same way every time and shows its work.

## Where the methods come from

This toolkit uses methods, not a downloaded dataset:

- The Department of Energy's federal rulebook for checking energy savings (FEMP M&V Guidelines, Version 5.0, September 2024). Free and public.
- The international protocol those rules build on (IPMVP Core Concepts 2022), specifically two of its four options: Option A, which measures the one thing that changed (for example, the wattage of new lights), and Option C, which looks at the whole building's utility bills.
- The standard way to add up a project's lifetime costs in today's dollars (ASTM E917, using the free federal version of the same equations in NIST Handbook 135).
- The federal discount rate published each year by NIST and DOE (3.0 percent real for 2025).
- The federal grant rule on performance reporting (2 CFR 200.329, revised 2024).

## What you will have at the end

- A public project page on GitHub with the code, tests, and a worked example.
- A permanent citation number (DOI) from Zenodo.
- A software paper ready to submit to the Journal of Open Source Software once the repository has some public history.
- A sample grant performance report the toolkit produced, which you can show to municipal staff.

## How it connects to your work

It is a working piece of your proposed Municipal Energy-Modernization Decision-Support System. TE3 helps a town decide what to build. The Verification Gap Ledger documents where programs fail to verify outcomes. MUNI-LCC is the tool that closes that gap for an individual project: it verifies and reports.

## What you need to do, and how long it takes

1. Read this page and the decisions list in VERIFY_CHECKLIST.md (15 minutes).
2. Check the results using the checklist (1 to 2 hours).
3. Approve publishing in your own words (5 minutes).
4. Create the GitHub repository and Zenodo record by following PUBLISH_GUIDE.md, or give Claude tokens to do it (20 minutes).

## The steps ahead

1. Methods confirmed and plan written. Done.
2. Lifetime cost engine built and tested. Done.
3. Savings verification (Options A and C) built and tested. Done.
4. Grant report output built. Done.
5. Documentation, checklist, and publishing guide written. Done.
6. Your check (you). Then publishing (you or Claude with your tokens).
