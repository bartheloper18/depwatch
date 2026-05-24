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


def _resolve_history_path(args: argparse.Namespace) -> tuple[str | None, int]:
    """Resolve the history file path from args or config.

    Returns a (path, exit_code) tuple. If exit_code is non-zero, path will be
    None and the caller should propagate the error.
    """
    if args.history is not None:
        return args.history, 0

    try:
        cfg = load_config(args.config)
        return cfg.history_path, 0
    except FileNotFoundError:
        print(
            f"Config file '{args.config}' not found and --history not specified.",
            file=sys.stderr,
        )
        return None, 1


def _cmd_summary(args: argparse.Namespace) -> int:
    """Handler for the 'summary' subcommand. Returns an exit code."""
    history_path, code = _resolve_history_path(args)
    if code != 0:
        return code

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
