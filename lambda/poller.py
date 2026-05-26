#!/usr/bin/env python3
"""Poll the pedestrian counting API every minute (local / long-running use)."""

import logging
import signal
import sys
import time

from api_client import fetch_records
from config import POLL_INTERVAL_SECONDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_running = True


def _shutdown(signum, _frame):
    global _running
    logger.info("Shutting down (signal %s)", signum)
    _running = False


def run_once() -> int:
    data = fetch_records()
    results = data.get("results", [])
    logger.info(
        "Polled OK: %s records (dataset total_count=%s)",
        len(results),
        data.get("total_count"),
    )
    return len(results)


def main() -> int:
    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info("Starting poller (interval=%ss)", POLL_INTERVAL_SECONDS)

    while _running:
        try:
            run_once()
        except Exception:
            logger.exception("Poll failed")

        if not _running:
            break

        deadline = time.monotonic() + POLL_INTERVAL_SECONDS
        while _running and time.monotonic() < deadline:
            time.sleep(min(1.0, deadline - time.monotonic()))

    logger.info("Poller stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
