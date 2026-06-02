
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
import json
import boto3
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SnowflakeRepository:
    def __init__(self, snowflake_connection):
        self.conn = snowflake_connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def insert(self, table_name, df_rows):
        try:
            success, n_chunks, n_rows, _ = write_pandas(
                self.conn,
                df_rows,
                table_name=table_name,
                auto_create_table=False,
                use_logical_type=True,
                quote_identifiers = False,
                on_error = "ABORT_STATEMENT"
            )
        except snowflake.connector.errors.ProgrammingError as e:
            logger.error(f"The actual underlying Snowflake error is: {e}")

    def select(self, sql_statement):
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql_statement)
            output = cursor.fetch_pandas_all()
        finally:
            cursor.close()

        return output

    def truncate(self, table_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"TRUNCATE TABLE {table_name}")
        finally:
            cursor.close()

    def execute_procedure(self, stored_procedure_name):
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"CALL {stored_procedure_name}();")
        finally:
            cursor.close()


