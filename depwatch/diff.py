"""Compute diffs between consecutive check results for a project."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.checker import PackageStatus
from depwatch.history import load_history


@dataclass
class PackageDiff:
    """Describes a change in a single package's status between two checks."""

    name: str
    previous_version: Optional[str]
    current_version: Optional[str]
    previous_latest: Optional[str]
    current_latest: Optional[str]
    became_outdated: bool   # was up-to-date, now outdated
    became_current: bool    # was outdated, now up-to-date
    is_new: bool            # not present in previous result
    was_removed: bool       # not present in current result

    def __str__(self) -> str:
        if self.is_new:
            return f"[NEW]     {self.name} {self.current_version} (latest {self.current_latest})"
        if self.was_removed:
            return f"[REMOVED] {self.name} {self.previous_version}"
        if self.became_outdated:
            return (
                f"[OUTDATED] {self.name} {self.current_version} "
                f"-> latest {self.current_latest}"
            )
        if self.became_current:
            return f"[FIXED]   {self.name} now at {self.current_version}"
        return f"[UNCHANGED] {self.name} {self.current_version}"


@dataclass
class CheckDiff:
    """Full diff between two consecutive check results for one project."""

    project: str
    changes: List[PackageDiff]

    @property
    def has_changes(self) -> bool:
        return any(
            d.became_outdated or d.became_current or d.is_new or d.was_removed
            for d in self.changes
        )

    def __str__(self) -> str:
        lines = [f"Diff for {self.project}:"]
        notable = [d for d in self.changes if str(d).split()[0] != "[UNCHANGED]"]
        if not notable:
            lines.append("  No changes detected.")
        else:
            lines.extend(f"  {d}" for d in notable)
        return "\n".join(lines)


def diff_results(previous: List[PackageStatus], current: List[PackageStatus]) -> List[PackageDiff]:
    """Return per-package diffs between two lists of PackageStatus."""
    prev_map = {p.name: p for p in previous}
    curr_map = {p.name: p for p in current}
    all_names = set(prev_map) | set(curr_map)

    diffs: List[PackageDiff] = []
    for name in sorted(all_names):
        prev = prev_map.get(name)
        curr = curr_map.get(name)
        diffs.append(
            PackageDiff(
                name=name,
                previous_version=prev.current if prev else None,
                current_version=curr.current if curr else None,
                previous_latest=prev.latest if prev else None,
                current_latest=curr.latest if curr else None,
                became_outdated=bool(prev and curr and not prev.outdated and curr.outdated),
                became_current=bool(prev and curr and prev.outdated and not curr.outdated),
                is_new=prev is None,
                was_removed=curr is None,
            )
        )
    return diffs


def diff_latest(project: str, history_path: str) -> Optional[CheckDiff]:
    """Load the two most recent history entries for *project* and diff them.

    Returns ``None`` if fewer than two entries exist.
    """
    entries = load_history(history_path)
    project_entries = [e for e in entries if e.get("project") == project]
    if len(project_entries) < 2:
        return None

    def _to_statuses(entry: dict) -> List[PackageStatus]:
        return [
            PackageStatus(name=p["name"], current=p["current"], latest=p["latest"])
            for p in entry.get("packages", [])
        ]

    previous = _to_statuses(project_entries[-2])
    current = _to_statuses(project_entries[-1])
    return CheckDiff(project=project, changes=diff_results(previous, current))
