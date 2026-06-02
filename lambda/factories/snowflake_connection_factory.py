import json
import boto3
import snowflake.connector

class SnowflakeConnectionFactory:
    def __init__(self, database_name, schema_name):
        self.credentials = SnowflakeConnectionFactory.__get_snowflake_creds("snowflake-credentials")
        self.database_name = database_name
        self.schema_name = schema_name

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __get_snowflake_creds(secret_name):
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name='us-east-2'
        )
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])

    def get_snowflake_connection(self):
        return snowflake.connector.connect(
            user=self.credentials["user"],
            account=self.credentials["account"],
            private_key=self.credentials["privateKey"] if "privateKey" in self.credentials else None,
            password=self.credentials.get("password"),
            warehouse=self.credentials.get("warehouse")
        )