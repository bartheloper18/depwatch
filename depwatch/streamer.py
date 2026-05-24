"""streamer.py – streams live check results to a file or stdout as newline-delimited JSON."""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Iterable, Optional

from depwatch.checker import CheckResult


@dataclass
class StreamEntry:
    project: str
    timestamp: str
    total: int
    outdated: int
    packages: list[dict]

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "timestamp": self.timestamp,
            "total": self.total,
            "outdated": self.outdated,
            "packages": self.packages,
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict())


def _result_to_entry(result: CheckResult) -> StreamEntry:
    packages = [
        {
            "name": ps.name,
            "current": ps.current_version,
            "latest": ps.latest_version,
            "outdated": ps.is_outdated,
        }
        for ps in result.packages
    ]
    outdated_count = sum(1 for ps in result.packages if ps.is_outdated)
    return StreamEntry(
        project=result.project,
        timestamp=datetime.now(timezone.utc).isoformat(),
        total=len(result.packages),
        outdated=outdated_count,
        packages=packages,
    )


def stream_results(
    results: Iterable[CheckResult],
    dest: Optional[Path] = None,
    *,
    append: bool = False,
) -> list[StreamEntry]:
    """Write each result as a newline-delimited JSON line.

    If *dest* is None the output goes to stdout.
    Returns the list of StreamEntry objects written.
    """
    entries: list[StreamEntry] = []
    mode = "a" if append else "w"

    def _write(fp: IO[str]) -> None:
        for result in results:
            entry = _result_to_entry(result)
            fp.write(str(entry) + "\n")
            entries.append(entry)

    if dest is None:
        _write(sys.stdout)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open(mode, encoding="utf-8") as fh:
            _write(fh)

    return entries


def read_stream(path: Path) -> list[StreamEntry]:
    """Read newline-delimited JSON entries previously written by stream_results."""
    if not path.exists():
        return []
    entries: list[StreamEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        entries.append(
            StreamEntry(
                project=data.get("project", ""),
                timestamp=data.get("timestamp", ""),
                total=data.get("total", 0),
                outdated=data.get("outdated", 0),
                packages=data.get("packages", []),
            )
        )
    return entries
