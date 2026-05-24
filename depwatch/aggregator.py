"""Aggregates multiple CheckResults into a unified cross-project summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class ProjectAggregate:
    project: str
    total: int
    outdated: int
    up_to_date: int

    def __str__(self) -> str:  # noqa: D105
        return (
            f"{self.project}: {self.outdated}/{self.total} outdated"
        )


@dataclass
class AggregateReport:
    projects: List[ProjectAggregate] = field(default_factory=list)

    @property
    def total_projects(self) -> int:
        return len(self.projects)

    @property
    def total_outdated(self) -> int:
        return sum(p.outdated for p in self.projects)

    @property
    def total_packages(self) -> int:
        return sum(p.total for p in self.projects)

    @property
    def has_issues(self) -> bool:
        return self.total_outdated > 0

    def __str__(self) -> str:  # noqa: D105
        lines = [f"Aggregate report ({self.total_projects} projects):"]
        for p in self.projects:
            lines.append(f"  {p}")
        lines.append(
            f"Total: {self.total_outdated}/{self.total_packages} outdated"
        )
        return "\n".join(lines)


def _aggregate_one(result: CheckResult) -> ProjectAggregate:
    outdated = [s for s in result.packages if s.is_outdated]
    return ProjectAggregate(
        project=result.project,
        total=len(result.packages),
        outdated=len(outdated),
        up_to_date=len(result.packages) - len(outdated),
    )


def aggregate_results(results: List[CheckResult]) -> AggregateReport:
    """Build an AggregateReport from a list of CheckResults."""
    return AggregateReport(projects=[_aggregate_one(r) for r in results])


def format_aggregate(report: AggregateReport, fmt: str = "text") -> str:
    """Render an AggregateReport as text or csv."""
    if fmt == "csv":
        rows = ["project,total,outdated,up_to_date"]
        for p in report.projects:
            rows.append(f"{p.project},{p.total},{p.outdated},{p.up_to_date}")
        return "\n".join(rows)
    return str(report)
