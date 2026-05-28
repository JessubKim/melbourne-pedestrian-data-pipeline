import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from urllib.parse import quote
from helpers.config import ROOT_API_URL
from urllib.parse import urlencode

from datetime import datetime

logger = logging.getLogger(__name__)

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

def fetch_counts_per_min(location_id: int, sensing_datetime_gt: datetime) -> dict:
    relative_url = "api/explore/v2.1/catalog/datasets/pedestrian-counting-system-past-hour-counts-per-minute/records"

    where_filter = quote(f"location_id={location_id} AND sensing_datetime > date'{sensing_datetime_gt.isoformat()}'")
    order_filter = quote("sensing_datetime ASC")
    limit = 60*24 # 60 mins x 24 hours = 1440

    url = f"{ROOT_API_URL}/{relative_url}?where={where_filter}&order_by={order_filter}&limit={limit}"

    request = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        logger.error("HTTP %s from %s", exc.code, url)
        raise
    except URLError as exc:
        logger.error("Request failed for %s: %s", url, exc.reason)
        raise
