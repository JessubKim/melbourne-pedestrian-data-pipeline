import json
import logging
import os
from io import StringIO

from factories.snowflake_connection_factory import SnowflakeConnectionFactory
from repositories.snowflake_repository import SnowflakeRepository
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from datetime import datetime
from services.location_service import LocationService

from helpers.melbourne_public_api_client import fetch_counts_per_min, fetch_locations

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_DATETIME_BY_LOCATION_SQL = """
    SELECT LOCATION_ID, MAX(SENSING_DATETIME) AS LATEST_SENSING_DATETIME
    FROM PEDESTRIAN_ANALYTICS.RAW.LOCATION_DIRECTION_COUNTS
    GROUP BY LOCATION_ID
"""

def filter_new_records(results_df, latest_df):    
    merged = results_df.merge(latest_df, on="LOCATION_ID", how="left")
    is_new = (
        merged["LATEST_SENSING_DATETIME"].isna()
        | (merged["SENSING_DATETIME"] > merged["LATEST_SENSING_DATETIME"])
    )
    return merged.loc[is_new].drop(columns=["LATEST_SENSING_DATETIME"])


def insert_records(conn, df):
    write_pandas(conn, df, "LOCATION_DIRECTION_COUNTS")


def handler(event, context):
    connection_factory = SnowflakeConnectionFactory('PEDESTRIAN_ANALYTICS', 'RAW')
    with (
        connection_factory.get_snowflake_connection() as conn,
        SnowflakeRepository(conn, 'LOCATION_DIRECTION_COUNTS') as repository,
        LocationService() as location_service,
    ):
        df_latest_location_counts = repository.select(MAX_DATETIME_BY_LOCATION_SQL)

        if df_latest_location_counts.empty:
            df_latest_location_counts = location_service.get_all_locations()


        df_new_counts_by_location = pd.DataFrame(columns=['LOCATION_ID','SENSING_DATETIME','DIRECTION_1','DIRECTION_2','TOTAL_OF_DIRECTIONS'])
        for index, df_latest_location_count in df_latest_location_counts.iterrows():
            df_new_counts_per_min = ingest_new_location_data(df_latest_location_count)

            if not isinstance(df_new_counts_per_min, pd.DataFrame):
                break

            df_new_counts_by_location = pd.concat([df_new_counts_by_location, df_new_counts_per_min], ignore_index=True)

        df_new_counts_by_location = df_new_counts_by_location.drop(columns=['SENSING_DATE', 'SENSING_TIME'], errors='ignore')

        repository.insert(df_new_counts_by_location)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
            }
        ),
    }        
    

def ingest_new_location_data(df_latest_count_per_min):
    new_location_counts = fetch_counts_per_min(location_id=df_latest_count_per_min["LOCATION_ID"], sensing_datetime_gt=df_latest_count_per_min["LATEST_SENSING_DATETIME"])
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

    return df_new_counts_per_minute
