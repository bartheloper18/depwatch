"""CLI sub-command: depwatch score — show dependency health scores."""
from __future__ import annotations

import argparse
import json
import sys

from depwatch.history import load_history
from depwatch.scorer import score_result, HealthScore
from depwatch.checker import CheckResult, PackageStatus


def _result_from_entry(entry: dict) -> CheckResult:
    pkgs = [
        PackageStatus(
            name=p["name"],
            current=p["current"],
            latest=p["latest"],
            is_outdated=p["is_outdated"],
        )
        for p in entry.get("packages", [])
    ]
    return CheckResult(
        project=entry["project"],
        project_type=entry.get("project_type", "unknown"),
        packages=pkgs,
    )


def _format_score(hs: HealthScore, fmt: str) -> str:
    if fmt == "json":
        data = {
            "project": hs.project,
            "project_type": hs.project_type,
            "overall": round(hs.overall, 4),
            "grade": hs.grade,
            "packages": [
                {"name": ps.name, "score": round(ps.score, 4), "reason": ps.reason}
                for ps in hs.package_scores
            ],
        }
        return json.dumps(data, indent=2)
    # text
    lines = [str(hs)]
    for ps in hs.package_scores:
        lines.append(f"  {ps}")
    return "\n".join(lines)


def add_scorer_subcommand(subparsers) -> None:
    p = subparsers.add_parser("score", help="Show dependency health scores")
    p.add_argument("--history", default=".depwatch_history.json", help="History file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=_cmd_scorer)


def _cmd_scorer(args) -> None:
    history = load_history(args.history)
    if not history:
        print("No history entries found.", file=sys.stderr)
        sys.exit(1)

    latest = history[-1]
    result = _result_from_entry(latest)
    hs = score_result(result)
    print(_format_score(hs, args.format))


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(prog="depwatch-score")
    subs = parser.add_subparsers()
    add_scorer_subcommand(subs)
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
