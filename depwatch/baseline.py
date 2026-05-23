"""Baseline management for depwatch.

A baseline captures the current state of packages for a project so that
future checks can be compared against it to highlight *new* issues only.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class Baseline:
    project: str
    recorded_at: str  # ISO-8601
    packages: Dict[str, str]  # name -> installed version


def _result_to_baseline(result: CheckResult) -> Baseline:
    packages = {ps.name: ps.installed for ps in result.packages}
    return Baseline(
        project=result.project,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        packages=packages,
    )


def save_baseline(result: CheckResult, path: str) -> Baseline:
    """Persist a baseline derived from *result* to *path*."""
    baseline = _result_to_baseline(result)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(baseline), fh, indent=2)
    return baseline


def load_baseline(path: str) -> Optional[Baseline]:
    """Load a baseline from *path*, returning ``None`` if absent or corrupt."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Baseline(
            project=data["project"],
            recorded_at=data["recorded_at"],
            packages=data["packages"],
        )
    except (KeyError, json.JSONDecodeError, OSError):
        return None


def new_since_baseline(result: CheckResult, baseline: Optional[Baseline]) -> List[PackageStatus]:
    """Return packages that are outdated in *result* but were absent from *baseline*.

    If *baseline* is ``None`` every outdated package is considered new.
    """
    if baseline is None:
        return result.outdated_packages()

    new_issues: List[PackageStatus] = []
    for ps in result.outdated_packages():
        baseline_version = baseline.packages.get(ps.name)
        # Package is "new" if it wasn't tracked before, or its installed
        # version has changed since the baseline was recorded.
        if baseline_version is None or baseline_version != ps.installed:
            new_issues.append(ps)
    return new_issues
