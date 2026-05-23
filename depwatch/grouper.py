"""Group CheckResult packages by severity or project type for reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class GroupedResult:
    """Packages from a CheckResult partitioned into severity buckets."""

    project_name: str
    critical: List[PackageStatus] = field(default_factory=list)   # major version behind
    moderate: List[PackageStatus] = field(default_factory=list)   # minor version behind
    low: List[PackageStatus] = field(default_factory=list)        # patch version behind
    up_to_date: List[PackageStatus] = field(default_factory=list)

    @property
    def total_outdated(self) -> int:
        return len(self.critical) + len(self.moderate) + len(self.low)

    def __str__(self) -> str:  # pragma: no cover
        return (
            f"GroupedResult({self.project_name}: "
            f"critical={len(self.critical)}, "
            f"moderate={len(self.moderate)}, "
            f"low={len(self.low)}, "
            f"up_to_date={len(self.up_to_date)})"
        )


def _severity(pkg: PackageStatus) -> str:
    """Return 'critical', 'moderate', 'low', or 'up_to_date' for a package."""
    if not pkg.outdated:
        return "up_to_date"

    current = pkg.current_version or ""
    latest = pkg.latest_version or ""

    try:
        cur_major = int(current.lstrip("v").split(".")[0])
        lat_major = int(latest.lstrip("v").split(".")[0])
        if lat_major > cur_major:
            return "critical"

        cur_minor = int(current.lstrip("v").split(".")[1]) if "." in current else 0
        lat_minor = int(latest.lstrip("v").split(".")[1]) if "." in latest else 0
        if lat_minor > cur_minor:
            return "moderate"
    except (ValueError, IndexError):
        return "low"

    return "low"


def group_result(result: CheckResult) -> GroupedResult:
    """Partition packages in *result* into severity buckets."""
    grouped = GroupedResult(project_name=result.project_name)
    for pkg in result.packages:
        sev = _severity(pkg)
        getattr(grouped, sev).append(pkg)
    return grouped


def group_results(results: List[CheckResult]) -> Dict[str, GroupedResult]:
    """Return a mapping of project_name -> GroupedResult for each result."""
    return {r.project_name: group_result(r) for r in results}
