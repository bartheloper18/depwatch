"""CLI helper that prints a summary digest, wired into __main__.py via build_parser."""

from __future__ import annotations

import argparse
import sys

from depwatch.config import load_config
from depwatch.summary import format_summary


def add_summary_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the 'summary' subcommand on an existing subparsers object."""
    parser = subparsers.add_parser(
        "summary",
        help="Print a digest of recorded check history.",
    )
    parser.add_argument(
        "--config",
        default="depwatch.toml",
        metavar="FILE",
        help="Path to depwatch config file (default: depwatch.toml).",
    )
    parser.add_argument(
        "--history",
        default=None,
        metavar="FILE",
        help="Override path to history JSON file.",
    )
    parser.set_defaults(func=_cmd_summary)


def _cmd_summary(args: argparse.Namespace) -> int:
    """Handler for the 'summary' subcommand. Returns an exit code."""
    history_path = args.history
    if history_path is None:
        try:
            cfg = load_config(args.config)
            history_path = cfg.history_path
        except FileNotFoundError:
            print(
                f"Config file '{args.config}' not found and --history not specified.",
                file=sys.stderr,
            )
            return 1

    print(format_summary(history_path))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Standalone entry point for the summary command."""
    parser = argparse.ArgumentParser(
        prog="depwatch-summary",
        description="Print a digest of depwatch check history.",
    )
    parser.add_argument(
        "--config",
        default="depwatch.toml",
        metavar="FILE",
        help="Path to depwatch config file (default: depwatch.toml).",
    )
    parser.add_argument(
        "--history",
        default=None,
        metavar="FILE",
        help="Override path to history JSON file.",
    )
    parsed = parser.parse_args(argv)
    return _cmd_summary(parsed)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
