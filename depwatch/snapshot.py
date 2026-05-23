"""snapshot.py — Capture and compare point-in-time snapshots of dependency states."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class Snapshot:
    """A point-in-time record of package states for one or more projects."""
    timestamp: float
    projects: Dict[str, List[dict]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "projects": self.projects}

    @classmethod
    def from_dict(cls, data: dict) -> "Snapshot":
        return cls(
            timestamp=float(data.get("timestamp", 0.0)),
            projects=data.get("projects", {}),
        )

    def __str__(self) -> str:  # pragma: no cover
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        total = sum(len(pkgs) for pkgs in self.projects.values())
        return f"Snapshot({ts}, {len(self.projects)} project(s), {total} package(s))"


def _result_to_snapshot_entry(result: CheckResult) -> dict:
    """Serialise a CheckResult into the snapshot projects dict."""
    return {
        "project": result.project,
        "packages": [
            {
                "name": ps.name,
                "current": ps.current_version,
                "latest": ps.latest_version,
                "outdated": ps.outdated,
            }
            for ps in result.packages
        ],
    }


def capture_snapshot(results: List[CheckResult]) -> Snapshot:
    """Build a Snapshot from a list of CheckResults."""
    projects: Dict[str, List[dict]] = {}
    for result in results:
        entry = _result_to_snapshot_entry(result)
        projects[result.project] = entry["packages"]
    return Snapshot(timestamp=time.time(), projects=projects)


def save_snapshot(snapshot: Snapshot, path: Path) -> None:
    """Persist a snapshot to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_snapshot(path: Path) -> Optional[Snapshot]:
    """Load a snapshot from a JSON file; returns None if missing or malformed."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return Snapshot.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def diff_snapshots(old: Snapshot, new: Snapshot) -> Dict[str, List[str]]:
    """Return packages that changed outdated status between two snapshots.

    Returns a dict with keys 'became_outdated' and 'became_current'.
    """
    became_outdated: List[str] = []
    became_current: List[str] = []

    all_projects = set(old.projects) | set(new.projects)
    for project in all_projects:
        old_pkgs = {p["name"]: p["outdated"] for p in old.projects.get(project, [])}
        new_pkgs = {p["name"]: p["outdated"] for p in new.projects.get(project, [])}
        for name, outdated in new_pkgs.items():
            prev = old_pkgs.get(name)
            label = f"{project}:{name}"
            if prev is False and outdated is True:
                became_outdated.append(label)
            elif prev is True and outdated is False:
                became_current.append(label)

    return {"became_outdated": became_outdated, "became_current": became_current}
