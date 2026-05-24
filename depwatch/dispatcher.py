"""dispatcher.py – routes CheckResult objects to one or more registered handlers.

A handler is any callable that accepts a CheckResult.  Handlers can be
registered globally or per-project-name.  When dispatch() is called the
result is forwarded to every matching global handler and every handler
registered for that project.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List

from depwatch.checker import CheckResult

Handler = Callable[[CheckResult], None]


class Dispatcher:
    """Routes CheckResult objects to registered handlers."""

    def __init__(self) -> None:
        self._global: List[Handler] = []
        self._project: Dict[str, List[Handler]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, handler: Handler, project: str | None = None) -> None:
        """Register *handler*.

        If *project* is None the handler receives every dispatched result.
        Otherwise it only receives results whose project_name matches.
        """
        if project is None:
            self._global.append(handler)
        else:
            self._project[project].append(handler)

    def unregister(self, handler: Handler, project: str | None = None) -> bool:
        """Remove a previously registered handler.  Returns True if found."""
        target: List[Handler] = self._global if project is None else self._project.get(project, [])
        if handler in target:
            target.remove(handler)
            return True
        return False

    def handler_count(self, project: str | None = None) -> int:
        """Return the number of handlers registered for *project* (or global)."""
        if project is None:
            return len(self._global)
        return len(self._project.get(project, []))

    # ------------------------------------------------------------------
    # Dispatching
    # ------------------------------------------------------------------

    def dispatch(self, result: CheckResult) -> int:
        """Forward *result* to all matching handlers.

        Returns the total number of handler invocations.
        """
        invoked = 0
        for handler in list(self._global):
            handler(result)
            invoked += 1
        for handler in list(self._project.get(result.project_name, [])):
            handler(result)
            invoked += 1
        return invoked

    def clear(self, project: str | None = None) -> None:
        """Remove all handlers, optionally scoped to *project*."""
        if project is None:
            self._global.clear()
            self._project.clear()
        else:
            self._project.pop(project, None)
