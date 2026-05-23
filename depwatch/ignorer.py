"""depwatch.ignorer — manage a list of packages to ignore during checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from depwatch.checker import CheckResult, PackageStatus

_DEFAULT_IGNORE_FILE = ".depwatch_ignore.json"


def load_ignore_list(path: str | Path) -> list[str]:
    """Load the list of ignored package names from *path*.

    Returns an empty list if the file does not exist or is malformed.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(item) for item in data]
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_ignore_list(packages: Iterable[str], path: str | Path) -> None:
    """Persist *packages* as the ignore list at *path*."""
    p = Path(path)
    p.write_text(
        json.dumps(sorted(set(packages)), indent=2),
        encoding="utf-8",
    )


def add_to_ignore_list(package: str, path: str | Path) -> list[str]:
    """Add *package* to the ignore list and return the updated list."""
    current = load_ignore_list(path)
    updated = sorted(set(current) | {package})
    save_ignore_list(updated, path)
    return updated


def remove_from_ignore_list(package: str, path: str | Path) -> list[str]:
    """Remove *package* from the ignore list and return the updated list.

    If *package* is not present in the ignore list, the list is returned
    unchanged without raising an error.
    """
    current = load_ignore_list(path)
    updated = sorted(p for p in current if p != package)
    save_ignore_list(updated, path)
    return updated


def is_ignored(package: str, path: str | Path) -> bool:
    """Return ``True`` if *package* is present in the ignore list at *path*.

    This is a convenience wrapper around :func:`load_ignore_list` for
    single-package look-ups without requiring the caller to load and
    inspect the full list manually.
    """
    return package in load_ignore_list(path)


def filter_result(result: CheckResult, ignore_list: list[str]) -> CheckResult:
    """Return a new :class:`CheckResult` with ignored packages removed."""
    if not ignore_list:
        return result
    ignore_set = set(ignore_list)
    filtered: list[PackageStatus] = [
        pkg for pkg in result.packages if pkg.name not in ignore_set
    ]
    return CheckResult(
        project_name=result.project_name,
        project_type=result.project_type,
        packages=filtered,
        checked_at=result.checked_at,
    )
