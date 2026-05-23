"""Report formatting utilities for depwatch."""

import json
from datetime import datetime, timezone
from typing import Dict, Any

from depwatch.checker import CheckResult


def _result_to_dict(result: CheckResult) -> Dict[str, Any]:
    """Serialise a CheckResult to a plain dictionary."""
    return {
        "project_name": result.project_name,
        "ecosystem": result.ecosystem,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "has_outdated": result.has_outdated,
        "packages": [
            {
                "name": pkg.name,
                "current_version": pkg.current_version,
                "latest_version": pkg.latest_version,
                "is_outdated": pkg.is_outdated,
            }
            for pkg in result.packages
        ],
    }


def format_text(result: CheckResult) -> str:
    """Return a human-readable text report."""
    lines = [
        f"Project : {result.project_name}",
        f"Ecosystem: {result.ecosystem}",
        f"Packages : {len(result.packages)} checked",
        "",
    ]
    if not result.has_outdated:
        lines.append("✓ All packages are up to date.")
    else:
        lines.append(f"✗ {len(result.outdated_packages)} outdated package(s):")
        for pkg in result.outdated_packages:
            lines.append(f"  {pkg}")
    return "\n".join(lines)


def format_json(result: CheckResult, indent: int = 2) -> str:
    """Return a JSON-formatted report string."""
    return json.dumps(_result_to_dict(result), indent=indent)


def format_report(result: CheckResult, fmt: str = "text") -> str:
    """Dispatch to the appropriate formatter.

    Args:
        result: The check result to format.
        fmt: One of ``"text"`` or ``"json"``.

    Raises:
        ValueError: If *fmt* is not supported.
    """
    if fmt == "text":
        return format_text(result)
    if fmt == "json":
        return format_json(result)
    raise ValueError(f"Unsupported report format: {fmt!r}. Choose 'text' or 'json'.")
