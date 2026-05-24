"""Tests for depwatch.dispatcher."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.dispatcher import Dispatcher
from depwatch.scanner import ProjectType


def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest)


def _make_result(project: str = "myapp", outdated: bool = False) -> CheckResult:
    pkg = _ps("requests", "2.28.0", "2.31.0" if outdated else "2.28.0")
    return CheckResult(project_name=project, project_type=ProjectType.PYTHON, packages=[pkg])


# ---------------------------------------------------------------------------
# Registration helpers
# ---------------------------------------------------------------------------

def test_register_global_increments_count():
    d = Dispatcher()
    d.register(lambda r: None)
    assert d.handler_count() == 1


def test_register_project_scoped():
    d = Dispatcher()
    d.register(lambda r: None, project="alpha")
    assert d.handler_count(project="alpha") == 1
    assert d.handler_count() == 0  # global unchanged


def test_unregister_returns_true_when_found():
    d = Dispatcher()
    h = lambda r: None
    d.register(h)
    assert d.unregister(h) is True
    assert d.handler_count() == 0


def test_unregister_returns_false_when_missing():
    d = Dispatcher()
    assert d.unregister(lambda r: None) is False


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def test_dispatch_calls_global_handler():
    d = Dispatcher()
    received = []
    d.register(received.append)
    result = _make_result()
    count = d.dispatch(result)
    assert count == 1
    assert received == [result]


def test_dispatch_calls_matching_project_handler():
    d = Dispatcher()
    received = []
    d.register(received.append, project="myapp")
    result = _make_result(project="myapp")
    d.dispatch(result)
    assert len(received) == 1


def test_dispatch_skips_non_matching_project_handler():
    d = Dispatcher()
    received = []
    d.register(received.append, project="other")
    d.dispatch(_make_result(project="myapp"))
    assert received == []


def test_dispatch_calls_both_global_and_project_handlers():
    d = Dispatcher()
    log: list = []
    d.register(lambda r: log.append("global"))
    d.register(lambda r: log.append("project"), project="myapp")
    d.dispatch(_make_result(project="myapp"))
    assert sorted(log) == ["global", "project"]


def test_dispatch_returns_invocation_count():
    d = Dispatcher()
    d.register(lambda r: None)
    d.register(lambda r: None)
    d.register(lambda r: None, project="myapp")
    assert d.dispatch(_make_result(project="myapp")) == 3


def test_dispatch_no_handlers_returns_zero():
    d = Dispatcher()
    assert d.dispatch(_make_result()) == 0


# ---------------------------------------------------------------------------
# Clear
# ---------------------------------------------------------------------------

def test_clear_all_removes_everything():
    d = Dispatcher()
    d.register(lambda r: None)
    d.register(lambda r: None, project="alpha")
    d.clear()
    assert d.handler_count() == 0
    assert d.handler_count(project="alpha") == 0


def test_clear_project_only_leaves_global():
    d = Dispatcher()
    d.register(lambda r: None)
    d.register(lambda r: None, project="alpha")
    d.clear(project="alpha")
    assert d.handler_count() == 1
    assert d.handler_count(project="alpha") == 0
