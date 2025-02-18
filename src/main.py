import time
import requests
from msal import PublicClientApplication
from bs4 import BeautifulSoup

# 🔹 Azure AD Details
CLIENT_ID = "fffc84e3-f4cc-46d8-a94f-d44993f2460c"
TENANT_ID = "ecefbb66-e571-4a04-ad37-82492edec860"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.Read"]  # ✅ Removed 'offline_access' (not needed for device flow)

# 🔹 MSAL Authentication (Interactive)
app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

# Step 1: Initiate Device Flow
flow = app.initiate_device_flow(SCOPES)
print(f"🔗 Go to: {flow['verification_uri']} and enter this code: {flow['user_code']}")

# print("flow : ",flow)
token_response = app.acquire_token_by_device_flow(flow)
# ✅ Get refresh token if available
print("✅ Successfully authenticated!")
print(token_response)
access_token = token_response["access_token"]

# 🔹 Poll for New Emails Every 30 Seconds
headers = lambda: {"Authorization": f"Bearer {access_token}"}
email_url = (
    "https://graph.microsoft.com/v1.0/me/messages?$top=1&$orderby=receivedDateTime DESC"
)

while True:
    try:
        response = requests.get(email_url, headers=headers())
        # print('response: ',response.json())
        if response.status_code == 200:
            emails = response.json().get("value", [])
            email = emails[0]
            print(f"Subject: {email.get('subject')}")
            print(
                f"From: {email.get('from', {}).get('emailAddress', {}).get('address')}"
            )
            print(
                f"To: {email.get('toRecipients', {})[0].get('emailAddress').get('address')}"
            )
            print(f"Received: {email.get('receivedDateTime')}")

            # Extract email body
            raw_body = email.get("body", {}).get("content", "No body available")

            # Remove HTML tags
            clean_body = BeautifulSoup(raw_body, "html.parser").get_text()

            print(
                f"Body:\n{clean_body.strip()[:500]}"
            )  # Trim long emails to 500 chars for readability
            print("-" * 80)
        else:
            print("❌ Failed to fetch emails:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"🚨 Network Error: {e}")

    time.sleep(30)  # Poll every 30 seconds


#########################################################################################3
#########################################################################################


import os
from dotenv import load_dotenv
from Email_Fetcher.email_fetcher import fetch_emails_by_page
from Authenticator.authenticator import (
    get_access_token,
)  # Import the function to get the access token

# Load environment variables
load_dotenv()

# Access credentials from .env
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
MAILBOX_USER_ID = os.getenv("MAILBOX_USER_ID")  # User ID/email from .env
EMAIL_API_BASE_URL = os.getenv("EMAIL_API_BASE_URL")


def main():
    """Main function to authenticate, fetch, and process emails."""
    if not (TENANT_ID and CLIENT_ID and CLIENT_SECRET and MAILBOX_USER_ID):
        print("One or more required environment variables are missing.")
        return

    try:
        # Generate access token
        access_token = get_access_token(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
        print("Access token successfully obtained.")

        # Build the email URL
        email_url = f"{EMAIL_API_BASE_URL}/users/{MAILBOX_USER_ID}/messages?$top=10&$orderby=receivedDateTime DESC"

        # Fetch emails page by page
        current_url = email_url
        while current_url:
            results = fetch_emails_by_page(access_token, MAILBOX_USER_ID, current_url)

            # Process emails on the current page
            emails = next(results, [])
            for email in emails:
                print(f"Subject: {email.get('subject')}")
                # will apply filters here
                # print(f"From: {email.get('from', {}).get('emailAddress', {}).get('address')}")
                # print(f"Received: {email.get('receivedDateTime')}")

            # Get the next page URL
            current_url = next(results, None)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
