import os

DEFAULT_API_URL = (
    "https://melbournetestbed.opendatasoft.com/api/explore/v2.1/catalog/"
    "datasets/pedestrian-counting-system-past-hour-counts-per-minute/records"
    "?order_by=sensing_date%20DESC%2C%20sensing_time%20DESC&limit=1"
)

API_URL = os.environ.get("PEDESTRIAN_API_URL", DEFAULT_API_URL)
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
