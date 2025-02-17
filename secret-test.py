import requests


user_id = "harshit.lohani@cynoteck.com"
# Step 1: Get Access Token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://graph.microsoft.com/.default",
}
token_response = requests.post(token_url, data=token_data)
access_token = token_response.json().get("access_token")

# Step 2: Fetch Emails
user_email = "nivesh.kumar@cynoteck.com"  # Your email address
graph_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(graph_url, headers=headers)

if response.status_code == 200:
    emails = response.json()
    print(emails)
    print("Fetched emails:")
    for email in emails.get("value", []):
        print(f"Subject: {email['subject']}, Received: {email['receivedDateTime']}")
else:
    print("Error fetching emails:", response.status_code, response.json())
