"""cli_stamper.py – CLI sub-command: stamp the latest history entry with age metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from depwatch.checker import CheckResult, PackageStatus
from depwatch.history import load_history
from depwatch.stamper import format_stamped, stamp_result


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


def add_stamper_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("stamp", help="Show latest history entry with timestamp metadata")
    p.add_argument("--history", default=".depwatch_history.json", help="Path to history file")
    p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    p.set_defaults(func=_cmd_stamper)


def _cmd_stamper(args: argparse.Namespace) -> int:
    hist_path = Path(args.history)
    if not hist_path.exists():
        print(f"[stamper] history file not found: {hist_path}", file=sys.stderr)
        return 1

    entries = load_history(hist_path)
    if not entries:
        print("[stamper] history is empty", file=sys.stderr)
        return 1

    latest = entries[-1]
    result = _result_from_entry(latest)
    stamped = stamp_result(result)

    if args.as_json:
        data = {
            "project": stamped.project,
            "project_type": stamped.project_type,
            "stamped_at": stamped.stamped_at,
            "total_outdated": stamped.total_outdated,
            "packages": [
                {
                    "name": p.name,
                    "current_version": p.current_version,
                    "latest_version": p.latest_version,
                    "is_outdated": p.is_outdated,
                    "stamp": p.stamp,
                    "age_seconds": p.age_seconds,
                }
                for p in stamped.packages
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_stamped(stamped))

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-stamp")
    subs = parser.add_subparsers(dest="command")
    add_stamper_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
