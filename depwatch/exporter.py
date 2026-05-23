"""Export check results to various file formats (JSON, CSV)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import List

from depwatch.checker import CheckResult, PackageStatus


def _status_rows(results: List[CheckResult]) -> List[dict]:
    """Flatten results into a list of row dicts suitable for CSV/JSON export."""
    rows: List[dict] = []
    for result in results:
        for pkg in result.packages:
            rows.append(
                {
                    "project": result.project_name,
                    "project_type": result.project_type,
                    "package": pkg.name,
                    "current_version": pkg.current_version,
                    "latest_version": pkg.latest_version,
                    "outdated": pkg.is_outdated,
                }
            )
    return rows


def export_json(results: List[CheckResult], path: Path) -> None:
    """Write results to *path* as a JSON array."""
    rows = _status_rows(results)
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def export_csv(results: List[CheckResult], path: Path) -> None:
    """Write results to *path* as a CSV file with a header row."""
    rows = _status_rows(results)
    fieldnames = ["project", "project_type", "package", "current_version", "latest_version", "outdated"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def export_results(results: List[CheckResult], path: Path, fmt: str = "json") -> None:
    """Dispatch to the appropriate exporter based on *fmt* ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        export_json(results, path)
    elif fmt == "csv":
        export_csv(results, path)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
