"""Filter CheckResult packages by various criteria."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class FilterCriteria:
    """Criteria used to filter packages from a CheckResult."""
    only_outdated: bool = False
    name_contains: Optional[str] = None
    project_types: List[str] = field(default_factory=list)
    min_bump: Optional[str] = None  # "patch", "minor", "major"


def _bump_level(pkg: PackageStatus) -> int:
    """Return a numeric bump level for comparison (0=none, 1=patch, 2=minor, 3=major)."""
    if not pkg.is_outdated:
        return 0
    try:
        cur = [int(x) for x in pkg.current_version.split(".")]
        lat = [int(x) for x in pkg.latest_version.split(".")]
    except (ValueError, AttributeError):
        return 1
    cur += [0] * (3 - len(cur))
    lat += [0] * (3 - len(lat))
    if lat[0] > cur[0]:
        return 3
    if lat[1] > cur[1]:
        return 2
    return 1


_BUMP_ORDER = {"patch": 1, "minor": 2, "major": 3}


def filter_result(result: CheckResult, criteria: FilterCriteria) -> CheckResult:
    """Return a new CheckResult containing only packages matching *criteria*."""
    packages = list(result.packages)

    if criteria.only_outdated:
        packages = [p for p in packages if p.is_outdated]

    if criteria.name_contains:
        needle = criteria.name_contains.lower()
        packages = [p for p in packages if needle in p.name.lower()]

    if criteria.min_bump:
        threshold = _BUMP_ORDER.get(criteria.min_bump.lower(), 1)
        packages = [p for p in packages if _bump_level(p) >= threshold]

    filtered = CheckResult(
        project_name=result.project_name,
        project_type=result.project_type,
        packages=packages,
        checked_at=result.checked_at,
    )

    if criteria.project_types:
        if result.project_type not in criteria.project_types:
            filtered = CheckResult(
                project_name=result.project_name,
                project_type=result.project_type,
                packages=[],
                checked_at=result.checked_at,
            )

    return filtered


def format_filtered(result: CheckResult) -> str:
    """Return a human-readable summary of a filtered CheckResult."""
    if not result.packages:
        return f"[{result.project_name}] No packages match the filter criteria."
    lines = [f"[{result.project_name}] Filtered packages ({len(result.packages)}):\n"]
    for pkg in result.packages:
        lines.append(f"  {pkg}")
    return "\n".join(lines)
