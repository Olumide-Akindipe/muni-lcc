"""Render documents from templates/ using examples/outputs/stats.json.

Every number quoted in README.md, docs/TALK_TRACK.md, and paper/paper.md is
interpolated here from the stats file the example pipeline writes, so the text
cannot drift from the results. Run after examples/run_example.py.

    python scripts/render_docs.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = {"README.md.tmpl": "README.md", "TALK_TRACK.md.tmpl": "docs/TALK_TRACK.md",
           "paper.md.tmpl": "paper/paper.md", "CITATION.cff.tmpl": "CITATION.cff"}


def fmt(v):
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int) and abs(v) >= 1000:
        return f"{v:,}"
    return str(v)


def main():
    with open(os.path.join(ROOT, "examples", "outputs", "stats.json"), encoding="utf-8") as f:
        stats = json.load(f)
    with open(os.path.join(ROOT, "config", "release.json"), encoding="utf-8") as f:
        stats.update({k: v for k, v in json.load(f).items() if not k.startswith("_")})
    doi = str(stats.get("doi", "")).strip()
    if doi.startswith("10."):
        stats["doi_status"] = f"DOI: [{doi}](https://doi.org/{doi})."
        stats["doi_cite"] = f"Zenodo. https://doi.org/{doi}"
        stats["doi_cff"] = f'doi: "{doi}"\n'
    else:
        stats["doi_status"] = "Archived on Zenodo; the DOI is added here once Zenodo assigns it."
        stats["doi_cite"] = "GitHub. https://github.com/Olumide-Akindipe/muni-lcc"
        stats["doi_cff"] = ""
    import datetime as _dt
    try:
        d = _dt.date.fromisoformat(stats["date_released"])
        stats["date_long"] = f"{d.day} {d.strftime('%B %Y')}"
    except (ValueError, KeyError):
        stats["date_long"] = stats.get("date_released", "")
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                         capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", out)
    stats["n_tests"] = int(m.group(1)) if m else "all"
    for src, dst in TARGETS.items():
        p = os.path.join(ROOT, "templates", src)
        if not os.path.exists(p):
            continue
        text = open(p, encoding="utf-8").read()
        missing = set(re.findall(r"{{(\w+)}}", text)) - set(stats)
        if missing:
            raise SystemExit(f"{src}: no stats for {sorted(missing)}")
        text = re.sub(r"{{(\w+)}}", lambda mm: fmt(stats[mm.group(1)]), text)
        with open(os.path.join(ROOT, dst), "w", encoding="utf-8") as f:
            f.write(text)
        print(f"rendered {dst}")


if __name__ == "__main__":
    main()
