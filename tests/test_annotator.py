"""Tests for depwatch.annotator."""
from __future__ import annotations

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.annotator import (
    Annotation,
    _bump_type,
    annotate_result,
    format_annotations,
)


def _ps(name: str, current: str, latest: str, up_to_date: bool = False) -> PackageStatus:
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        up_to_date=up_to_date,
    )


def _make_result(packages):
    return CheckResult(project="myapp", project_type="python", packages=packages)


# --- _bump_type ---

def test_bump_type_major():
    assert _bump_type("1.0.0", "2.0.0") == "major"


def test_bump_type_minor():
    assert _bump_type("1.2.0", "1.3.0") == "minor"


def test_bump_type_patch():
    assert _bump_type("1.2.3", "1.2.4") == "patch"


def test_bump_type_with_v_prefix():
    assert _bump_type("v1.0.0", "v2.1.0") == "major"


def test_bump_type_unknown_non_numeric():
    assert _bump_type("abc", "def") == "unknown"


def test_bump_type_same_version():
    assert _bump_type("1.2.3", "1.2.3") == "unknown"


# --- annotate_result ---

def test_annotate_result_empty_when_all_up_to_date():
    result = _make_result([_ps("requests", "2.28.0", "2.28.0", up_to_date=True)])
    assert annotate_result(result) == []


def test_annotate_result_major_bump():
    result = _make_result([_ps("django", "3.2.0", "4.0.0")])
    annotations = annotate_result(result)
    assert len(annotations) == 1
    ann = annotations[0]
    assert ann.package == "django"
    assert ann.project == "myapp"
    assert "major" in ann.note
    assert "major" in ann.tags


def test_annotate_result_minor_bump():
    result = _make_result([_ps("flask", "2.1.0", "2.3.0")])
    annotations = annotate_result(result)
    assert annotations[0].tags == ["minor"]


def test_annotate_result_multiple_packages():
    pkgs = [
        _ps("a", "1.0.0", "2.0.0"),
        _ps("b", "0.1.0", "0.1.1"),
        _ps("c", "5.0.0", "5.0.0", up_to_date=True),
    ]
    result = _make_result(pkgs)
    annotations = annotate_result(result)
    assert len(annotations) == 2
    names = {a.package for a in annotations}
    assert names == {"a", "b"}


# --- format_annotations ---

def test_format_annotations_no_annotations():
    assert format_annotations([]) == "No annotations."


def test_format_annotations_contains_package_name():
    ann = Annotation(package="requests", project="myapp", note="outdated (patch bump): 2.0.0 -> 2.0.1", tags=["patch"])
    output = format_annotations([ann])
    assert "requests" in output
    assert "patch" in output


def test_annotation_str_no_tags():
    ann = Annotation(package="pkg", project="proj", note="some note", tags=[])
    s = str(ann)
    assert "proj/pkg" in s
    assert "some note" in s
    assert "[" not in s
