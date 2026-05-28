
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import json
import boto3


class SnowflakeRepository:
    def __init__(self, snowflake_connection, table_name):
        self.conn = snowflake_connection
        self.table_name = table_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def insert(self, df_rows):
        success, n_chunks, n_rows, _ = write_pandas(
            self.conn,
            df_rows,
            self.table_name,
            auto_create_table=False
        )

    def select(self, sql_statement):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql_statement)
            output = cursor.fetch_pandas_all()
        finally:
            cursor.close()

        return output



