"""Classify packages by their update urgency and category."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class ClassifiedPackage:
    name: str
    current_version: str
    latest_version: str
    category: str  # 'security', 'major', 'minor', 'patch', 'current'
    project_type: str

    def __str__(self) -> str:
        return f"{self.name} ({self.current_version} -> {self.latest_version}) [{self.category}]"


@dataclass
class ClassificationReport:
    project: str
    packages: List[ClassifiedPackage]

    @property
    def by_category(self) -> dict:
        result: dict = {}
        for pkg in self.packages:
            result.setdefault(pkg.category, []).append(pkg)
        return result

    @property
    def has_security(self) -> bool:
        return any(p.category == "security" for p in self.packages)

    def __str__(self) -> str:
        lines = [f"Classification report for {self.project}:"]
        for cat, pkgs in self.by_category.items():
            lines.append(f"  [{cat}] {', '.join(p.name for p in pkgs)}")
        return "\n".join(lines)


def _detect_category(pkg: PackageStatus) -> str:
    """Derive a category string from a PackageStatus."""
    if pkg.is_outdated is False:
        return "current"
    cur = pkg.current_version or "0.0.0"
    lat = pkg.latest_version or "0.0.0"
    try:
        cur_parts = [int(x) for x in cur.lstrip("v").split(".")[:3]]
        lat_parts = [int(x) for x in lat.lstrip("v").split(".")[:3]]
        while len(cur_parts) < 3:
            cur_parts.append(0)
        while len(lat_parts) < 3:
            lat_parts.append(0)
        if lat_parts[0] > cur_parts[0]:
            return "major"
        if lat_parts[1] > cur_parts[1]:
            return "minor"
        if lat_parts[2] > cur_parts[2]:
            return "patch"
    except (ValueError, AttributeError):
        pass
    return "unknown"


def classify_result(result: CheckResult, security_packages: List[str] | None = None) -> ClassificationReport:
    """Classify all packages in a CheckResult."""
    flagged = set(security_packages or [])
    classified = []
    for pkg in result.packages:
        if pkg.name in flagged:
            category = "security"
        else:
            category = _detect_category(pkg)
        classified.append(
            ClassifiedPackage(
                name=pkg.name,
                current_version=pkg.current_version or "",
                latest_version=pkg.latest_version or "",
                category=category,
                project_type=result.project_type,
            )
        )
    return ClassificationReport(project=result.project, packages=classified)


def format_classification(report: ClassificationReport) -> str:
    """Return a human-readable classification summary."""
    if not report.packages:
        return f"{report.project}: no packages to classify."
    lines = [str(report)]
    total = len(report.packages)
    outdated = sum(1 for p in report.packages if p.category != "current")
    lines.append(f"  Total: {total}, Outdated: {outdated}")
    return "\n".join(lines)
