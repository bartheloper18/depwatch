"""Remediation advice generator for outdated/vulnerable packages."""

from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus
from depwatch.scanner import ProjectType


@dataclass
class RemediationAdvice:
    project_name: str
    project_type: ProjectType
    package: str
    current_version: str
    latest_version: str
    command: str

    def __str__(self) -> str:
        return (
            f"[{self.project_name}] {self.package} "
            f"{self.current_version} -> {self.latest_version}: "
            f"`{self.command}`"
        )


def _upgrade_command(project_type: ProjectType, package: str, version: str) -> str:
    """Return the shell command to upgrade a package to the latest version."""
    if project_type == ProjectType.PYTHON:
        return f"pip install --upgrade {package}=={version}"
    if project_type == ProjectType.NODE:
        return f"npm install {package}@{version}"
    return f"# unknown project type for {package}"


def generate_advice(result: CheckResult) -> List[RemediationAdvice]:
    """Generate remediation advice for all outdated packages in a CheckResult."""
    advice: List[RemediationAdvice] = []
    for status in result.outdated_packages:
        if status.latest_version is None:
            continue
        cmd = _upgrade_command(result.project_type, status.package, status.latest_version)
        advice.append(
            RemediationAdvice(
                project_name=result.project_name,
                project_type=result.project_type,
                package=status.package,
                current_version=status.current_version,
                latest_version=status.latest_version,
                command=cmd,
            )
        )
    return advice


def format_advice(advice: List[RemediationAdvice]) -> str:
    """Format a list of remediation advice items as a human-readable string."""
    if not advice:
        return "No remediation needed — all packages are up to date."
    lines = ["Remediation advice:", ""]
    for item in advice:
        lines.append(f"  {item}")
    return "\n".join(lines)
