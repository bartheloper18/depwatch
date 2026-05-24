"""cli_recommender.py – CLI subcommand: depwatch recommend"""
from __future__ import annotations

import argparse
import sys

from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import load_history
from depwatch.recommender import format_recommendations, recommend


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
    return CheckResult(
        project=entry.get("project", "unknown"),
        project_type=entry.get("project_type", "unknown"),
        packages=packages,
    )


def add_recommender_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser(
        "recommend",
        help="Show prioritised upgrade recommendations from the latest history entry.",
    )
    p.add_argument(
        "--history",
        default=".depwatch_history.json",
        help="Path to history file (default: .depwatch_history.json)",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Filter to a specific project name.",
    )
    p.set_defaults(func=_cmd_recommender)


def _cmd_recommender(args: argparse.Namespace) -> int:
    history = load_history(args.history)
    if not history:
        print("No history entries found.", file=sys.stderr)
        return 1

    # Use the most recent entry
    entry = history[-1]
    results = entry.get("results", [])

    if not results:
        print("Latest history entry contains no results.", file=sys.stderr)
        return 1

    if args.project:
        results = [r for r in results if r.get("project") == args.project]
        if not results:
            print(f"No results for project '{args.project}'.", file=sys.stderr)
            return 1

    for raw in results:
        result = _result_from_entry(raw)
        report = recommend(result)
        print(format_recommendations(report))

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-recommend")
    subs = parser.add_subparsers(dest="command")
    add_recommender_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
