import asyncio
import aioredis
import json
from external_api import fetch_filters, send_parsed_data
from config import REDIS_HOST, REDIS_PORT
from logger import logger


async def process_email():
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    filters = fetch_filters()  # Get filtering rules

    while True:
        try:
            email_json = await redis.rpop("email_queue")
            if not email_json:
                await asyncio.sleep(2)
                continue

            email = json.loads(email_json)
            parsed_data = parse_email(email, filters)

            if parsed_data:
                send_parsed_data(parsed_data)

        except Exception as e:
            logger.error(f"Error processing email: {e}")


async def parse_email(email, filters):
    """Apply parsing logic (to be implemented)"""
    try:
        parsed_data = {"email_id": email.get("id"), "subject": email.get("subject")}

        for filter_rule in filters:
            if filter_rule["keyword"] in email.get("body", ""):
                parsed_data["matched_rule"] = filter_rule["keyword"]

        logger.info(f"Parsed email {email.get('id')}: {parsed_data}")
        return parsed_data
    except Exception as e:
        logger.error(f"Error in parsing email: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(process_email())
