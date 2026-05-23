"""annotator.py – attach human-readable annotations to PackageStatus entries.

Annotations enrich a CheckResult with short notes explaining *why* a package
is considered outdated (major bump, minor bump, patch, or unknown) and whether
it has a known CVE placeholder flag set by the checker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class Annotation:
    package: str
    project: str
    note: str
    tags: List[str] = field(default_factory=list)

    def __str__(self) -> str:  # pragma: no cover
        tag_str = f" [{', '.join(self.tags)}]" if self.tags else ""
        return f"{self.project}/{self.package}: {self.note}{tag_str}"


def _bump_type(current: str, latest: str) -> str:
    """Return 'major', 'minor', 'patch', or 'unknown' based on version strings."""
    try:
        cur_parts = [int(x) for x in current.lstrip("v").split(".")[:3]]
        lat_parts = [int(x) for x in latest.lstrip("v").split(".")[:3]]
        # Pad to length 3
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
        return "unknown"
    except (ValueError, AttributeError):
        return "unknown"


def annotate_result(result: CheckResult) -> List[Annotation]:
    """Return a list of Annotation objects for every outdated package in *result*."""
    annotations: List[Annotation] = []
    for pkg in result.outdated_packages:
        bump = _bump_type(pkg.current_version, pkg.latest_version)
        note = f"outdated ({bump} bump): {pkg.current_version} -> {pkg.latest_version}"
        tags = [bump]
        if getattr(pkg, "vulnerable", False):
            tags.append("vulnerable")
        annotations.append(
            Annotation(package=pkg.name, project=result.project, note=note, tags=tags)
        )
    return annotations


def format_annotations(annotations: List[Annotation]) -> str:
    """Return a plain-text block summarising all annotations."""
    if not annotations:
        return "No annotations."
    lines = [str(a) for a in annotations]
    return "\n".join(lines)
