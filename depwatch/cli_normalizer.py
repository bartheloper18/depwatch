"""cli_normalizer.py – CLI subcommand to display normalised package versions."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from depwatch.history import load_history
from depwatch.normalizer import NormalizedResult, normalize_result
from depwatch.checker import CheckResult, PackageStatus


def _result_from_entry(entry: dict) -> CheckResult:
    packages = [
        PackageStatus(
            name=p["name"],
            current_version=p["current_version"],
            latest_version=p["latest_version"],
            is_outdated=p["is_outdated"],
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(project=entry["project"], packages=packages)


def add_normalizer_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("normalize", help="Show normalised package version info")
    p.add_argument("--history", default="depwatch_history.json", help="History file path")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    p.set_defaults(func=_cmd_normalizer)


def _cmd_normalizer(args: argparse.Namespace) -> int:
    history = load_history(args.history)
    if not history:
        print("No history entries found.", file=sys.stderr)
        return 1

    results: List[NormalizedResult] = []
    for entry in history:
        result = _result_from_entry(entry)
        results.append(normalize_result(result))

    if args.as_json:
        out = []
        for nr in results:
            out.append({
                "project": nr.project,
                "packages": [
                    {
                        "name": p.name,
                        "current": p.current,
                        "latest": p.latest,
                        "is_outdated": p.is_outdated,
                        "current_parts": p.current_parts,
                        "latest_parts": p.latest_parts,
                    }
                    for p in nr.packages
                ],
            })
        print(json.dumps(out, indent=2))
    else:
        for nr in results:
            print(nr)

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-normalize")
    subs = parser.add_subparsers()
    add_normalizer_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
