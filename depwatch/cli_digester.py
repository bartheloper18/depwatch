"""depwatch.cli_digester — CLI subcommand: `depwatch digest`

Reads the most recent history entry for each project found in the history
file and prints a digest report.
"""
from __future__ import annotations

import argparse
import sys
from typing import List

from depwatch.checker import CheckResult, PackageStatus
from depwatch.digester import build_digest, format_digest
from depwatch.history import load_history


def _result_from_entry(entry: dict) -> CheckResult:
    packages = [
        PackageStatus(
            name=p["name"],
            current_version=p["current_version"],
            latest_version=p["latest_version"],
            is_outdated=p.get("is_outdated", False),
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(
        project=entry.get("project", "unknown"),
        project_type=entry.get("project_type", "unknown"),
        packages=packages,
        checked_at=entry.get("checked_at", ""),
    )


def add_digester_subcommand(subparsers) -> None:
    p = subparsers.add_parser("digest", help="Show a digest of latest check results")
    p.add_argument("--history", default="depwatch_history.json", help="Path to history file")
    p.add_argument("--format", choices=["text", "markdown"], default="text", dest="fmt")
    p.set_defaults(func=_cmd_digester)


def _cmd_digester(args) -> int:
    history = load_history(args.history)
    if not history:
        print("No history entries found.", file=sys.stderr)
        return 1

    # Collect the latest entry per project
    seen: dict = {}
    for entry in history:
        project = entry.get("project", "unknown")
        seen[project] = entry  # later entries overwrite earlier ones

    results: List[CheckResult] = [_result_from_entry(e) for e in seen.values()]
    digest = build_digest(results)
    print(format_digest(digest, fmt=args.fmt))
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-digest")
    sub = parser.add_subparsers()
    add_digester_subcommand(sub)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
