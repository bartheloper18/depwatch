"""CLI sub-command: filter — display packages matching filter criteria."""
from __future__ import annotations

import argparse
import sys

from depwatch.filterer import FilterCriteria, filter_result, format_filtered
from depwatch.history import load_history
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
    return CheckResult(
        project_name=entry["project_name"],
        project_type=entry.get("project_type", "unknown"),
        packages=packages,
        checked_at=entry.get("checked_at", ""),
    )


def add_filterer_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("filter", help="Filter packages by criteria")
    p.add_argument("--history", default=".depwatch_history.json", metavar="PATH")
    p.add_argument("--only-outdated", action="store_true", default=False)
    p.add_argument("--name-contains", default=None, metavar="TEXT")
    p.add_argument("--min-bump", choices=["patch", "minor", "major"], default=None)
    p.add_argument("--project-type", dest="project_types", action="append",
                   default=[], metavar="TYPE")
    p.set_defaults(func=_cmd_filterer)


def _cmd_filterer(args: argparse.Namespace) -> None:
    entries = load_history(args.history)
    if not entries:
        print("No history entries found.", file=sys.stderr)
        return

    criteria = FilterCriteria(
        only_outdated=args.only_outdated,
        name_contains=args.name_contains,
        min_bump=args.min_bump,
        project_types=args.project_types,
    )

    latest = entries[-1]
    result = _result_from_entry(latest)
    filtered = filter_result(result, criteria)
    print(format_filtered(filtered))


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-filter")
    subs = parser.add_subparsers()
    add_filterer_subcommand(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
