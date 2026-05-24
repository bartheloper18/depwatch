"""depwatch.digester — Produce a concise digest (summary snapshot) of multiple
CheckResult objects, suitable for periodic email or log output."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from depwatch.checker import CheckResult


@dataclass
class DigestEntry:
    project: str
    project_type: str
    total_packages: int
    outdated_count: int
    checked_at: str

    def __str__(self) -> str:
        status = "up-to-date" if self.outdated_count == 0 else f"{self.outdated_count} outdated"
        return f"[{self.project}] ({self.project_type}) {status} / {self.total_packages} total"


@dataclass
class Digest:
    generated_at: str
    entries: List[DigestEntry] = field(default_factory=list)

    @property
    def total_outdated(self) -> int:
        return sum(e.outdated_count for e in self.entries)

    @property
    def has_issues(self) -> bool:
        return self.total_outdated > 0

    def __str__(self) -> str:
        lines = [f"Digest generated at {self.generated_at}"]
        for entry in self.entries:
            lines.append(f"  {entry}")
        lines.append(f"Total outdated: {self.total_outdated}")
        return "\n".join(lines)


def _result_to_entry(result: CheckResult) -> DigestEntry:
    outdated = [p for p in result.packages if p.is_outdated]
    return DigestEntry(
        project=result.project,
        project_type=result.project_type,
        total_packages=len(result.packages),
        outdated_count=len(outdated),
        checked_at=result.checked_at,
    )


def build_digest(results: List[CheckResult]) -> Digest:
    """Build a Digest from a list of CheckResult objects."""
    now = datetime.now(timezone.utc).isoformat()
    entries = [_result_to_entry(r) for r in results]
    return Digest(generated_at=now, entries=entries)


def format_digest(digest: Digest, fmt: str = "text") -> str:
    """Render a Digest as text or markdown."""
    if fmt == "markdown":
        lines = [f"## Depwatch Digest\n_Generated: {digest.generated_at}_\n"]
        lines.append("| Project | Type | Outdated | Total |")
        lines.append("|---------|------|----------|-------|")
        for e in digest.entries:
            lines.append(f"| {e.project} | {e.project_type} | {e.outdated_count} | {e.total_packages} |")
        lines.append(f"\n**Total outdated packages: {digest.total_outdated}**")
        return "\n".join(lines)
    return str(digest)
