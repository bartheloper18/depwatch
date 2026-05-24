"""ranker.py – rank packages by urgency of update.

Each package is assigned a numeric urgency score (0–100) and a priority
label (critical / high / medium / low) based on how far behind it is.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class RankedPackage:
    package: PackageStatus
    urgency: int          # 0-100
    priority: str         # critical | high | medium | low

    def __str__(self) -> str:
        return (
            f"{self.package.name} {self.package.current_version} -> "
            f"{self.package.latest_version}  "
            f"[{self.priority.upper()} urgency={self.urgency}]"
        )


def _urgency_score(pkg: PackageStatus) -> int:
    """Return 0-100 urgency score.  Up-to-date packages score 0."""
    if not pkg.is_outdated:
        return 0

    current = pkg.current_version or "0.0.0"
    latest = pkg.latest_version or "0.0.0"

    def _parts(v: str) -> List[int]:
        parts = []
        for seg in v.split(".")[:3]:
            try:
                parts.append(int(seg))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return parts

    cur = _parts(current)
    lat = _parts(latest)

    major_diff = max(lat[0] - cur[0], 0)
    minor_diff = max(lat[1] - cur[1], 0) if lat[0] == cur[0] else 0
    patch_diff = (
        max(lat[2] - cur[2], 0)
        if lat[0] == cur[0] and lat[1] == cur[1]
        else 0
    )

    score = min(major_diff * 40 + minor_diff * 10 + patch_diff * 2, 100)
    return max(score, 5)   # outdated packages always score at least 5


def _priority_label(urgency: int) -> str:
    if urgency >= 70:
        return "critical"
    if urgency >= 40:
        return "high"
    if urgency >= 15:
        return "medium"
    return "low"


def rank_result(result: CheckResult) -> List[RankedPackage]:
    """Return outdated packages sorted by descending urgency."""
    ranked = []
    for pkg in result.packages:
        if not pkg.is_outdated:
            continue
        score = _urgency_score(pkg)
        ranked.append(
            RankedPackage(
                package=pkg,
                urgency=score,
                priority=_priority_label(score),
            )
        )
    ranked.sort(key=lambda r: r.urgency, reverse=True)
    return ranked


def format_ranking(ranked: List[RankedPackage]) -> str:
    """Human-readable ranked list."""
    if not ranked:
        return "All packages are up-to-date."
    lines = ["Packages ranked by urgency:", ""]
    for i, rp in enumerate(ranked, 1):
        lines.append(f"  {i:>2}. {rp}")
    return "\n".join(lines)
