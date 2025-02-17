import asyncio
import aioredis
import requests
from authenticator import OutlookAuthenticator
from config import REDIS_HOST, REDIS_PORT
from logger import logger


async def fetch_emails():
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")

    try:
        token = OutlookAuthenticator().get_token()
        if not token:
            logger.error("Failed to get access token.")
            return

        headers = {"Authorization": f"Bearer {token}"}
        url = "https://graph.microsoft.com/v1.0/me/messages?$top=10"

        while True:
            response = requests.get(url, headers=headers)
            emails = response.json().get("value", [])

            for email in emails:
                await redis.lpush("email_queue", str(email))
                logger.info(f"Stored email in Redis queue: {email.get('id')}")

            await asyncio.sleep(5)

    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
    finally:
        await redis.close()


if __name__ == "__main__":
    asyncio.run(fetch_emails())
