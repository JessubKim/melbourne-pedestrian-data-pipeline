import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import API_URL

logger = logging.getLogger(__name__)


def fetch_records(url: str | None = None) -> dict:
    """Fetch pedestrian count records from the OpenDataSoft API."""
    target = url or API_URL
    request = Request(target, headers={"Accept": "application/json"})

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.error("HTTP %s from %s", exc.code, target)
        raise
    except URLError as exc:
        logger.error("Request failed for %s: %s", target, exc.reason)
        raise
