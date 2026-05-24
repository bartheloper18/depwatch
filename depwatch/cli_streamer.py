"""cli_streamer.py – 'depwatch stream' subcommand."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from depwatch.history import load_history
from depwatch.checker import CheckResult, PackageStatus
from depwatch.streamer import stream_results, read_stream


def _result_from_entry(entry: dict) -> CheckResult:
    packages = [
        PackageStatus(
            name=p["name"],
            current_version=p["current"],
            latest_version=p["latest"],
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(project=entry.get("project", "unknown"), packages=packages)


def add_streamer_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("stream", help="Stream check results as newline-delimited JSON")
    p.add_argument("--history", default=".depwatch_history.json", help="History file to read from")
    p.add_argument("--out", default=None, help="Output file (default: stdout)")
    p.add_argument("--append", action="store_true", help="Append to output file instead of overwriting")
    p.add_argument("--read", default=None, help="Read and pretty-print an existing stream file")
    p.set_defaults(func=_cmd_streamer)


def _cmd_streamer(args: argparse.Namespace) -> int:
    if args.read:
        path = Path(args.read)
        entries = read_stream(path)
        if not entries:
            print("No entries found.", file=sys.stderr)
            return 0
        for e in entries:
            ts = e.timestamp
            print(f"[{ts}] {e.project}: {e.outdated}/{e.total} outdated")
        return 0

    hist_path = Path(args.history)
    history = load_history(hist_path)
    if not history:
        print("No history entries found.", file=sys.stderr)
        return 1

    latest = history[-1]
    results = [_result_from_entry(latest)]
    dest = Path(args.out) if args.out else None
    stream_results(results, dest=dest, append=args.append)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="depwatch-stream")
    subs = parser.add_subparsers()
    add_streamer_subcommand(subs)
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
