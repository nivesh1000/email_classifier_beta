import asyncio
import json
from fetcher import fetch_emails
from email_parser import process_email
from logger import logger


def lambda_handler(event, context):
    """
    AWS Lambda entry point: Fetches emails & processes them.
    """
    logger.info("Lambda function started.")

    try:
        # Since AWS Lambda does not support true async execution, we use asyncio.run()
        asyncio.run(fetch_emails())  # Fetch emails & store in Redis
        asyncio.run(process_email())  # Process emails from Redis

        logger.info("Lambda function completed.")
        return {"statusCode": 200, "body": json.dumps("Execution successful.")}

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {"statusCode": 500, "body": json.dumps(f"Error: {str(e)}")}
