"""Command line interface.

    muni-lcc run PROJECT.json [--out DIR] [--final]
    muni-lcc due-date PERIOD_END FREQUENCY [--subrecipient]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import __version__
from . import pipeline
from . import report as R


def _cmd_run(args) -> int:
    res = pipeline.run(args.project, final=args.final)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in res.items() if k != "report"}, f, indent=2, default=float)
    if "report" in res:
        rep = res["report"]
        with open(os.path.join(args.out, "performance_report.md"), "w", encoding="utf-8") as f:
            f.write(R.to_markdown(rep))
        with open(os.path.join(args.out, "performance_report.json"), "w", encoding="utf-8") as f:
            f.write(R.to_json(rep))
        for issue in rep["completeness_issues"]:
            print(f"needs attention: {issue}", file=sys.stderr)
    print(f"wrote outputs to {args.out}")
    return 0


def _cmd_due(args) -> int:
    print(R.due_date(args.period_end, args.frequency, args.subrecipient))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="muni-lcc", description=__doc__.splitlines()[0])
    p.add_argument("--version", action="version", version=f"muni-lcc {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a project file and write results and the performance report")
    r.add_argument("project")
    r.add_argument("--out", default="outputs")
    r.add_argument("--final", action="store_true", help="mark the report verified (removes the draft banner)")
    r.set_defaults(fn=_cmd_run)
    d = sub.add_parser("due-date", help="performance report due date under 2 CFR 200.329(c)(1)")
    d.add_argument("period_end")
    d.add_argument("frequency", choices=["annual", "semiannual", "quarterly", "final"])
    d.add_argument("--subrecipient", action="store_true")
    d.set_defaults(fn=_cmd_due)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
