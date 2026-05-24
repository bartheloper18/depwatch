"""suppressor.py – temporarily suppress alerts for specific packages.

A suppressed package is ignored by the notifier/alert pipeline until
its suppression window expires or it is explicitly lifted.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import CheckResult

DEFAULT_SUPPRESSION_PATH = ".depwatch_suppressions.json"


@dataclass
class Suppression:
    package: str
    project: str
    expires_at: Optional[datetime]  # None means indefinite
    reason: str = ""

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Return True if this suppression is still in effect."""
        if self.expires_at is None:
            return True
        _now = now or datetime.now(timezone.utc)
        return _now < self.expires_at

    def __str__(self) -> str:
        exp = self.expires_at.isoformat() if self.expires_at else "indefinite"
        return f"{self.project}/{self.package} suppressed until {exp}"


def _to_dict(s: Suppression) -> dict:
    return {
        "package": s.package,
        "project": s.project,
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        "reason": s.reason,
    }


def _from_dict(d: dict) -> Suppression:
    exp_raw = d.get("expires_at")
    expires_at = datetime.fromisoformat(exp_raw) if exp_raw else None
    return Suppression(
        package=d["package"],
        project=d["project"],
        expires_at=expires_at,
        reason=d.get("reason", ""),
    )


def load_suppressions(path: str | Path) -> List[Suppression]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return [_from_dict(e) for e in data]
    except (json.JSONDecodeError, KeyError):
        return []


def save_suppressions(suppressions: List[Suppression], path: str | Path) -> None:
    Path(path).write_text(json.dumps([_to_dict(s) for s in suppressions], indent=2))


def add_suppression(
    suppressions: List[Suppression],
    package: str,
    project: str,
    expires_at: Optional[datetime] = None,
    reason: str = "",
) -> List[Suppression]:
    """Add or replace a suppression entry for (project, package)."""
    updated = [s for s in suppressions if not (s.package == package and s.project == project)]
    updated.append(Suppression(package=package, project=project, expires_at=expires_at, reason=reason))
    return updated


def remove_suppression(suppressions: List[Suppression], package: str, project: str) -> List[Suppression]:
    return [s for s in suppressions if not (s.package == package and s.project == project)]


def is_suppressed(
    suppressions: List[Suppression],
    package: str,
    project: str,
    now: Optional[datetime] = None,
) -> bool:
    for s in suppressions:
        if s.package == package and s.project == project:
            return s.is_active(now)
    return False


def filter_suppressed(result: CheckResult, suppressions: List[Suppression], now: Optional[datetime] = None) -> CheckResult:
    """Return a new CheckResult with suppressed packages removed from the outdated list."""
    from depwatch.checker import PackageStatus

    filtered = [
        pkg for pkg in result.packages
        if not (pkg.outdated and is_suppressed(suppressions, pkg.name, result.project, now))
    ]
    return CheckResult(project=result.project, project_type=result.project_type, packages=filtered)
