"""CLI subcommand: watchdog — start an interactive file-watch session.

Usage:
    depwatch watchdog --roots /path/to/project [/other/project] [--verbose]
"""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import List

from depwatch.watchdog_integration import WatchEvent, create_session, emit_event
from depwatch.watcher import FileWatcher

logger = logging.getLogger(__name__)


def _on_event(event: WatchEvent) -> None:
    print(f"[depwatch] Change detected: {event}")


def add_watchdog_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "watchdog",
        help="Watch dependency files for changes interactively",
    )
    p.add_argument(
        "--roots",
        nargs="+",
        required=True,
        metavar="DIR",
        help="One or more project root directories to watch",
    )
    p.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose logging",
    )
    p.set_defaults(func=_cmd_watchdog)


def _cmd_watchdog(args: argparse.Namespace) -> int:
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    roots: List[Path] = [Path(r) for r in args.roots]
    for root in roots:
        if not root.exists():
            print(f"[depwatch] ERROR: root does not exist: {root}", file=sys.stderr)
            return 1

    session = create_session(roots=roots, callback=_on_event)
    watcher = FileWatcher(roots=[str(r) for r in roots], on_change=lambda p: emit_event(session, Path(p)))

    print(f"[depwatch] Watching {len(roots)} root(s). Press Ctrl+C to stop.")
    watcher.start()

    def _stop(sig, frame):  # type: ignore[no-untyped-def]
        print("\n[depwatch] Stopping watchdog...")
        session.deactivate()
        watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    signal.pause()  # type: ignore[attr-defined]
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-watchdog")
    subs = parser.add_subparsers(dest="command")
    add_watchdog_subcommand(subs)
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    main()
