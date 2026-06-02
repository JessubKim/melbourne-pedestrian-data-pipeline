import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from urllib.parse import quote
from helpers.config import ROOT_API_URL
from urllib.parse import urlencode

from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

RESOURCE_RELATIVE_URL = "api/explore/v2.1/catalog/datasets/pedestrian-counting-system-past-hour-counts-per-minute/records"

def fetch_locations():
    url = "https://melbournetestbed.opendatasoft.com/api/explore/v2.1/catalog/datasets/pedestrian-counting-system-sensor-locations/exports/csv?lang=en&timezone=Australia%2FSydney&use_labels=true&delimiter=%2C"

    request = Request(url, headers={"Accept": "text/csv"})
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except HTTPError as exc:
        logger.error("HTTP %s from %s", exc.code, url)
        raise
    except URLError as exc:
        logger.error("Request failed for %s: %s", url, exc.reason)
        raise

def fetch_max_sensing_datetime_per_location() -> dict:
    select_filter = "location_id,max(sensing_datetime)"
    url = f"{ROOT_API_URL}/{RESOURCE_RELATIVE_URL}?select={select_filter}&group_by=location_id"

    return __send_request(url, {"Accept": "application/json"})


def fetch_counts_per_min(location_id: int, sensing_datetime_gt: datetime) -> dict:

    where_filter = quote(f"location_id={location_id} AND sensing_datetime > date'{sensing_datetime_gt.isoformat()}'")
    order_filter = quote("sensing_datetime ASC")
    limit = 100 # max limit by API

    url = f"{ROOT_API_URL}/{RESOURCE_RELATIVE_URL}?where={where_filter}&order_by={order_filter}&limit={limit}"

    return __send_request(url, {"Accept": "application/json"})


def __send_request(url, headers):
    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.error("HTTPError %s from %s\nReason: %s", exc.code, url, exc.read().decode())
        raise
    except URLError as exc:
        logger.error("Request failed for %s: %s", url, exc.reason)
        raise
