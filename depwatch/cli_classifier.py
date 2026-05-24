"""CLI subcommand: classify — show packages grouped by update category."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.checker import CheckResult, PackageStatus
from depwatch.classifier import classify_result, format_classification
from depwatch.history import load_history


def _result_from_entry(entry: dict) -> CheckResult:
    packages = [
        PackageStatus(
            name=p["name"],
            current_version=p.get("current_version"),
            latest_version=p.get("latest_version"),
            is_outdated=p.get("is_outdated", False),
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(
        project=entry.get("project", "unknown"),
        project_type=entry.get("project_type", "unknown"),
        packages=packages,
    )


def add_classifier_subcommand(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "classify",
        help="Classify packages by update urgency (major/minor/patch/security/current)",
    )
    parser.add_argument("--history", required=True, help="Path to history JSON file")
    parser.add_argument(
        "--security",
        nargs="*",
        default=[],
        metavar="PKG",
        help="Package names to flag as security-sensitive",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output raw JSON",
    )
    parser.set_defaults(func=_cmd_classifier)


def _cmd_classifier(args: argparse.Namespace) -> int:
    entries = load_history(args.history)
    if not entries:
        print("No history entries found.", file=sys.stderr)
        return 1

    latest = entries[-1]
    result = _result_from_entry(latest)
    report = classify_result(result, security_packages=args.security)

    if args.as_json:
        data = {
            "project": report.project,
            "packages": [
                {
                    "name": p.name,
                    "current_version": p.current_version,
                    "latest_version": p.latest_version,
                    "category": p.category,
                    "project_type": p.project_type,
                }
                for p in report.packages
            ],
        }
        print(json.dumps(data, indent=2))
    else:
        print(format_classification(report))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-classify")
    subs = parser.add_subparsers()
    add_classifier_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
