"""Dependency health scorer — assigns a numeric health score to a CheckResult."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class PackageScore:
    name: str
    version: str
    latest: str
    score: float          # 0.0 (worst) – 1.0 (best)
    reason: str

    def __str__(self) -> str:
        return f"{self.name}: {self.score:.2f} ({self.reason})"


@dataclass
class HealthScore:
    project: str
    project_type: str
    overall: float        # weighted average, 0.0 – 1.0
    package_scores: List[PackageScore]

    @property
    def grade(self) -> str:
        if self.overall >= 0.9:
            return "A"
        if self.overall >= 0.75:
            return "B"
        if self.overall >= 0.5:
            return "C"
        if self.overall >= 0.25:
            return "D"
        return "F"

    def __str__(self) -> str:
        return (
            f"{self.project} [{self.project_type}] "
            f"score={self.overall:.2f} grade={self.grade}"
        )


def _score_package(pkg: PackageStatus) -> PackageScore:
    """Return a score for a single package based on version bump magnitude."""
    if not pkg.is_outdated:
        return PackageScore(pkg.name, pkg.current, pkg.latest, 1.0, "up-to-date")

    def _parts(v: str):
        parts = v.lstrip("v").split(".")
        result = []
        for p in parts[:3]:
            try:
                result.append(int(p))
            except ValueError:
                result.append(0)
        while len(result) < 3:
            result.append(0)
        return result

    try:
        cur = _parts(pkg.current)
        lat = _parts(pkg.latest)
    except Exception:
        return PackageScore(pkg.name, pkg.current, pkg.latest, 0.0, "unparseable versions")

    if lat[0] > cur[0]:
        return PackageScore(pkg.name, pkg.current, pkg.latest, 0.1, "major bump")
    if lat[1] > cur[1]:
        return PackageScore(pkg.name, pkg.current, pkg.latest, 0.5, "minor bump")
    if lat[2] > cur[2]:
        return PackageScore(pkg.name, pkg.current, pkg.latest, 0.8, "patch bump")
    return PackageScore(pkg.name, pkg.current, pkg.latest, 0.9, "pre-release drift")


def score_result(result: CheckResult) -> HealthScore:
    """Compute an overall HealthScore for a CheckResult."""
    if not result.packages:
        return HealthScore(result.project, result.project_type, 1.0, [])

    pkg_scores = [_score_package(p) for p in result.packages]
    overall = sum(ps.score for ps in pkg_scores) / len(pkg_scores)
    return HealthScore(result.project, result.project_type, overall, pkg_scores)
