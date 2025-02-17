from msal import ConfidentialClientApplication

client_id = "fffc84e3-f4cc-46d8-a94f-d44993f2460c"
tenant_id = "ecefbb66-e571-4a04-ad37-82492edec860"
authority = f"https://login.microsoftonline.com/{tenant_id}"
private_key = open("certificate/private_key.pem", "r").read()

app = ConfidentialClientApplication(
    client_id, authority=authority, client_credential=private_key
)

result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])


if "access_token" in result:
    print(f"Access token: {result['access_token']}")
else:
    print(f"Authentication failed: {result}")
