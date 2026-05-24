"""sanitizer.py – strips and normalises raw package version strings
before they reach downstream modules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus

# Matches common prefixes such as ^1.2.3, ~1.2.3, >=1.2.3, v1.2.3
_PREFIX_RE = re.compile(r"^[\^~>=<v]+")
# Matches build metadata / pre-release suffixes, e.g. 1.2.3-beta.1+build.42
_SUFFIX_RE = re.compile(r"[-+].+$")


def _clean(version: str) -> str:
    """Return a plain MAJOR.MINOR.PATCH string, stripping range operators
    and pre-release / build-metadata suffixes."""
    v = version.strip()
    v = _PREFIX_RE.sub("", v)
    v = _SUFFIX_RE.sub("", v)
    return v or version  # fall back to original if result is empty


@dataclass
class SanitizedPackage:
    name: str
    current_version: str
    latest_version: str
    is_outdated: bool
    original_current: str
    original_latest: str

    def __str__(self) -> str:
        marker = "OUTDATED" if self.is_outdated else "ok"
        return (
            f"{self.name}: {self.current_version} -> {self.latest_version} [{marker}]"
        )


@dataclass
class SanitizedResult:
    project_name: str
    project_type: str
    packages: List[SanitizedPackage]

    @property
    def outdated(self) -> List[SanitizedPackage]:
        return [p for p in self.packages if p.is_outdated]

    def __str__(self) -> str:
        lines = [f"[{self.project_name}] ({self.project_type})"]
        for pkg in self.packages:
            lines.append(f"  {pkg}")
        return "\n".join(lines)


def sanitize_package(pkg: PackageStatus) -> SanitizedPackage:
    """Sanitize a single PackageStatus, cleaning version strings."""
    clean_current = _clean(pkg.current_version)
    clean_latest = _clean(pkg.latest_version)
    return SanitizedPackage(
        name=pkg.name,
        current_version=clean_current,
        latest_version=clean_latest,
        is_outdated=pkg.is_outdated,
        original_current=pkg.current_version,
        original_latest=pkg.latest_version,
    )


def sanitize_result(result: CheckResult) -> SanitizedResult:
    """Return a SanitizedResult built from a CheckResult."""
    return SanitizedResult(
        project_name=result.project_name,
        project_type=result.project_type,
        packages=[sanitize_package(p) for p in result.packages],
    )
