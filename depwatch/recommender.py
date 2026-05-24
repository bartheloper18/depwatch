"""recommender.py – Suggests upgrade priority order for outdated packages.

For each outdated package, a recommendation is generated that combines
bump severity, number of versions behind, and project type to produce
an ordered action list.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class Recommendation:
    package: str
    current: str
    latest: str
    project_type: str
    priority: int          # lower = more urgent
    reason: str

    def __str__(self) -> str:
        return (
            f"[P{self.priority}] {self.package} "
            f"{self.current} -> {self.latest} "
            f"({self.project_type}): {self.reason}"
        )


@dataclass
class RecommendationReport:
    project: str
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def has_recommendations(self) -> bool:
        return bool(self.recommendations)

    def __str__(self) -> str:
        if not self.recommendations:
            return f"{self.project}: no upgrades recommended"
        lines = [f"{self.project} – upgrade recommendations:"]
        for rec in self.recommendations:
            lines.append(f"  {rec}")
        return "\n".join(lines)


def _priority(pkg: PackageStatus) -> int:
    """Return a priority integer (1=critical, 2=moderate, 3=low)."""
    try:
        cur = [int(x) for x in pkg.current_version.lstrip("v^").split(".")]
        lat = [int(x) for x in pkg.latest_version.lstrip("v^").split(".")]
    except (ValueError, AttributeError):
        return 2
    if len(cur) < 1 or len(lat) < 1:
        return 2
    if lat[0] > cur[0]:
        return 1
    if len(lat) > 1 and len(cur) > 1 and lat[1] > cur[1]:
        return 2
    return 3


def _reason(priority: int) -> str:
    return {1: "major version bump – breaking changes likely",
            2: "minor version bump – new features available",
            3: "patch bump – bug fixes available"}.get(priority, "update available")


def recommend(result: CheckResult) -> RecommendationReport:
    """Build a RecommendationReport from a CheckResult."""
    recs: List[Recommendation] = []
    for pkg in result.packages:
        if not pkg.is_outdated:
            continue
        p = _priority(pkg)
        recs.append(Recommendation(
            package=pkg.name,
            current=pkg.current_version,
            latest=pkg.latest_version,
            project_type=result.project_type,
            priority=p,
            reason=_reason(p),
        ))
    recs.sort(key=lambda r: r.priority)
    return RecommendationReport(project=result.project, recommendations=recs)


def format_recommendations(report: RecommendationReport) -> str:
    return str(report)
