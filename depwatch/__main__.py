"""Entry point for the depwatch daemon.

Run with: python -m depwatch [options]
"""

import argparse
import logging
import sys
import time

from depwatch.checker import check_python, check_node
from depwatch.config import load_config, DepwatchConfig
from depwatch.notifier import send_notification
from depwatch.report import format_report
from depwatch.scheduler import Scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("depwatch")


def run_checks(config: DepwatchConfig) -> None:
    """Run all configured dependency checks and dispatch notifications/reports."""
    results = []

    for project in config.projects:
        path = project.get("path", ".")
        kind = project.get("type", "python")
        name = project.get("name", path)

        logger.info("Checking %s project '%s' at %s", kind, name, path)

        try:
            if kind == "python":
                result = check_python(path, project_name=name)
            elif kind == "node":
                result = check_node(path, project_name=name)
            else:
                logger.warning("Unknown project type '%s' for '%s', skipping.", kind, name)
                continue
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to check project '%s': %s", name, exc)
            continue

        results.append(result)

        report_output = format_report(result, fmt=config.report_format)
        print(report_output)

    if results and config.notify:
        try:
            send_notification(results, config.notifier)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Notification failed: %s", exc)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="depwatch",
        description="Monitor Python and Node project dependencies for outdated or vulnerable packages.",
    )
    parser.add_argument(
        "--config",
        default="depwatch.yml",
        metavar="FILE",
        help="Path to the configuration file (default: depwatch.yml).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run checks once and exit instead of running as a daemon.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default=None,
        help="Override the report output format.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    return parser


def main() -> int:
    """Main entry point for depwatch."""
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.debug("Loading config from '%s'", args.config)
    config = load_config(args.config)

    if args.format:
        config.report_format = args.format

    if args.once:
        logger.info("Running one-shot dependency check.")
        run_checks(config)
        return 0

    # Daemon mode: schedule recurring checks
    interval = config.interval_seconds
    logger.info("Starting depwatch daemon (interval: %ds). Press Ctrl+C to stop.", interval)

    scheduler = Scheduler(interval_seconds=interval, task=lambda: run_checks(config))
    scheduler.start()

    try:
        while scheduler.is_running():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Interrupted — stopping depwatch.")
        scheduler.stop()

    return 0


if __name__ == "__main__":
    sys.exit(main())
