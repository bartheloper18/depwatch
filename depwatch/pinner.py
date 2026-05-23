"""depwatch.pinner — generate pinned dependency snapshots.

Produces a mapping of {package: current_version} for all packages
reported in a CheckResult, optionally filtering to only outdated ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List
import json
import pathlib

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class PinnedSnapshot:
    """A pinned set of package versions for a project."""

    project: str
    project_type: str
    pins: Dict[str, str] = field(default_factory=dict)  # name -> current_version

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "project_type": self.project_type,
            "pins": self.pins,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PinnedSnapshot":
        return cls(
            project=data.get("project", ""),
            project_type=data.get("project_type", ""),
            pins=data.get("pins", {}),
        )

    def __str__(self) -> str:
        lines = [f"[{self.project}] ({self.project_type})"]
        for name, version in sorted(self.pins.items()):
            lines.append(f"  {name}=={version}")
        return "\n".join(lines)


def pin_result(result: CheckResult, outdated_only: bool = False) -> PinnedSnapshot:
    """Build a PinnedSnapshot from a CheckResult.

    Args:
        result: The check result to pin.
        outdated_only: When True, only include packages that are outdated.

    Returns:
        A PinnedSnapshot with current versions.
    """
    packages: List[PackageStatus] = (
        result.outdated_packages() if outdated_only else result.packages
    )
    pins = {
        pkg.name: pkg.current_version
        for pkg in packages
        if pkg.current_version
    }
    return PinnedSnapshot(
        project=result.project,
        project_type=result.project_type,
        pins=pins,
    )


def save_pins(snapshot: PinnedSnapshot, path: pathlib.Path) -> None:
    """Persist a PinnedSnapshot to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot.to_dict(), fh, indent=2)


def load_pins(path: pathlib.Path) -> PinnedSnapshot:
    """Load a PinnedSnapshot from a JSON file.

    Returns an empty snapshot when the file is missing or malformed.
    """
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        return PinnedSnapshot.from_dict(data)
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return PinnedSnapshot(project="", project_type="", pins={})
