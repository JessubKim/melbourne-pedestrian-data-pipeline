import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import API_URL

logger = logging.getLogger(__name__)


def fetch_records(url: str | None = None, location_id: int | None = None, sensing_datetime_gt: str | None = None) -> dict:
    """Fetch pedestrian count records from the OpenDataSoft API."""
    target = url or API_URL
    filters = []
    if location_id is not None:
        filters.append(f"location_id={location_id}")
    if sensing_datetime_gt is not None:
        filters.append(f"sensing_datetime>'{sensing_datetime_gt}'")
    if filters:
        where_clause = " AND ".join(filters)
        separator = "&" if "?" in target else "?"
        target = f"{target}{separator}where={where_clause}"
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
