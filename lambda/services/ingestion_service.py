import pandas as pd
import logging
from factories.snowflake_connection_factory import SnowflakeConnectionFactory
from repositories.snowflake_repository import SnowflakeRepository
from services.api_service import ApiService
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_DATETIME_PER_LOCATION_SQL = """
    SELECT 
        sl.LOCATION_ID,
        MAX(SENSING_DATETIME) AS LATEST_SENSING_DATETIME
    FROM 
        PEDESTRIAN_ANALYTICS.MART.SENSOR_LOCATIONS sl
    LEFT JOIN
        PEDESTRIAN_ANALYTICS.RAW.LOCATION_DIRECTION_COUNTS ldc ON sl.LOCATION_ID = ldc.LOCATION_ID
    GROUP BY sl.LOCATION_ID
"""

class IngestionService:
    def __init__(self, connection_factory):
        self.conn = connection_factory.get_snowflake_connection()
        self.api_service = ApiService()
        self.snowflake_repository = SnowflakeRepository(self.conn)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def process(self):
        self.__process_location_metadata()

        df_counts_for_all_locations = self.snowflake_repository.select(MAX_DATETIME_PER_LOCATION_SQL)

        df_max_sensing_datetimes = self.api_service.get_max_sensing_datetime_per_location()

        for index, df_latest_location_count in df_counts_for_all_locations.iterrows():
            location_id = df_latest_location_count["LOCATION_ID"]
            df_max_sensing_datetime = df_max_sensing_datetimes[
                df_max_sensing_datetimes['LOCATION_ID'] == location_id]

            max_sensing_datetime_from_api = df_max_sensing_datetime["MAX(SENSING_DATETIME)"].max()
            max_sensing_datetime_from_snowflake = df_latest_location_count["LATEST_SENSING_DATETIME"]
            if pd.isna(max_sensing_datetime_from_snowflake):
                max_sensing_datetime_from_snowflake = pd.Timestamp('2000-01-01')

            self.__proces_counts_for_location(location_id, max_sensing_datetime_from_snowflake, max_sensing_datetime_from_api)

    def __process_location_metadata(self):
        df_all_locations = self.api_service.get_all_locations()
        df_all_locations.columns = df_all_locations.columns.str.upper()
        df_all_locations = df_all_locations.drop(columns=['LOCATION'])

        self.snowflake_repository.truncate('PEDESTRIAN_ANALYTICS.RAW.SENSOR_LOCATIONS')

        self.snowflake_repository.insert('PEDESTRIAN_ANALYTICS.RAW.SENSOR_LOCATIONS', df_all_locations)
        self.snowflake_repository.execute_procedure('PEDESTRIAN_ANALYTICS.MART.MERGE_SENSOR_LOCATIONS_FROM_RAW')

    def __proces_counts_for_location(self, location_id, max_sensing_datetime_from_snowflake, max_sensing_datetime_from_api):

        sensing_datetime_gt = max_sensing_datetime_from_snowflake
        df_newer_counts_for_current_location = self.api_service.get_new_counts_for_location(location_id, sensing_datetime_gt)

        if not isinstance(df_newer_counts_for_current_location, pd.DataFrame) or df_newer_counts_for_current_location.empty:
            return

        max_sensing_datetime_from_api_batch = pd.to_datetime(
            df_newer_counts_for_current_location["SENSING_DATETIME"].max()
        )

        while max_sensing_datetime_from_api_batch < max_sensing_datetime_from_api:

            df_newer_counts_for_current_location = df_newer_counts_for_current_location.drop(columns=['SENSING_DATE', 'SENSING_TIME'],
                                                                       errors='ignore')

            self.snowflake_repository.insert('LOCATION_DIRECTION_COUNTS', df_newer_counts_for_current_location)

            df_newer_counts_for_current_location = self.api_service.get_new_counts_for_location(location_id, max_sensing_datetime_from_api_batch)
            if not isinstance(df_newer_counts_for_current_location, pd.DataFrame) or df_newer_counts_for_current_location.empty:
                break

            max_sensing_datetime_from_api_batch = pd.to_datetime(
                df_newer_counts_for_current_location["SENSING_DATETIME"].max()
            )