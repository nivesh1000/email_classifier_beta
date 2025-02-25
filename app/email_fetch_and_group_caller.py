import logging
import os
from datetime import datetime, timedelta
from typing import Optional
import json
from dotenv import load_dotenv
from Email_Fetcher.email_fetcher import fetch_emails
from Email_Filter.filter import classify_emails
from api.get_filters import fetch_groups

# Load environment variables from .env file
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Setup logger
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("EmailProcessor")

def generate_all_email_url() -> str:
    """
    Generate the URL to fetch all emails using Microsoft Graph API.

    Returns:
        str: The URL for fetching all emails.
    """
    try:
        url = (
            "https://graph.microsoft.com/v1.0/me/messages?"
            "$orderby=receivedDateTime"
        )
        return url
    except Exception as e:
        logger.error(f"Error generating all email URL: {e}")
        return ""

def generate_today_email_url() -> str:
    """
    Generate the URL to fetch emails received today using Microsoft Graph API.

    Returns:
        str: The URL for fetching today's emails.
    """
    try:
        today = datetime.utcnow()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

        start_time = start_of_day.isoformat() + "Z"
        end_time = end_of_day.isoformat() + "Z"

        url = (
            f"https://graph.microsoft.com/v1.0/me/messages?"
            f"$filter=receivedDateTime ge {start_time} and receivedDateTime le {end_time}"
            f"&$orderby=receivedDateTime DESC"
        )
        return url
    except Exception as e:
        logger.error(f"Error generating today's email URL: {e}")
        return ""

def read_json_file(file_path: str) -> Optional[dict]:
    """
    Reads a JSON file and returns the data as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or None: The data loaded from the JSON file, or None if an error occurs.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        logger.error(f"Error: The file '{file_path}' is not a valid JSON file.")
    except Exception as e:
        logger.error(f"An unexpected error occurred while reading '{file_path}': {e}")
    
    return None

def main():
    """
    Main function to fetch, classify, and save today's emails.
    """
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN not found. Please ensure it's set in your .env file.")
        return

    email_url = generate_today_email_url()
    if not email_url:
        logger.error("Failed to generate email URL. Exiting...")
        return

    try:
        emails = fetch_emails(email_url, ACCESS_TOKEN)

        email_filters = fetch_groups()
        if email_filters is None:
            logger.error("Failed to load email filters. Exiting...")
            return

        grouped_emails = classify_emails(emails, email_filters)

        try:
            with open("grouped_emails.json", "w", encoding="utf-8") as f:
                json.dump({"data": grouped_emails}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving grouped emails to file: {e}")
            return

        for email_ in grouped_emails:
            print(email_)
            print('-' * 73)

        logger.info("Email Classification Done!!!")
    
    except Exception as e:
        logger.error(f"Error processing emails: {e}")

if __name__ == "__main__":
    main()
