"""Trend analysis: compute how outdated-package counts change over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class TrendPoint:
    """A single data point in a project's outdated-count history."""

    timestamp: str
    outdated_count: int

    def __str__(self) -> str:
        return f"{self.timestamp}: {self.outdated_count} outdated"


@dataclass
class TrendSummary:
    """Trend summary for a single project."""

    project: str
    points: List[TrendPoint]

    @property
    def latest(self) -> Optional[TrendPoint]:
        return self.points[-1] if self.points else None

    @property
    def delta(self) -> Optional[int]:
        """Change in outdated count between first and last point."""
        if len(self.points) < 2:
            return None
        return self.points[-1].outdated_count - self.points[0].outdated_count

    @property
    def direction(self) -> str:
        d = self.delta
        if d is None:
            return "stable"
        if d > 0:
            return "worsening"
        if d < 0:
            return "improving"
        return "stable"


def build_trend(history_path: str, project: str) -> TrendSummary:
    """Build a TrendSummary for *project* from the history file."""
    entries = load_history(history_path)
    points: List[TrendPoint] = []
    for entry in entries:
        if entry.get("project") != project:
            continue
        ts = entry.get("timestamp", "")
        pkgs = entry.get("packages", [])
        outdated = sum(1 for p in pkgs if p.get("status") == "outdated")
        points.append(TrendPoint(timestamp=ts, outdated_count=outdated))
    return TrendSummary(project=project, points=points)


def format_trend(summary: TrendSummary) -> str:
    """Return a human-readable trend report."""
    lines = [f"Trend for '{summary.project}' ({len(summary.points)} entries):"]
    if not summary.points:
        lines.append("  No data available.")
        return "\n".join(lines)
    for pt in summary.points:
        lines.append(f"  {pt}")
    lines.append(f"Direction : {summary.direction}")
    if summary.delta is not None:
        sign = "+" if summary.delta >= 0 else ""
        lines.append(f"Delta     : {sign}{summary.delta}")
    return "\n".join(lines)
