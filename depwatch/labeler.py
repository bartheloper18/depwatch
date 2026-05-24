"""labeler.py — Attach human-readable labels to packages based on their status.

Labels provide a quick categorical description such as 'up-to-date',
'patch-available', 'minor-available', 'major-available', or 'unknown'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import CheckResult, PackageStatus


@dataclass
class LabeledPackage:
    name: str
    current_version: str
    latest_version: str
    label: str

    def __str__(self) -> str:
        return f"{self.name} ({self.current_version} -> {self.latest_version}) [{self.label}]"


def _derive_label(pkg: PackageStatus) -> str:
    """Return a label string for a single PackageStatus."""
    if not pkg.is_outdated:
        return "up-to-date"

    try:
        cur_parts = [int(x) for x in pkg.current_version.lstrip("v").split(".")]
        lat_parts = [int(x) for x in pkg.latest_version.lstrip("v").split(".")]
    except (ValueError, AttributeError):
        return "unknown"

    # Pad to at least 3 parts
    while len(cur_parts) < 3:
        cur_parts.append(0)
    while len(lat_parts) < 3:
        lat_parts.append(0)

    if lat_parts[0] > cur_parts[0]:
        return "major-available"
    if lat_parts[1] > cur_parts[1]:
        return "minor-available"
    if lat_parts[2] > cur_parts[2]:
        return "patch-available"

    return "unknown"


def label_result(result: CheckResult) -> List[LabeledPackage]:
    """Return a LabeledPackage for every package in *result*."""
    labeled: List[LabeledPackage] = []
    for pkg in result.packages:
        labeled.append(
            LabeledPackage(
                name=pkg.name,
                current_version=pkg.current_version,
                latest_version=pkg.latest_version,
                label=_derive_label(pkg),
            )
        )
    return labeled


def format_labels(labeled: List[LabeledPackage]) -> str:
    """Return a plain-text summary of labeled packages."""
    if not labeled:
        return "No packages to label."
    lines = [str(lp) for lp in labeled]
    return "\n".join(lines)
