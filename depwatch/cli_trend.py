"""CLI sub-command: depwatch trend — show outdated-count trend for a project."""
from __future__ import annotations

import argparse
import sys

from depwatch.trend import build_trend, format_trend


def add_trend_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "trend",
        help="Show how the outdated-package count has changed over time.",
    )
    p.add_argument(
        "project",
        help="Project name to analyse (must match name stored in history).",
    )
    p.add_argument(
        "--history",
        default="depwatch_history.json",
        metavar="FILE",
        help="Path to the history JSON file (default: depwatch_history.json).",
    )
    p.set_defaults(func=_cmd_trend)


def _cmd_trend(args: argparse.Namespace) -> None:
    summary = build_trend(args.history, args.project)
    if not summary.points:
        print(
            f"No history found for project '{args.project}' in '{args.history}'.",
            file=sys.stderr,
        )
        sys.exit(1)
    print(format_trend(summary))


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        prog="depwatch-trend",
        description="Show outdated-package trend for a depwatch-monitored project.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_trend_subcommand(subparsers)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
