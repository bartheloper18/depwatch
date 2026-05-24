"""cli_merger.py – CLI sub-command: merge history entries across projects."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depwatch.history import load_history
from depwatch.merger import merge_results, format_merged
from depwatch.checker import CheckResult, PackageStatus


def _results_from_history(hist_path: str) -> list:
    """Load the latest entry per project from a history file."""
    entries = load_history(Path(hist_path))
    seen: dict = {}
    for entry in entries:
        seen[entry.get("project", "unknown")] = entry
    results = []
    for project, entry in seen.items():
        pkgs = [
            PackageStatus(
                name=p["name"],
                current=p["current"],
                latest=p["latest"],
                outdated=p["outdated"],
            )
            for p in entry.get("packages", [])
        ]
        results.append(CheckResult(project_name=project, packages=pkgs))
    return results


def add_merger_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("merge", help="Merge results from multiple history files")
    p.add_argument("history_files", nargs="+", metavar="HISTORY", help="History JSON files")
    p.add_argument("--format", choices=["text", "csv"], default="text", dest="fmt")
    p.set_defaults(func=_cmd_merger)


def _cmd_merger(args: argparse.Namespace) -> int:
    all_results: list = []
    for hist_path in args.history_files:
        if not Path(hist_path).exists():
            print(f"[warn] history file not found: {hist_path}", file=sys.stderr)
            continue
        all_results.extend(_results_from_history(hist_path))

    if not all_results:
        print("No results to merge.", file=sys.stderr)
        return 1

    report = merge_results(all_results)
    print(format_merged(report, fmt=args.fmt))
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-merge")
    subs = parser.add_subparsers()
    add_merger_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
