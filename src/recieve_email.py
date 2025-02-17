import boto3
import json
import requests
from msal import ConfidentialClientApplication
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

# 🔹 Azure AD Details
CLIENT_ID = "fffc84e3-f4cc-46d8-a94f-d44993f2460c"
TENANT_ID = "ecefbb66-e571-4a04-ad37-82492edec860"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["Mail.Read"]  # ✅ Scope for reading emails

# MSAL Authentication with Certificate
def authenticate_msal_with_certificate(private_key):
    # Prepare ConfidentialClientApplication with the certificate (using the private key)
    app = ConfidentialClientApplication(
        CLIENT_ID, authority=AUTHORITY, client_credential=private_key
    )

    # Acquire token using the certificate
    result = app.acquire_token_for_client(scopes=SCOPES)

    if "access_token" in result:
        print("✅ Successfully authenticated using certificate!")
        return result["access_token"]
    else:
        print("❌ Authentication failed.")
        return None


# Function to fetch the most recent email
def fetch_recent_email():

    # Get the access token using certificate authentication
    access_token = authenticate_msal_with_certificate(private_key)

    if not access_token:
        return {"error": "Failed to obtain access token."}

    headers = {"Authorization": f"Bearer {access_token}"}
    email_url = "https://graph.microsoft.com/v1.0/me/messages?$top=1&$orderby=receivedDateTime DESC"
    email_details = {}

    try:
        response = requests.get(email_url, headers=headers)
        if response.status_code == 200:
            emails = response.json().get("value", [])
            if emails:
                email = emails[0]
                email_details = {
                    "subject": email.get("subject"),
                    "from": email.get("from", {})
                    .get("emailAddress", {})
                    .get("address"),
                    "to": email.get("toRecipients", {})[0]
                    .get("emailAddress")
                    .get("address"),
                    "received": email.get("receivedDateTime"),
                    "body": clean_email_body(
                        email.get("body", {}).get("content", "No body available")
                    ),
                }
        else:
            print(f"❌ Failed to fetch emails: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"🚨 Network Error: {e}")

    return email_details


# Helper function to clean email body (remove HTML tags)
def clean_email_body(raw_body):
    clean_body = BeautifulSoup(raw_body, "html.parser").get_text()
    return clean_body.strip()[
        :500
    ]  # Limiting body size to 500 characters for readability
