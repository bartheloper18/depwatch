"""deduplicator.py – collapse duplicate package entries across multiple CheckResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class DeduplicatedPackage:
    """A package entry that has been merged from one or more sources."""

    name: str
    current_version: str
    latest_version: str
    is_outdated: bool
    seen_in: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "outdated" if self.is_outdated else "up-to-date"
        projects = ", ".join(self.seen_in)
        return f"{self.name} {self.current_version} -> {self.latest_version} [{status}] (in: {projects})"


@dataclass
class DeduplicatedReport:
    """Report produced after deduplicating packages across multiple CheckResults."""

    packages: List[DeduplicatedPackage] = field(default_factory=list)

    @property
    def total_packages(self) -> int:
        return len(self.packages)

    @property
    def total_outdated(self) -> int:
        return sum(1 for p in self.packages if p.is_outdated)

    @property
    def has_issues(self) -> bool:
        return self.total_outdated > 0

    def __str__(self) -> str:
        lines = [f"DeduplicatedReport: {self.total_packages} unique packages, {self.total_outdated} outdated"]
        for pkg in self.packages:
            lines.append(f"  {pkg}")
        return "\n".join(lines)


def deduplicate_results(results: Sequence[CheckResult]) -> DeduplicatedReport:
    """Merge packages from multiple CheckResults, deduplicating by name.

    When the same package appears in several projects the entry with the
    highest *latest_version* wins (simple lexicographic comparison).  All
    project names are recorded in *seen_in*.
    """
    merged: Dict[str, DeduplicatedPackage] = {}

    for result in results:
        project = result.project_name
        for ps in result.packages:
            key = ps.name.lower()
            if key not in merged:
                merged[key] = DeduplicatedPackage(
                    name=ps.name,
                    current_version=ps.current_version,
                    latest_version=ps.latest_version,
                    is_outdated=ps.is_outdated,
                    seen_in=[project],
                )
            else:
                existing = merged[key]
                if ps.latest_version > existing.latest_version:
                    existing.latest_version = ps.latest_version
                    existing.current_version = ps.current_version
                    existing.is_outdated = ps.is_outdated
                if project not in existing.seen_in:
                    existing.seen_in.append(project)

    return DeduplicatedReport(packages=list(merged.values()))


def format_deduplicated(report: DeduplicatedReport) -> str:
    """Return a human-readable summary of the deduplicated report."""
    if not report.packages:
        return "No packages found across provided results."
    return str(report)
