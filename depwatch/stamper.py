"""stamper.py – attach human-readable timestamps and age metadata to check results."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class StampedPackage:
    name: str
    current_version: str
    latest_version: str
    is_outdated: bool
    stamp: str  # ISO-8601 UTC
    age_seconds: float

    def __str__(self) -> str:
        status = "outdated" if self.is_outdated else "up-to-date"
        return f"{self.name} {self.current_version} [{status}] stamped={self.stamp} age={self.age_seconds:.1f}s"


@dataclass
class StampedResult:
    project: str
    project_type: str
    stamped_at: str  # ISO-8601 UTC
    packages: List[StampedPackage] = field(default_factory=list)

    @property
    def total_outdated(self) -> int:
        return sum(1 for p in self.packages if p.is_outdated)

    def __str__(self) -> str:
        return (
            f"StampedResult(project={self.project!r}, type={self.project_type}, "
            f"stamped_at={self.stamped_at}, outdated={self.total_outdated}/{len(self.packages)})"
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _iso_to_epoch(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp()


def stamp_result(result: CheckResult, reference_time: float | None = None) -> StampedResult:
    """Attach timestamp metadata to every package in *result*."""
    if reference_time is None:
        reference_time = time.time()

    now_iso = _now_iso()
    stamped_packages: List[StampedPackage] = []

    for pkg in result.packages:
        age = reference_time - _iso_to_epoch(now_iso)
        stamped_packages.append(
            StampedPackage(
                name=pkg.name,
                current_version=pkg.current_version,
                latest_version=pkg.latest_version,
                is_outdated=pkg.is_outdated,
                stamp=now_iso,
                age_seconds=abs(age),
            )
        )

    return StampedResult(
        project=result.project,
        project_type=result.project_type,
        stamped_at=now_iso,
        packages=stamped_packages,
    )


def format_stamped(stamped: StampedResult) -> str:
    """Return a plain-text summary of a StampedResult."""
    lines = [str(stamped)]
    for pkg in stamped.packages:
        lines.append(f"  {pkg}")
    if not stamped.packages:
        lines.append("  (no packages)")
    return "\n".join(lines)
