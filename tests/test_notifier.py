"""Tests for depwatch.notifier."""

from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import CheckResult, PackageStatus
from depwatch.notifier import NotifierConfig, build_email_body, send_notification


def _make_result(has_outdated: bool) -> CheckResult:
    packages = [
        PackageStatus(name="requests", current_version="2.28.0", latest_version="2.31.0"),
    ]
    if not has_outdated:
        packages = [
            PackageStatus(name="requests", current_version="2.31.0", latest_version="2.31.0"),
        ]
    return CheckResult(project_name="myapp", ecosystem="python", packages=packages)


def test_build_email_body_outdated():
    result = _make_result(has_outdated=True)
    body = build_email_body(result)
    assert "myapp" in body
    assert "requests" in body
    assert "outdated" in body.lower()


def test_build_email_body_up_to_date():
    result = _make_result(has_outdated=False)
    body = build_email_body(result)
    assert "up to date" in body.lower()


def test_send_notification_no_recipients():
    config = NotifierConfig(to_addresses=[])
    result = _make_result(has_outdated=True)
    assert send_notification(result, config) is False


def test_send_notification_no_outdated():
    config = NotifierConfig(to_addresses=["dev@example.com"])
    result = _make_result(has_outdated=False)
    assert send_notification(result, config) is False


def test_send_notification_success():
    config = NotifierConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        to_addresses=["dev@example.com"],
        use_tls=False,
    )
    result = _make_result(has_outdated=True)

    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("depwatch.notifier.smtplib.SMTP", return_value=mock_server):
        success = send_notification(result, config)

    assert success is True
    mock_server.sendmail.assert_called_once()


def test_send_notification_smtp_error():
    import smtplib

    config = NotifierConfig(to_addresses=["dev@example.com"])
    result = _make_result(has_outdated=True)

    with patch(
        "depwatch.notifier.smtplib.SMTP", side_effect=smtplib.SMTPException("connection refused")
    ):
        success = send_notification(result, config)

    assert success is False
