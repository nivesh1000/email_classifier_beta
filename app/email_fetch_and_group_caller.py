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

# Setup logger (Simple logging to a file)
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

logger = logging.getLogger()


def generate_last_3_days_email_url() -> str:
    """
    Generate the URL to fetch emails received in the last 3 days using Microsoft Graph API.
 
    Returns:
        str: The URL for fetching emails from the last 3 days.
    """
    today = datetime.utcnow()
    start_of_range = today - timedelta(days=3)  # 3 days ago
    end_of_range = today
 
    # Format times in ISO 8601
    start_time = start_of_range.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    end_time = end_of_range.isoformat() + "Z"
 
    # Construct the URL for filtering emails by receivedDateTime
    url = (
        f"https://graph.microsoft.com/v1.0/me/messages?"
        f"$top=5&"
        f"$filter=receivedDateTime ge {start_time} and receivedDateTime le {end_time}"
        f"&$orderby=receivedDateTime DESC"
    )
 
    return url

def generate_all_email_url() -> str:
    """Generate the URL to fetch all emails using Microsoft Graph API."""
    try:
        # return "https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge 2024-02-20T00:00:00Z and receivedDateTime lt 2024-02-20T23:59:59Z&$orderby=receivedDateTime" #sample f0r feb 20

        return "https://graph.microsoft.com/v1.0/me/messages?$top=5&$orderby=receivedDateTime"
    except Exception as e:
        logger.error(f"Error generating all email URL: {e}")
        return ""

def generate_today_email_url() -> str:
    """Generate the URL to fetch emails received today using Microsoft Graph API."""
    try:
        today = datetime.utcnow()
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

        start_time = start_of_day.isoformat() + "Z"
        end_time = end_of_day.isoformat() + "Z"

        return (
            f"https://graph.microsoft.com/v1.0/me/messages?"
            f"$filter=receivedDateTime ge {start_time} and receivedDateTime le {end_time}"
            f"&$orderby=receivedDateTime DESC"
        )
    except Exception as e:
        logger.error(f"Error generating today's email URL: {e}")
        return ""

def read_json_file(file_path: str) -> Optional[dict]:
    """Reads a JSON file and returns the data as a Python dictionary."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON format in: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error reading '{file_path}': {e}")
    return None

def main():
    """Main function to fetch, classify, and save today's emails."""
    if not ACCESS_TOKEN:
        logger.error("ACCESS_TOKEN not found. Please check your .env file.")
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
            logger.error(f"Error saving grouped emails: {e}")
            return

        logger.info("Email Classification Done!!!")
    
    except Exception as e:
        logger.error(f"Error processing emails: {e}")

if __name__ == "__main__":
    main()
