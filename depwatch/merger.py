"""merger.py – merge multiple CheckResult objects into a unified report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class MergedReport:
    """Aggregated view across multiple CheckResult objects."""

    results: List[CheckResult] = field(default_factory=list)

    @property
    def total_projects(self) -> int:
        return len(self.results)

    @property
    def total_packages(self) -> int:
        return sum(len(r.packages) for r in self.results)

    @property
    def total_outdated(self) -> int:
        return sum(len(r.outdated_packages) for r in self.results)

    @property
    def projects_with_issues(self) -> List[str]:
        return [r.project_name for r in self.results if r.has_outdated]

    def packages_by_project(self) -> Dict[str, List[PackageStatus]]:
        return {r.project_name: r.packages for r in self.results}

    def __str__(self) -> str:  # pragma: no cover
        lines = [
            f"MergedReport: {self.total_projects} project(s), "
            f"{self.total_outdated}/{self.total_packages} outdated"
        ]
        for r in self.results:
            flag = "[!]" if r.has_outdated else "[ok]"
            lines.append(f"  {flag} {r.project_name}")
        return "\n".join(lines)


def merge_results(results: List[CheckResult]) -> MergedReport:
    """Combine a list of CheckResult objects into a MergedReport."""
    return MergedReport(results=list(results))


def format_merged(report: MergedReport, fmt: str = "text") -> str:
    """Render a MergedReport as text or csv."""
    if fmt == "csv":
        lines = ["project,total,outdated"]
        for r in report.results:
            lines.append(f"{r.project_name},{len(r.packages)},{len(r.outdated_packages)}")
        return "\n".join(lines)

    # default: text
    lines = [
        f"Merged report — {report.total_projects} project(s)",
        f"Total packages : {report.total_packages}",
        f"Total outdated : {report.total_outdated}",
    ]
    if report.projects_with_issues:
        lines.append("Projects with issues:")
        for name in report.projects_with_issues:
            lines.append(f"  • {name}")
    else:
        lines.append("All projects up to date.")
    return "\n".join(lines)
