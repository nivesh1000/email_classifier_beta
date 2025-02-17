# **chatgpt-optimization:**

# Updated fetcher.py (Now with Exponential Backoff & Redis Pub/Sub)

import aiohttp
import asyncio
import datetime
import json
import aioredis
from authenticator import OutlookAuthenticator
from config import GRAPH_API_URL, REDIS_HOST, REDIS_PORT


async def fetch_emails():
    token = OutlookAuthenticator().get_token()
    headers = {"Authorization": f"Bearer {token}"}
    redis = await aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}")
    next_link = (
        f"{GRAPH_API_URL}?$top=10&$filter=receivedDateTime ge {get_past_24_hours()}"
    )

    async with aiohttp.ClientSession(headers=headers) as session:
        while next_link:
            for attempt in range(5):  # Retry mechanism
                try:
                    async with session.get(next_link) as response:
                        if response.status == 429:  # Too many requests
                            retry_after = int(response.headers.get("Retry-After", 5))
                            print(f"Rate limited. Retrying in {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue

                        data = await response.json()
                        emails = data.get("value", [])
                        for email in emails:
                            await redis.publish(
                                "email_channel", json.dumps(email)
                            )  # Publish event

                        next_link = data.get("@odata.nextLink")  # Handle pagination
                        break
                except Exception as e:
                    print(f"Error: {e}")
                    await asyncio.sleep(2**attempt)  # Exponential backoff


def get_past_24_hours():
    return (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"


async def main():
    await fetch_emails()


if __name__ == "__main__":
    asyncio.run(main())

# ------------------------------------------------
# Updated email_parser.py (Now with Redis Pub/Sub and Celery)

import redis
import json
from celery import Celery
from config import REDIS_HOST, REDIS_PORT

# Initialize Celery
celery_app = Celery("tasks", broker=f"redis://{REDIS_HOST}:{REDIS_PORT}")


def listen_for_emails():
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    pubsub = client.pubsub()
    pubsub.subscribe("email_channel")  # Subscribe to Redis channel

    print("Listening for new emails...")
    for message in pubsub.listen():
        if message["type"] == "message":
            email = json.loads(message["data"])
            process_email.delay(email)  # Send to Celery for parallel processing


@celery_app.task
def process_email(email):
    print(f"Processing email: {email['subject']}")
    # Placeholder for parsing logic


if __name__ == "__main__":
    listen_for_emails()


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# **CHATGPT:**

# authenticator.py (Singleton Pattern for Outlook Authentication)

import requests
import threading
from config import OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET, OUTLOOK_TENANT_ID


class OutlookAuthenticator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(OutlookAuthenticator, cls).__new__(cls)
                    cls._instance.token = cls._instance.authenticate()
        return cls._instance

    def authenticate(self):
        url = f"https://login.microsoftonline.com/{OUTLOOK_TENANT_ID}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": OUTLOOK_CLIENT_ID,
            "client_secret": OUTLOOK_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json().get("access_token")

    def get_token(self):
        return self.token


# -------------------------
# fetcher.py (Asynchronous Email Fetcher)

import aiohttp
import asyncio
import datetime
from authenticator import OutlookAuthenticator
from redis_queue import RedisQueue

GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"


async def fetch_emails():
    token = OutlookAuthenticator().get_token()
    headers = {"Authorization": f"Bearer {token}"}
    queue = RedisQueue()

    async with aiohttp.ClientSession(headers=headers) as session:
        next_link = (
            GRAPH_API_URL
            + f"?$top=10&$filter=receivedDateTime ge {get_past_24_hours()}"
        )
        while next_link:
            async with session.get(next_link) as response:
                data = await response.json()
                emails = data.get("value", [])
                for email in emails:
                    queue.add_email(email)  # Store in Redis
                next_link = data.get("@odata.nextLink")  # Handle pagination


def get_past_24_hours():
    return (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"


async def main():
    await fetch_emails()


if __name__ == "__main__":
    asyncio.run(main())

# --------------------------
# email_parser.py (Triggered When an Email is Stored in Redis)

import time
from redis_queue import RedisQueue


def process_email(email):
    # Placeholder for your parsing logic
    print(f"Processing email: {email['subject']}")


def listen_for_emails():
    queue = RedisQueue()
    while True:
        email = queue.get_email()
        if email:
            process_email(email)
        time.sleep(1)


if __name__ == "__main__":
    listen_for_emails()

# ---------------------------------
# redis_queue.py (Handles Redis Operations)

import redis
import json
from config import REDIS_HOST, REDIS_PORT


class RedisQueue:
    def __init__(self):
        self.client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    def add_email(self, email):
        self.client.lpush("email_queue", json.dumps(email))  # Push email to queue

    def get_email(self):
        email_json = self.client.rpop("email_queue")  # Pop from queue
        return json.loads(email_json) if email_json else None


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# **QWEN**:

# authenticator.py
# This file implements the singleton pattern for Outlook email authentication.

import msal


class OutlookAuthenticator:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(OutlookAuthenticator, cls).__new__(cls)
        return cls._instance

    def __init__(self, client_id, authority, scope):
        self.client_id = client_id
        self.authority = authority
        self.scope = scope
        self.app = None

    def authenticate(self):
        if not self.app:
            self.app = msal.PublicClientApplication(
                self.client_id, authority=self.authority
            )
        result = self.app.acquire_token_interactive(scopes=self.scope)
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception("Authentication failed")


# ---------------------------------------------
# redis_client.py
# This file sets up the Redis client for storing and retrieving emails.

import redis
import json


class RedisClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance

    def __init__(self, host="localhost", port=6379, db=0):
        self.client = redis.StrictRedis(
            host=host, port=port, db=db, decode_responses=True
        )

    def store_email(self, email_id, email_data):
        """Store email in Redis."""
        self.client.set(email_id, json.dumps(email_data))
        self.client.publish(
            "email_channel", email_id
        )  # Publish to trigger email parser

    def get_email(self, email_id):
        """Retrieve email from Redis."""
        email_data = self.client.get(email_id)
        return json.loads(email_data) if email_data else None


# ------------------------------------------------------

# fetch_emails.py
# This file fetches emails for the last 24 hours using async and stores them in Redis.

import asyncio
from datetime import datetime, timedelta
from authenticator import OutlookAuthenticator
from redis_client import RedisClient


class EmailFetcher:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.redis_client = RedisClient()

    async def fetch_emails(self):
        # Simulate fetching emails in batches of 10
        start_time = datetime.utcnow() - timedelta(hours=24)
        batch_size = 10
        page = 1

        while True:
            print(f"Fetching batch {page}...")
            emails = await self._fetch_batch(start_time, batch_size)
            if not emails:
                break

            for email in emails:
                email_id = email["id"]
                self.redis_client.store_email(email_id, email)

            page += 1
            await asyncio.sleep(1)  # Simulate delay between batches

    async def _fetch_batch(self, start_time, batch_size):
        # Simulate API call to fetch emails
        await asyncio.sleep(1)  # Simulate network delay
        # Replace this with actual API call to fetch emails
        return [
            {"id": f"email_{i}", "subject": f"Subject {i}", "body": f"Body {i}"}
            for i in range(batch_size)
        ]


# --------------------------------------------
# email_parser.py
# This file listens to Redis for new emails and parses them.

import asyncio
import json
from redis_client import RedisClient


class EmailParser:
    def __init__(self):
        self.redis_client = RedisClient()

    async def parse_emails(self):
        pubsub = self.redis_client.client.pubsub()
        await pubsub.subscribe("email_channel")

        async for message in pubsub.listen():
            if message["type"] == "message":
                email_id = message["data"]
                email_data = self.redis_client.get_email(email_id)
                if email_data:
                    await self._parse_email(email_data)

    async def _parse_email(self, email_data):
        # Placeholder for parsing logic
        print(f"Parsing email: {email_data['subject']}")
        # Add your parsing logic here


# --------------------------------------_
# main.py
# This is the entry point to run the application.

import asyncio
from authenticator import OutlookAuthenticator
from fetch_emails import EmailFetcher
from email_parser import EmailParser


async def main():
    # Authenticate Outlook
    auth = OutlookAuthenticator(
        client_id="YOUR_CLIENT_ID",
        authority="https://login.microsoftonline.com/common",
        scope=["https://outlook.office.com/.default"],
    )
    auth_token = auth.authenticate()

    # Start fetching emails
    fetcher = EmailFetcher(auth_token)
    fetch_task = asyncio.create_task(fetcher.fetch_emails())

    # Start parsing emails
    parser = EmailParser()
    parse_task = asyncio.create_task(parser.parse_emails())

    # Wait for both tasks to complete
    await asyncio.gather(fetch_task, parse_task)


if __name__ == "__main__":
    asyncio.run(main())
