"""cli_auditor.py – CLI sub-command: depwatch audit"""
from __future__ import annotations

import argparse
import sys

from depwatch.auditor import audit_result, format_audit
from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import load_history


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


def add_auditor_subcommand(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("audit", help="Audit dependencies for severity findings")
    p.add_argument("--history", default="depwatch_history.json", help="History file path")
    p.add_argument("--project", default=None, help="Filter to a specific project name")
    p.add_argument("--min-severity", choices=["low", "high", "critical"], default="low")
    p.set_defaults(func=_cmd_auditor)


_SEVERITY_RANK = {"low": 0, "high": 1, "critical": 2}


def _cmd_auditor(args: argparse.Namespace) -> int:
    entries = load_history(args.history)
    if not entries:
        print("No history entries found.", file=sys.stderr)
        return 1

    results = [_result_from_entry(e) for e in entries]
    if args.project:
        results = [r for r in results if r.project == args.project]

    min_rank = _SEVERITY_RANK[args.min_severity]
    found_any = False
    for result in results:
        report = audit_result(result)
        filtered = [
            f for f in report.findings if _SEVERITY_RANK[f.severity] >= min_rank
        ]
        if filtered:
            found_any = True
            for finding in filtered:
                print(finding)

    if not found_any:
        print("No findings at or above the requested severity level.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-audit")
    sub = parser.add_subparsers()
    add_auditor_subcommand(sub)
    args = parser.parse_args()
    if hasattr(args, "func"):
        sys.exit(args.func(args))
    else:
        parser.print_help()
