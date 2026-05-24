"""highlighter.py – highlight packages that exceed a staleness threshold.

A package is considered 'stale' when the version gap between its installed
version and the latest available version crosses a configurable threshold
(major, minor, or patch level).  This module wraps a CheckResult and
produces a HighlightedResult that tags every package accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class HighlightedPackage:
    name: str
    current: str
    latest: str
    is_outdated: bool
    stale: bool  # True when the version gap meets/exceeds the threshold
    highlight_reason: str  # e.g. "major bump", "minor bump", "patch bump", ""

    def __str__(self) -> str:
        if self.stale:
            return f"{self.name} {self.current} -> {self.latest} [{self.highlight_reason}]"
        return f"{self.name} {self.current} (current)"


@dataclass
class HighlightedResult:
    project: str
    project_type: str
    packages: List[HighlightedPackage] = field(default_factory=list)

    @property
    def stale_packages(self) -> List[HighlightedPackage]:
        return [p for p in self.packages if p.stale]

    @property
    def has_stale(self) -> bool:
        return bool(self.stale_packages)

    def __str__(self) -> str:
        lines = [f"Project: {self.project} ({self.project_type})"]
        if not self.has_stale:
            lines.append("  No stale packages.")
        else:
            for pkg in self.stale_packages:
                lines.append(f"  {pkg}")
        return "\n".join(lines)


def _parse_version(version: str) -> tuple:
    """Return (major, minor, patch) integers, best-effort."""
    clean = version.lstrip("^~>=<v")
    parts = clean.split(".")
    result = []
    for p in parts[:3]:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _highlight_reason(current: str, latest: str) -> str:
    c = _parse_version(current)
    l = _parse_version(latest)
    if l[0] > c[0]:
        return "major bump"
    if l[1] > c[1]:
        return "minor bump"
    if l[2] > c[2]:
        return "patch bump"
    return ""


def highlight_result(
    result: CheckResult,
    threshold: str = "major",
) -> HighlightedResult:
    """Wrap *result* and mark packages stale based on *threshold*.

    threshold values: "major", "minor", "patch"  (inclusive – e.g. "minor"
    flags both minor and major bumps).
    """
    _order = {"major": 0, "minor": 1, "patch": 2}
    threshold_rank = _order.get(threshold, 0)

    highlighted: List[HighlightedPackage] = []
    for pkg in result.packages:
        reason = _highlight_reason(pkg.current_version, pkg.latest_version) if pkg.is_outdated else ""
        reason_rank = _order.get(reason.split()[0], -1) if reason else -1
        stale = pkg.is_outdated and reason_rank <= threshold_rank and reason != ""
        highlighted.append(
            HighlightedPackage(
                name=pkg.name,
                current=pkg.current_version,
                latest=pkg.latest_version,
                is_outdated=pkg.is_outdated,
                stale=stale,
                highlight_reason=reason if stale else "",
            )
        )

    return HighlightedResult(
        project=result.project,
        project_type=result.project_type,
        packages=highlighted,
    )


def format_highlights(hr: HighlightedResult) -> str:
    return str(hr)
