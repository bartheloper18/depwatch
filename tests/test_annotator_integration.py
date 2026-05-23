"""Integration tests: annotator working end-to-end with real CheckResult data."""
from __future__ import annotations

from depwatch.checker import CheckResult, PackageStatus
from depwatch.annotator import annotate_result, format_annotations


def _ps(name, current, latest, up_to_date=False):
    return PackageStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        up_to_date=up_to_date,
    )


def test_full_pipeline_produces_formatted_output():
    packages = [
        _ps("numpy", "1.21.0", "1.24.0"),
        _ps("scipy", "1.7.0", "1.7.0", up_to_date=True),
        _ps("pandas", "1.3.0", "2.0.0"),
    ]
    result = CheckResult(project="data-science", project_type="python", packages=packages)
    annotations = annotate_result(result)
    assert len(annotations) == 2

    output = format_annotations(annotations)
    assert "numpy" in output
    assert "pandas" in output
    assert "scipy" not in output
    assert "major" in output


def test_all_up_to_date_gives_no_annotations_message():
    packages = [
        _ps("lodash", "4.17.21", "4.17.21", up_to_date=True),
        _ps("express", "4.18.2", "4.18.2", up_to_date=True),
    ]
    result = CheckResult(project="my-node-app", project_type="node", packages=packages)
    annotations = annotate_result(result)
    output = format_annotations(annotations)
    assert output == "No annotations."


def test_mixed_bump_types_all_annotated():
    packages = [
        _ps("a", "1.0.0", "2.0.0"),   # major
        _ps("b", "1.0.0", "1.1.0"),   # minor
        _ps("c", "1.0.0", "1.0.1"),   # patch
    ]
    result = CheckResult(project="proj", project_type="python", packages=packages)
    annotations = annotate_result(result)
    bump_tags = {ann.tags[0] for ann in annotations}
    assert bump_tags == {"major", "minor", "patch"}
