from helpers.melbourne_public_api_client import fetch_locations
from io import StringIO
import pandas as pd
from datetime import datetime

class LocationService:
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
        df_locations["LATEST_SENSING_DATETIME"] = datetime(1999, 12, 31)

        return df_locations