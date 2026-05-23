"""Notification module for depwatch — sends alerts when outdated or vulnerable packages are found."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field
from typing import Optional

from depwatch.checker import CheckResult

logger = logging.getLogger(__name__)


@dataclass
class NotifierConfig:
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    from_address: str = "depwatch@localhost"
    to_addresses: list = field(default_factory=list)


def build_email_body(result: CheckResult) -> str:
    """Build a plain-text email body summarising the check result."""
    lines = [
        f"depwatch report for project: {result.project_name}",
        f"Ecosystem : {result.ecosystem}",
        "",
    ]
    if not result.has_outdated:
        lines.append("All packages are up to date. No action required.")
    else:
        lines.append(f"Found {len(result.outdated_packages)} outdated package(s):\n")
        for pkg in result.outdated_packages:
            lines.append(f"  - {pkg}")
    return "\n".join(lines)


def send_notification(result: CheckResult, config: NotifierConfig) -> bool:
    """Send an email notification for the given CheckResult.

    Returns True on success, False on failure.
    """
    if not config.to_addresses:
        logger.warning("No recipient addresses configured; skipping notification.")
        return False

    if not result.has_outdated:
        logger.info("No outdated packages found; skipping notification.")
        return False

    body = build_email_body(result)
    subject = f"[depwatch] Outdated packages detected in {result.project_name}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.from_address
    msg["To"] = ", ".join(config.to_addresses)
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            if config.use_tls:
                server.starttls()
            if config.smtp_user and config.smtp_password:
                server.login(config.smtp_user, config.smtp_password)
            server.sendmail(config.from_address, config.to_addresses, msg.as_string())
        logger.info("Notification sent to %s", config.to_addresses)
        return True
    except smtplib.SMTPException as exc:
        logger.error("Failed to send notification: %s", exc)
        return False
