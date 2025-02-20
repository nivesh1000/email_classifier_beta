import requests
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from Email_Fetcher.email_fetcher import fetch_emails
from Email_Filter.filter import classify_emails

# Load environment variables from .env file
load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


def generate_all_email_url() -> str:
    """
    Generate the URL to fetch all emails using Microsoft Graph API.

    Returns:
        str: The URL for fetching all emails.
    """
    # Construct the URL for fetching all emails
    url = (
        "https://graph.microsoft.com/v1.0/me/messages?"
        "$orderby=receivedDateTime DESC"
    )
    return url



def generate_today_email_url() -> str:
    """
    Generate the URL to fetch emails received today using Microsoft Graph API.

    Returns:
        str: The URL for fetching today's emails.
    """
    today = datetime.utcnow()
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

    # Format times in ISO 8601
    start_time = start_of_day.isoformat() + "Z"
    end_time = end_of_day.isoformat() + "Z"

    # Construct the URL for filtering emails by receivedDateTime
    url = (
        f"https://graph.microsoft.com/v1.0/me/messages?"
        f"$filter=receivedDateTime ge {start_time} and receivedDateTime le {end_time}"
        f"&$orderby=receivedDateTime DESC"
    )
    return url

import json

def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python object.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or list: The data loaded from the JSON file.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



def main():
    """
    Main function to fetch and display today's emails.
    """
    if not ACCESS_TOKEN:
        print("ACCESS_TOKEN not found. Please ensure it's set in your .env file.")
        return

    # Generate the email URL for today's emails
    email_url = generate_all_email_url()

    # Fetch today's emails using the generated URL and access token
    try:
        emails=fetch_emails(email_url, ACCESS_TOKEN)
        print("Emails fetched succesfully !!!")
        email_filters=read_json_file("app/Config/filter.json")
        print("Email classification process started....")
        grouped_emails=classify_emails(emails,email_filters)
        print(grouped_emails[0:2])
        print("Email Classification Done!!!")
    except Exception as e:
        print(f"Error fetching emails: {e}")


if __name__ == "__main__":
    main()
