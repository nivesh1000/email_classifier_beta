import os
from dotenv import load_dotenv
from Email_Fetcher.email_fetcher import fetch_emails_by_page
from Authenticator.authenticator import get_access_token  # Import the function to get the access token

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
