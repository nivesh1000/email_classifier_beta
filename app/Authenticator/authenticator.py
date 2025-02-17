from msal import PublicClientApplication
from Config.config import TENANT_ID,CLIENT_ID


def authenticate_user():    #email_info is a dictionary of client_id and tenant_id
    
    AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
    SCOPES = ["Mail.Read"]
    # 🔹 MSAL Authentication (Interactive)
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
        # Step 1: Initiate Device Flow
    flow = app.initiate_device_flow(SCOPES)
    print(f"Go to: {flow['verification_uri']} and enter this code: {flow['user_code']}")
    token_response = app.acquire_token_by_device_flow(flow)
    print("Successfully authenticated!")
    print(token_response)
    return token_response["access_token"]