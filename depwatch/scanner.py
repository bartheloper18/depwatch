"""Scanner module for detecting project type and discovering dependency files."""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ProjectType(Enum):
    PYTHON = "python"
    NODE = "node"
    UNKNOWN = "unknown"


@dataclass
class ProjectScan:
    path: str
    project_type: ProjectType
    dependency_files: List[str] = field(default_factory=list)

    def is_supported(self) -> bool:
        return self.project_type != ProjectType.UNKNOWN


PYTHON_DEP_FILES = ["requirements.txt", "Pipfile", "pyproject.toml", "setup.cfg"]
NODE_DEP_FILES = ["package.json"]

DEP_FILES_BY_TYPE = {
    ProjectType.PYTHON: PYTHON_DEP_FILES,
    ProjectType.NODE: NODE_DEP_FILES,
}


def _find_files(directory: str, filenames: List[str]) -> List[str]:
    """Return absolute paths for any matching filenames found in directory."""
    found = []
    for name in filenames:
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate):
            found.append(candidate)
    return found


def detect_project_type(directory: str) -> ProjectType:
    """Detect the project type based on files present in the directory."""
    if _find_files(directory, NODE_DEP_FILES):
        return ProjectType.NODE
    if _find_files(directory, PYTHON_DEP_FILES):
        return ProjectType.PYTHON
    return ProjectType.UNKNOWN


def scan_project(directory: str, project_type: Optional[str] = None) -> ProjectScan:
    """Scan a project directory and return a ProjectScan result.

    Args:
        directory: Path to the project root.
        project_type: Optional override ('python' or 'node'). Auto-detected if None.

    Returns:
        A ProjectScan instance describing what was found.
    """
    directory = os.path.abspath(directory)

    if project_type:
        try:
            ptype = ProjectType(project_type.lower())
        except ValueError:
            ptype = ProjectType.UNKNOWN
    else:
        ptype = detect_project_type(directory)

    dep_files = _find_files(directory, DEP_FILES_BY_TYPE.get(ptype, []))

    return ProjectScan(path=directory, project_type=ptype, dependency_files=dep_files)
