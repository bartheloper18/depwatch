"""CLI sub-command: depwatch baseline

Usage examples
--------------
  depwatch baseline record  --project myapp --baseline-file .depwatch/baseline.json
  depwatch baseline show    --baseline-file .depwatch/baseline.json
  depwatch baseline clear   --baseline-file .depwatch/baseline.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from depwatch.baseline import load_baseline, save_baseline
from depwatch.checker import check_python, check_node
from depwatch.scanner import detect_project_type, ProjectType


def add_baseline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser("baseline", help="Manage dependency baselines")
    sub = parser.add_subparsers(dest="baseline_action", required=True)

    for name in ("record", "show", "clear"):
        p = sub.add_parser(name)
        p.add_argument("--project", default=os.getcwd(), help="Project root directory")
        p.add_argument(
            "--baseline-file",
            default=".depwatch/baseline.json",
            help="Path to the baseline file",
        )

    parser.set_defaults(func=_cmd_baseline)


def _cmd_baseline(args: argparse.Namespace) -> int:
    action = args.baseline_action
    bfile: str = args.baseline_file
    project: str = args.project

    if action == "clear":
        if os.path.exists(bfile):
            os.remove(bfile)
            print(f"Baseline cleared: {bfile}")
        else:
            print("No baseline file found — nothing to clear.")
        return 0

    if action == "show":
        baseline = load_baseline(bfile)
        if baseline is None:
            print("No baseline recorded yet.", file=sys.stderr)
            return 1
        print(json.dumps({"project": baseline.project, "recorded_at": baseline.recorded_at,
                          "packages": baseline.packages}, indent=2))
        return 0

    # record
    scan = detect_project_type(project)
    if scan is None:
        print(f"Could not detect project type in: {project}", file=sys.stderr)
        return 1

    if scan.project_type == ProjectType.PYTHON:
        result = check_python(project)
    else:
        result = check_node(project)

    baseline = save_baseline(result, bfile)
    print(f"Baseline recorded for '{baseline.project}' at {baseline.recorded_at}")
    print(f"  {len(baseline.packages)} package(s) tracked → {bfile}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-baseline")
    subs = parser.add_subparsers(dest="baseline_action", required=True)
    for name in ("record", "show", "clear"):
        p = subs.add_parser(name)
        p.add_argument("--project", default=os.getcwd())
        p.add_argument("--baseline-file", default=".depwatch/baseline.json")
    args = parser.parse_args()
    args.func = _cmd_baseline
    sys.exit(_cmd_baseline(args))


if __name__ == "__main__":  # pragma: no cover
    main()
