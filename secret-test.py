import requests

# Replace these with your Azure AD app details
tenant_id = "ecefbb66-e571-4a04-ad37-82492edec860"
client_id = "2ec46f47-7192-47af-b640-f5cbb6cbf849"
client_secret = "ZRT8Q~wS5N2c_qeovKBZYqR-v4e3cBs0h1Wq4c8u"
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
