"""CLI sub-command: depwatch group — show packages grouped by severity."""

from __future__ import annotations

import argparse
import sys

from depwatch.grouper import group_result
from depwatch.history import latest_entry
from depwatch.checker import CheckResult, PackageStatus


def _result_from_entry(entry: dict) -> CheckResult:
    pkgs = [
        PackageStatus(
            name=p["name"],
            current_version=p.get("current_version", ""),
            latest_version=p.get("latest_version", ""),
            outdated=p.get("outdated", False),
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(project_name=entry["project_name"], packages=pkgs)


def add_grouper_subcommand(subparsers: argparse.Action) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("group", help="Show packages grouped by severity")
    p.add_argument("--history", required=True, help="Path to history JSON file")
    p.add_argument(
        "--project", default=None, help="Filter to a specific project name"
    )
    p.set_defaults(func=_cmd_grouper)


def _cmd_grouper(args: argparse.Namespace) -> None:
    entry = latest_entry(args.history, project=getattr(args, "project", None))
    if entry is None:
        print("No history found.", file=sys.stderr)
        sys.exit(1)

    result = _result_from_entry(entry)
    grouped = group_result(result)

    print(f"Project : {grouped.project_name}")
    print(f"Critical: {len(grouped.critical)}")
    for p in grouped.critical:
        print(f"  {p}")
    print(f"Moderate: {len(grouped.moderate)}")
    for p in grouped.moderate:
        print(f"  {p}")
    print(f"Low     : {len(grouped.low)}")
    for p in grouped.low:
        print(f"  {p}")
    print(f"Up-to-date: {len(grouped.up_to_date)}")


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-group")
    subs = parser.add_subparsers(dest="command")
    add_grouper_subcommand(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
