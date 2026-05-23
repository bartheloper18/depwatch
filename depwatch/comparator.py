"""comparator.py – compare two CheckResults to produce a structured delta report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class PackageChange:
    name: str
    project: str
    old_version: Optional[str]
    new_version: Optional[str]
    was_outdated: bool
    is_outdated: bool

    def __str__(self) -> str:
        direction = "unchanged"
        if not self.was_outdated and self.is_outdated:
            direction = "became outdated"
        elif self.was_outdated and not self.is_outdated:
            direction = "resolved"
        elif self.was_outdated and self.is_outdated:
            if self.old_version != self.new_version:
                direction = "version changed (still outdated)"
        return (
            f"{self.name} ({self.project}): "
            f"{self.old_version} -> {self.new_version} [{direction}]"
        )


@dataclass
class ComparisonReport:
    newly_outdated: List[PackageChange] = field(default_factory=list)
    resolved: List[PackageChange] = field(default_factory=list)
    version_changed: List[PackageChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.newly_outdated or self.resolved or self.version_changed)

    def __str__(self) -> str:
        lines: List[str] = []
        if self.newly_outdated:
            lines.append("Newly outdated:")
            lines.extend(f"  {c}" for c in self.newly_outdated)
        if self.resolved:
            lines.append("Resolved:")
            lines.extend(f"  {c}" for c in self.resolved)
        if self.version_changed:
            lines.append("Version changed (still outdated):")
            lines.extend(f"  {c}" for c in self.version_changed)
        return "\n".join(lines) if lines else "No changes detected."


def _index(result: CheckResult) -> Dict[str, PackageStatus]:
    """Build a (project, name) -> PackageStatus index from a CheckResult."""
    return {(ps.project, ps.name): ps for ps in result.packages}


def compare_results(before: CheckResult, after: CheckResult) -> ComparisonReport:
    """Compare two CheckResults and return a ComparisonReport."""
    before_idx = _index(before)
    after_idx = _index(after)

    report = ComparisonReport()
    all_keys = set(before_idx) | set(after_idx)

    for key in sorted(all_keys):
        project, name = key
        b = before_idx.get(key)
        a = after_idx.get(key)

        b_outdated = b.outdated if b else False
        a_outdated = a.outdated if a else False
        b_ver = b.current_version if b else None
        a_ver = a.current_version if a else None

        change = PackageChange(
            name=name,
            project=project,
            old_version=b_ver,
            new_version=a_ver,
            was_outdated=b_outdated,
            is_outdated=a_outdated,
        )

        if not b_outdated and a_outdated:
            report.newly_outdated.append(change)
        elif b_outdated and not a_outdated:
            report.resolved.append(change)
        elif b_outdated and a_outdated and b_ver != a_ver:
            report.version_changed.append(change)

    return report
