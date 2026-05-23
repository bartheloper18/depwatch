"""CLI sub-command: generate or display a status badge for a project."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depwatch.badge import build_badge, load_badge, save_badge
from depwatch.history import latest_entry
from depwatch.checker import CheckResult, PackageStatus


def _result_from_entry(entry: dict) -> CheckResult:
    packages = [
        PackageStatus(
            name=p["name"],
            current=p["current"],
            latest=p["latest"],
            outdated=p["outdated"],
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(project_name=entry["project"], packages=packages)


def add_badge_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser("badge", help="Generate a Shields.io status badge")
    p.add_argument("history_file", type=Path, help="Path to the history JSON file")
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write badge JSON to this file instead of stdout",
    )
    p.add_argument(
        "--project",
        default=None,
        help="Project name to filter (uses first entry if omitted)",
    )
    p.set_defaults(func=_cmd_badge)


def _cmd_badge(args: argparse.Namespace) -> int:
    entry = latest_entry(args.history_file, project=args.project)
    if entry is None:
        print("depwatch badge: no history found", file=sys.stderr)
        return 1

    result = _result_from_entry(entry)
    badge = build_badge(result)

    if args.out:
        save_badge(badge, args.out)
        print(f"Badge written to {args.out}")
    else:
        import json
        print(json.dumps(badge.to_dict(), indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-badge")
    subs = parser.add_subparsers(dest="command")
    add_badge_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
