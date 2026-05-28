#!/usr/bin/env python3
"""Run the Lambda `handler` locally (once or on an interval)."""

import argparse
import logging
import os
from pathlib import Path
import signal
import sys
import time

from index import handler

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


class _LocalLambdaContext:
    function_name = "local_runner"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:local:0:function:local_runner"
    aws_request_id = "local"

def run_once(event: dict) -> object:
    context = _LocalLambdaContext()
    result = handler(event, context)
    logger.info("Handler returned: %s", result)
    return result


def main() -> int:
    from helpers.config import POLL_INTERVAL_SECONDS

    parser = argparse.ArgumentParser(description="Run the Lambda handler locally.")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run the handler once and exit.",
    )
    parser.add_argument(
        "--event-json",
        default=os.environ.get("LAMBDA_EVENT_JSON", "{}"),
        help='Event JSON string to pass to handler (default: "{}"). '
        "Can also be set via LAMBDA_EVENT_JSON.",
    )
    args = parser.parse_args()

    try:
        import json

        event = json.loads(args.event_json) if args.event_json else {}
        if not isinstance(event, dict):
            raise ValueError("event must be a JSON object")
    except Exception as e:
        logger.error("Invalid --event-json / LAMBDA_EVENT_JSON: %s", e)
        return 2

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    if args.once:
        try:
            run_once(event)
        except Exception:
            logger.exception("Handler failed")
            return 1
        return 0

    logger.info("Starting handler loop (interval=%ss)", POLL_INTERVAL_SECONDS)

    while _running:
        try:
            run_once(event)
        except Exception:
            logger.exception("Handler failed")

        if not _running:
            break

        deadline = time.monotonic() + POLL_INTERVAL_SECONDS
        while _running and time.monotonic() < deadline:
            time.sleep(min(1.0, deadline - time.monotonic()))

    logger.info("Handler loop stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
