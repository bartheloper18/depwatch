"""CLI entry-point for depwatch."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import List

from depwatch.checker import check_python, check_node
from depwatch.config import load_config
from depwatch.notifier import send_notification
from depwatch.report import format_report
from depwatch.scheduler import Scheduler
from depwatch.watcher import FileWatcher, collect_watched_files

logger = logging.getLogger("depwatch")


def run_checks(config_path: str) -> None:
    """Load config, run all checks, report and optionally notify."""
    cfg = load_config(config_path)
    results = []
    for project in cfg.projects:
        p = Path(project["path"])
        kind = project.get("type", "python")
        if kind == "python":
            results.append(check_python(p, project.get("name", p.name)))
        elif kind == "node":
            results.append(check_node(p, project.get("name", p.name)))
        else:
            logger.warning("Unknown project type '%s' — skipping.", kind)

    for result in results:
        print(format_report(result, fmt=cfg.report_format))

    if cfg.notify and any(r.has_outdated for r in results):
        send_notification(cfg.notifier, results)


def _on_dep_file_changed(path: Path, config_path: str) -> None:
    logger.info("Dependency file changed: %s — re-running checks.", path)
    try:
        run_checks(config_path)
    except Exception as exc:  # pragma: no cover
        logger.error("Check failed after file change: %s", exc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depwatch",
        description="Monitor Python and Node dependencies for outdated or vulnerable packages.",
    )
    parser.add_argument("--config", default="depwatch.yaml", help="Path to config file.")
    parser.add_argument("--once", action="store_true", help="Run checks once and exit.")
    parser.add_argument("--watch", action="store_true", help="Re-check when dependency files change.")
    parser.add_argument("--interval", type=int, default=3600, help="Scheduler interval in seconds.")
    parser.add_argument("--log-level", default="INFO", help="Logging level.", dest="log_level")
    return parser


def main(argv: List[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.once:
        run_checks(args.config)
        return

    scheduler = Scheduler(interval=args.interval, task=lambda: run_checks(args.config))

    watcher: FileWatcher | None = None
    if args.watch:
        try:
            cfg = load_config(args.config)
            roots = [Path(p["path"]) for p in cfg.projects]
            watched = collect_watched_files(roots)
            if watched:
                watcher = FileWatcher(
                    paths=watched,
                    callback=lambda p: _on_dep_file_changed(p, args.config),
                    poll_interval=5.0,
                )
                watcher.start()
                logger.info("Watching %d dependency file(s) for changes.", len(watched))
            else:
                logger.warning("--watch enabled but no recognised dependency files found.")
        except Exception as exc:  # pragma: no cover
            logger.error("Could not start file watcher: %s", exc)

    def _shutdown(sig, frame):  # pragma: no cover
        logger.info("Shutting down (signal %d)…", sig)
        scheduler.stop()
        if watcher:
            watcher.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    scheduler.start()


if __name__ == "__main__":  # pragma: no cover
    main()
