"""normalizer.py – Normalise raw package version strings into comparable forms."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class NormalizedPackage:
    name: str
    current: str
    latest: str
    is_outdated: bool
    current_parts: List[int]
    latest_parts: List[int]

    def __str__(self) -> str:
        status = "outdated" if self.is_outdated else "current"
        return f"{self.name} {self.current} -> {self.latest} [{status}]"


@dataclass
class NormalizedResult:
    project: str
    packages: List[NormalizedPackage]

    def outdated(self) -> List[NormalizedPackage]:
        return [p for p in self.packages if p.is_outdated]

    def __str__(self) -> str:
        lines = [f"NormalizedResult({self.project})"]
        for p in self.packages:
            lines.append(f"  {p}")
        return "\n".join(lines)


_VERSION_RE = re.compile(r"[^\d]*([\d]+(?:\.[\d]+)*)")


def _parse_version(version: str) -> List[int]:
    """Return a list of integer parts from a version string, e.g. '1.2.3' -> [1, 2, 3]."""
    m = _VERSION_RE.match(version.strip())
    if not m:
        return [0]
    return [int(x) for x in m.group(1).split(".")]


def normalize_package(pkg: PackageStatus) -> NormalizedPackage:
    """Convert a PackageStatus into a NormalizedPackage with parsed version parts."""
    current_parts = _parse_version(pkg.current_version)
    latest_parts = _parse_version(pkg.latest_version)
    return NormalizedPackage(
        name=pkg.name,
        current=pkg.current_version,
        latest=pkg.latest_version,
        is_outdated=pkg.is_outdated,
        current_parts=current_parts,
        latest_parts=latest_parts,
    )


def normalize_result(result: CheckResult) -> NormalizedResult:
    """Normalize all packages in a CheckResult."""
    packages = [normalize_package(p) for p in result.packages]
    return NormalizedResult(project=result.project, packages=packages)
