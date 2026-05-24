"""CLI sub-command: throttler — inspect or reset throttle state."""
from __future__ import annotations

import argparse
import sys

from depwatch.throttler import Throttler

# Module-level shared throttler (re-used by __main__ and other CLI helpers).
_global_throttler = Throttler(rate=1.0, capacity=3.0)


def add_throttler_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("throttler", help="Inspect or reset the run throttler.")
    p.add_argument(
        "--reset",
        metavar="KEY",
        default=None,
        help="Reset the token bucket for KEY (or 'all').",
    )
    p.add_argument(
        "--check",
        metavar="KEY",
        default=None,
        help="Print whether KEY is currently allowed.",
    )
    p.set_defaults(func=_cmd_throttler)


def _cmd_throttler(args: argparse.Namespace, throttler: Throttler = _global_throttler) -> int:
    if args.reset:
        if args.reset == "all":
            throttler.reset_all()
            print("All throttle buckets reset.")
        else:
            throttler.reset(args.reset)
            print(f"Throttle bucket '{args.reset}' reset.")
        return 0

    if args.check:
        allowed = throttler.allow(args.check)
        status = "allowed" if allowed else "throttled"
        print(f"Key '{args.check}': {status}")
        return 0

    # Default: list tracked keys
    keys = throttler.tracked_keys
    if not keys:
        print("No throttle buckets active.")
    else:
        print("Active throttle keys:")
        for k in keys:
            print(f"  {k}")
    return 0


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-throttler")
    subs = parser.add_subparsers()
    add_throttler_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))
