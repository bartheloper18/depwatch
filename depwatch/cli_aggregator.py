"""CLI sub-command: aggregate — cross-project outdated package summary."""
from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.history import load_history
from depwatch.checker import CheckResult, PackageStatus
from depwatch.aggregator import aggregate_results, format_aggregate


def _results_from_history(history_path: str) -> List[CheckResult]:
    entries = load_history(history_path)
    results: List[CheckResult] = []
    for entry in entries:
        packages = [
            PackageStatus(
                name=p["name"],
                current=p["current"],
                latest=p["latest"],
                is_outdated=p["is_outdated"],
            )
            for p in entry.get("packages", [])
        ]
        results.append(CheckResult(project=entry["project"], packages=packages))
    return results


def add_aggregator_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "aggregate", help="Show cross-project dependency aggregate"
    )
    p.add_argument("history", help="Path to history JSON file")
    p.add_argument(
        "--format",
        choices=["text", "csv"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.set_defaults(func=_cmd_aggregator)


def _cmd_aggregator(args: argparse.Namespace) -> int:
    results = _results_from_history(args.history)
    if not results:
        print("No history entries found.", file=sys.stderr)
        return 1
    report = aggregate_results(results)
    print(format_aggregate(report, fmt=args.fmt))
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-aggregate")
    subs = parser.add_subparsers()
    add_aggregator_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
