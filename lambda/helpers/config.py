import os

DEFAULT_API_URL = (
    "https://melbournetestbed.opendatasoft.com"
)

ROOT_API_URL = os.environ.get("PEDESTRIAN_API_URL", DEFAULT_API_URL)
POLL_INTERVAL_SECONDS = int(os.environ.get("POLL_INTERVAL_SECONDS", "60"))
