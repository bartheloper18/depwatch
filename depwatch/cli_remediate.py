"""CLI sub-command: depwatch remediate — show upgrade commands for outdated packages."""

import argparse
import sys

from depwatch.config import load_config
from depwatch.history import load_history, latest_entry
from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType
from depwatch.remediate import generate_advice, format_advice


def _result_from_entry(entry: dict) -> CheckResult:
    """Reconstruct a lightweight CheckResult from a history entry dict."""
    packages = [
        PackageStatus(
            package=p["package"],
            current_version=p["current_version"],
            latest_version=p.get("latest_version"),
            outdated=p.get("outdated", False),
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(
        project_name=entry["project_name"],
        project_type=ProjectType(entry.get("project_type", "python")),
        packages=packages,
    )


def add_remediate_subcommand(subparsers) -> None:
    p = subparsers.add_parser(
        "remediate",
        help="Show upgrade commands for outdated packages based on latest history.",
    )
    p.add_argument("--config", default=None, help="Path to depwatch config file.")
    p.add_argument("--project", default=None, help="Filter by project name.")
    p.set_defaults(func=_cmd_remediate)


def _cmd_remediate(args) -> int:
    cfg = load_config(args.config)
    history = load_history(cfg.history_path)

    if not history:
        print("No history found. Run depwatch first to collect data.", file=sys.stderr)
        return 1

    projects = {e["project_name"] for e in history}
    if args.project and args.project not in projects:
        print(f"Project '{args.project}' not found in history.", file=sys.stderr)
        return 1

    all_advice = []
    for project_name in sorted(projects):
        if args.project and project_name != args.project:
            continue
        entry = latest_entry(history, project_name)
        if entry is None:
            continue
        result = _result_from_entry(entry)
        all_advice.extend(generate_advice(result))

    print(format_advice(all_advice))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-remediate")
    subs = parser.add_subparsers()
    add_remediate_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
