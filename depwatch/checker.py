"""Dependency checker module for Python and Node projects."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class PackageStatus:
    name: str
    current_version: str
    latest_version: Optional[str] = None
    outdated: bool = False
    ecosystem: str = "python"  # "python" or "node"

    def __str__(self) -> str:
        status = "outdated" if self.outdated else "up-to-date"
        latest = self.latest_version or "unknown"
        return f"[{self.ecosystem}] {self.name} {self.current_version} -> {latest} ({status})"


@dataclass
class CheckResult:
    project_path: str
    ecosystem: str
    packages: List[PackageStatus] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def outdated_packages(self) -> List[PackageStatus]:
        return [p for p in self.packages if p.outdated]

    @property
    def has_outdated(self) -> bool:
        return len(self.outdated_packages) > 0


def check_python_outdated(project_path: str) -> CheckResult:
    """Run pip list --outdated in the given project directory."""
    result = CheckResult(project_path=project_path, ecosystem="python")
    try:
        proc = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=30,
        )
        if proc.returncode != 0:
            result.error = proc.stderr.strip()
            return result

        packages = json.loads(proc.stdout)
        for pkg in packages:
            result.packages.append(
                PackageStatus(
                    name=pkg["name"],
                    current_version=pkg["version"],
                    latest_version=pkg["latest_version"],
                    outdated=True,
                    ecosystem="python",
                )
            )
    except FileNotFoundError:
        result.error = "pip not found"
    except subprocess.TimeoutExpired:
        result.error = "pip list timed out"
    except json.JSONDecodeError as e:
        result.error = f"Failed to parse pip output: {e}"
    return result


def check_node_outdated(project_path: str) -> CheckResult:
    """Run npm outdated in the given project directory."""
    result = CheckResult(project_path=project_path, ecosystem="node")
    pkg_json = Path(project_path) / "package.json"
    if not pkg_json.exists():
        result.error = "package.json not found"
        return result
    try:
        proc = subprocess.run(
            ["npm", "outdated", "--json"],
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=60,
        )
        # npm outdated exits with 1 when there are outdated packages
        output = proc.stdout.strip()
        if not output:
            return result

        packages = json.loads(output)
        for name, info in packages.items():
            current = info.get("current", "unknown")
            latest = info.get("latest", "unknown")
            result.packages.append(
                PackageStatus(
                    name=name,
                    current_version=current,
                    latest_version=latest,
                    outdated=current != latest,
                    ecosystem="node",
                )
            )
    except FileNotFoundError:
        result.error = "npm not found"
    except subprocess.TimeoutExpired:
        result.error = "npm outdated timed out"
    except json.JSONDecodeError as e:
        result.error = f"Failed to parse npm output: {e}"
    return result
