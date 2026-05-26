import json
import logging

from api_client import fetch_records

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """Poll the API once per invocation (e.g. EventBridge schedule every minute)."""
    data = fetch_records()
    results = data.get("results", [])

    logger.info(
        "Fetched %s records (total_count=%s)",
        len(results),
        data.get("total_count"),
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "total_count": data.get("total_count"),
                "record_count": len(results),
                "results": results,
            }
        ),
    }
