import json
import logging
from services.ingestion_service import IngestionService
from factories.snowflake_connection_factory import SnowflakeConnectionFactory


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

connection_factory = SnowflakeConnectionFactory('PEDESTRIAN_ANALYTICS', 'RAW')

def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    with IngestionService(connection_factory) as ingestion_service:
        ingestion_service.process()



        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                }
            ),
        }

