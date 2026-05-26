import json
import logging
import os

import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas

from api_client import fetch_records

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_DATETIME_BY_LOCATION_SQL = """
    SELECT LOCATION_ID, MAX(SENSING_DATETIME) AS LATEST_SENSING_DATETIME
    FROM PEDESTRIAN_ANALYTICS.RAW.LOCATION_DIRECTION_COUNTS
    WHERE LOCATION_ID IN ({placeholders})
    GROUP BY LOCATION_ID
"""


def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        database="PEDESTRIAN_ANALYTICS",
        schema="RAW",
    )

def filter_new_records(results_df, latest_df):    
    merged = results_df.merge(latest_df, on="LOCATION_ID", how="left")
    is_new = (
        merged["LATEST_SENSING_DATETIME"].isna()
        | (merged["SENSING_DATETIME"] > merged["LATEST_SENSING_DATETIME"])
    )
    return merged.loc[is_new].drop(columns=["LATEST_SENSING_DATETIME"])


def insert_records(conn, df):
    write_pandas(conn, df, "LOCATION_DIRECTION_COUNTS")


def lambda_handler(event, context):
    conn = get_snowflake_connection()
    latest_location_counts = pd.read_sql(MAX_DATETIME_BY_LOCATION_SQL, conn)

    new_location_counts = []
    for index, latest_location_count in latest_location_counts.iterrows():
        new_location_counts.append(ingest_new_location_data(latest_location_count))

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "total_count": new_location_counts.get("total_count"),
                "record_count": len(results),
                "results": results,
            }
        ),
    }        
    

def ingest_new_location_data(conn, latest_location_count):
    new_location_counts = fetch_records(location_id=latest_location_count["LOCATION_ID"], sensing_datetime_gt=latest_location_count["SENSING_DATETIME"])
    results = new_location_counts.get("results", [])

    logger.info(
        "Fetched %s records (total_count=%s)",
        len(results),
        new_location_counts.get("total_count"),
    )

    if not results:
        return []

    results_df = pd.DataFrame(results).rename(columns=str.upper)

    results_df.columns = results_df.columns.str.upper()
    latest_df.columns = latest_df.columns.str.upper()
    
    location_ids = results_df["LOCATION_ID"].unique().tolist()

    
    try:        
        new_records_df = filter_new_records(results_df, latest_df)

        if not new_records_df.empty:
            insert_records(conn, new_records_df)
            logger.info("Inserted %s records into LOCATION_DIRECTION_COUNTS", len(new_records_df))
        else:
            logger.info("No new records to insert")
    finally:
        conn.close()
