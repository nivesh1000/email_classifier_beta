import time
import requests
from msal import PublicClientApplication
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# 🔹 Azure AD Details
CLIENT_ID = "2ec46f47-7192-47af-b640-f5cbb6cbf849"
TENANT_ID = "ecefbb66-e571-4a04-ad37-82492edec860"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.Read"]

# 🔹 MSAL Authentication (Interactive)
app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)

# Step 1: Initiate Device Flow
flow = app.initiate_device_flow(SCOPES)
print(f"🔗 Go to: {flow['verification_uri']} and enter this code: {flow['user_code']}")

token_response = app.acquire_token_by_device_flow(flow)
print("✅ Successfully authenticated!")
access_token = token_response["access_token"]

# 🔹 Poll for New Emails Every 30 Seconds
headers = lambda: {"Authorization": f"Bearer {access_token}"}

# Function to get today's start and end time in ISO 8601 format (UTC)
def get_today_time_range():
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day.isoformat().replace('+00:00', 'Z'), end_of_day.isoformat().replace('+00:00', 'Z')

start_time, end_time = get_today_time_range()

# Construct the email URL without quotes around the datetime values
email_url = (
    f"https://graph.microsoft.com/v1.0/me/messages?"
    f"$filter=receivedDateTime ge {start_time} and receivedDateTime lt {end_time}"
    f"&$orderby=receivedDateTime DESC"
)


while True:
    try:
        response = requests.get(email_url, headers=headers())
        if response.status_code == 200:
            emails = response.json().get("value", [])
            if not emails:
                print("No emails received today.")
            else:
                for email in emails:
                    print(f"Subject: {email.get('subject')}")
                    print(f"From: {email.get('from', {}).get('emailAddress', {}).get('address')}")
                    print(f"To: {email.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address')}")
                    print(f"Received: {email.get('receivedDateTime')}")

                    # Extract email body
                    raw_body = email.get("body", {}).get("content", "No body available")
                    clean_body = BeautifulSoup(raw_body, "html.parser").get_text()

                    print(f"Body:\n{clean_body.strip()[:500]}")  # Trim long emails to 500 chars
                    print("-" * 80)
        else:
            print("❌ Failed to fetch emails:", response.json())

    except requests.exceptions.RequestException as e:
        print(f"🚨 Network Error: {e}")

    time.sleep(30)  # Poll every 30 seconds
