"""auditor.py – Audit a CheckResult for known vulnerability patterns.

A lightweight heuristic auditor: packages that are more than one major
version behind are flagged as *critical*; packages that are one major version
behind are flagged as *high*; minor/patch lags are *low*.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class AuditFinding:
    project: str
    package: str
    current_version: str
    latest_version: str
    severity: str  # "critical" | "high" | "low"

    def __str__(self) -> str:
        return (
            f"[{self.severity.upper()}] {self.project}/{self.package} "
            f"{self.current_version} -> {self.latest_version}"
        )


@dataclass
class AuditReport:
    findings: List[AuditFinding] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        return any(f.severity == "critical" for f in self.findings)

    @property
    def has_high(self) -> bool:
        return any(f.severity == "high" for f in self.findings)

    def __str__(self) -> str:
        if not self.findings:
            return "Audit clean – no findings."
        lines = [str(f) for f in self.findings]
        return "\n".join(lines)


def _major(version: str) -> int:
    """Return the major component of a version string, or 0 on failure."""
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError):
        return 0


def _severity(pkg: PackageStatus) -> str:
    current_major = _major(pkg.current_version)
    latest_major = _major(pkg.latest_version)
    gap = latest_major - current_major
    if gap >= 2:
        return "critical"
    if gap == 1:
        return "high"
    return "low"


def audit_result(result: CheckResult) -> AuditReport:
    """Produce an AuditReport from a single CheckResult."""
    findings: List[AuditFinding] = []
    for pkg in result.packages:
        if pkg.is_outdated:
            findings.append(
                AuditFinding(
                    project=result.project,
                    package=pkg.name,
                    current_version=pkg.current_version,
                    latest_version=pkg.latest_version,
                    severity=_severity(pkg),
                )
            )
    return AuditReport(findings=findings)


def format_audit(report: AuditReport) -> str:
    """Return a human-readable string for the audit report."""
    return str(report)
