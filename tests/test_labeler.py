"""Tests for depwatch.labeler."""

from __future__ import annotations

from depwatch.checker import CheckResult, PackageStatus
from depwatch.labeler import LabeledPackage, _derive_label, format_labels, label_result


def _ps(name: str, current: str, latest: str, outdated: bool) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_result(*pkgs: PackageStatus) -> CheckResult:
    return CheckResult(project_name="test-project", project_type="python", packages=list(pkgs))


# ---------------------------------------------------------------------------
# _derive_label
# ---------------------------------------------------------------------------

def test_derive_label_up_to_date():
    pkg = _ps("requests", "2.28.0", "2.28.0", False)
    assert _derive_label(pkg) == "up-to-date"


def test_derive_label_patch():
    pkg = _ps("requests", "2.28.0", "2.28.2", True)
    assert _derive_label(pkg) == "patch-available"


def test_derive_label_minor():
    pkg = _ps("requests", "2.27.0", "2.28.0", True)
    assert _derive_label(pkg) == "minor-available"


def test_derive_label_major():
    pkg = _ps("requests", "1.0.0", "2.0.0", True)
    assert _derive_label(pkg) == "major-available"


def test_derive_label_unknown_version_string():
    pkg = _ps("weird-pkg", "abc", "xyz", True)
    assert _derive_label(pkg) == "unknown"


# ---------------------------------------------------------------------------
# label_result
# ---------------------------------------------------------------------------

def test_label_result_empty():
    result = _make_result()
    labeled = label_result(result)
    assert labeled == []


def test_label_result_mixed():
    result = _make_result(
        _ps("pkgA", "1.0.0", "1.0.0", False),
        _ps("pkgB", "1.0.0", "2.0.0", True),
        _ps("pkgC", "1.2.0", "1.3.0", True),
    )
    labeled = label_result(result)
    assert len(labeled) == 3
    labels = {lp.name: lp.label for lp in labeled}
    assert labels["pkgA"] == "up-to-date"
    assert labels["pkgB"] == "major-available"
    assert labels["pkgC"] == "minor-available"


def test_labeled_package_str():
    lp = LabeledPackage("mylib", "1.0.0", "1.1.0", "minor-available")
    text = str(lp)
    assert "mylib" in text
    assert "minor-available" in text
    assert "1.0.0" in text
    assert "1.1.0" in text


# ---------------------------------------------------------------------------
# format_labels
# ---------------------------------------------------------------------------

def test_format_labels_empty():
    output = format_labels([])
    assert "No packages" in output


def test_format_labels_lists_all():
    result = _make_result(
        _ps("alpha", "0.1.0", "0.1.1", True),
        _ps("beta", "2.0.0", "2.0.0", False),
    )
    labeled = label_result(result)
    output = format_labels(labeled)
    assert "alpha" in output
    assert "beta" in output
    assert "patch-available" in output
    assert "up-to-date" in output
