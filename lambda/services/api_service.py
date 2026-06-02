from helpers.melbourne_public_api_client import fetch_locations, fetch_max_sensing_datetime_per_location, fetch_counts_per_min
from io import StringIO
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class ApiService:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def get_all_locations(self):
        locations = fetch_locations()
        df_locations = pd.read_csv(StringIO(locations))
        df_locations.columns = df_locations.columns.str.upper()

        return df_locations

    def get_max_sensing_datetime_per_location(self):
        response = fetch_max_sensing_datetime_per_location()
        results = response.get("results",[])
        df_max_sensing_datetimes = pd.DataFrame(results)
        df_max_sensing_datetimes.columns = df_max_sensing_datetimes.columns.str.upper()
        df_max_sensing_datetimes["MAX(SENSING_DATETIME)"] = pd.to_datetime(
            df_max_sensing_datetimes["MAX(SENSING_DATETIME)"], format="ISO8601", utc=True
        )

        return df_max_sensing_datetimes

    def get_new_counts_for_location(self, location_id, latest_sensing_datetime):
        new_location_counts = fetch_counts_per_min(location_id=location_id, sensing_datetime_gt=latest_sensing_datetime)
        results = new_location_counts.get("results", [])

        logger.info(
            "Fetched %s records (total_count=%s)",
            len(results),
            new_location_counts.get("total_count"),
        )

        if not results:
            return []

        df_new_counts_per_minute = pd.DataFrame(results).rename(columns=str.upper)
        df_new_counts_per_minute.columns = df_new_counts_per_minute.columns.str.upper()
        df_new_counts_per_minute["SENSING_DATETIME"] = pd.to_datetime(
            df_new_counts_per_minute["SENSING_DATETIME"]
        )

        return df_new_counts_per_minute
