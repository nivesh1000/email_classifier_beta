import msal
import requests

# Replace these with your Azure AD app details
tenant_id = "ecefbb66-e571-4a04-ad37-82492edec860"
client_id = "2ec46f47-7192-47af-b640-f5cbb6cbf849"
cert_thumbprint = "10EA8AED98BD728831AC3CBDC82CA4C1E2200566"  # Thumbprint from Azure AD
private_key_path = "certificate/private_key.pem"  # Path to your private key file

# Load the private key
with open(private_key_path, "r") as key_file:
    private_key = key_file.read()

# Create an MSAL confidential client
app = msal.ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential={"thumbprint": cert_thumbprint, "private_key": private_key},
)

# Acquire token
scopes = ["https://graph.microsoft.com/.default"]
result = app.acquire_token_for_client(scopes=scopes)
print(result)
if "access_token" in result:
    access_token = result["access_token"]
    # print("Access Token:", access_token)

    # Example: Fetch emails using Microsoft Graph API
    user_email = "harshit.lohani@cynoteck.com"
    graph_url = f"https://graph.microsoft.com/v1.0/users/{user_email}/messages"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(graph_url, headers=headers)
    emails = response.json()
    # print(emails)
#     print("Fetched emails:")
#     for email in emails.get("value", []):
#         print(f"Subject: {email['subject']}, Received: {email['receivedDateTime']}")
# else:
#     print("Error acquiring token:", result.get("error_description"))
