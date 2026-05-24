"""Integration tests for Dispatcher used alongside checker/notifier patterns."""
from __future__ import annotations

from depwatch.checker import CheckResult, PackageStatus
from depwatch.dispatcher import Dispatcher
from depwatch.scanner import ProjectType


def _ps(name: str, current: str, latest: str) -> PackageStatus:
    return PackageStatus(name=name, current_version=current, latest_version=latest)


def _result(project: str, *pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project_name=project, project_type=ProjectType.PYTHON, packages=list(pkgs))


def test_multiple_projects_routed_independently():
    d = Dispatcher()
    alpha_log: list[str] = []
    beta_log: list[str] = []

    d.register(lambda r: alpha_log.append(r.project_name), project="alpha")
    d.register(lambda r: beta_log.append(r.project_name), project="beta")

    d.dispatch(_result("alpha", _ps("flask", "2.0.0", "3.0.0")))
    d.dispatch(_result("beta", _ps("express", "4.17.0", "4.18.0")))
    d.dispatch(_result("gamma", _ps("django", "4.0.0", "4.0.0")))

    assert alpha_log == ["alpha"]
    assert beta_log == ["beta"]


def test_global_handler_sees_all_projects():
    d = Dispatcher()
    seen: list[str] = []
    d.register(lambda r: seen.append(r.project_name))

    for proj in ("alpha", "beta", "gamma"):
        d.dispatch(_result(proj, _ps("lib", "1.0.0", "1.0.0")))

    assert seen == ["alpha", "beta", "gamma"]


def test_handler_can_filter_outdated_only():
    d = Dispatcher()
    outdated_projects: list[str] = []

    def only_outdated(r: CheckResult) -> None:
        if r.has_outdated:
            outdated_projects.append(r.project_name)

    d.register(only_outdated)

    d.dispatch(_result("ok", _ps("lib", "1.0.0", "1.0.0")))
    d.dispatch(_result("stale", _ps("lib", "1.0.0", "2.0.0")))

    assert outdated_projects == ["stale"]


def test_unregister_mid_run_stops_future_calls():
    d = Dispatcher()
    log: list[str] = []
    h = lambda r: log.append(r.project_name)
    d.register(h)

    d.dispatch(_result("first", _ps("x", "1.0", "1.0")))
    d.unregister(h)
    d.dispatch(_result("second", _ps("x", "1.0", "1.0")))

    assert log == ["first"]
