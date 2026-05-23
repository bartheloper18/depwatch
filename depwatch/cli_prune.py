"""CLI sub-command: prune — remove old history entries."""

from __future__ import annotations

import argparse
import sys

from depwatch.config import load_config
from depwatch.pruner import DEFAULT_MAX_AGE_DAYS, DEFAULT_MAX_ENTRIES, prune_history


def add_prune_subcommand(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    parser = subparsers.add_parser(
        "prune",
        help="Remove old entries from the history file.",
    )
    parser.add_argument(
        "--config",
        default="depwatch.json",
        metavar="FILE",
        help="Path to depwatch config file (default: depwatch.json).",
    )
    parser.add_argument(
        "--max-entries",
        type=int,
        default=DEFAULT_MAX_ENTRIES,
        metavar="N",
        help=f"Keep at most N entries per history file (default: {DEFAULT_MAX_ENTRIES}).",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        metavar="DAYS",
        help=f"Remove entries older than DAYS days (default: {DEFAULT_MAX_AGE_DAYS}).",
    )
    parser.set_defaults(func=_cmd_prune)


def _cmd_prune(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    history_path = cfg.history_path

    removed = prune_history(
        history_path,
        max_entries=args.max_entries,
        max_age_days=args.max_age_days,
    )

    if removed:
        print(f"Pruned {removed} old entr{'y' if removed == 1 else 'ies'} from {history_path}.")
    else:
        print(f"Nothing to prune in {history_path}.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="depwatch-prune",
        description="Prune old depwatch history entries.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_prune_subcommand(subparsers)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
