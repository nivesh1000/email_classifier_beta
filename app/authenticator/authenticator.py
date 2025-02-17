import requests
import sys

def get_access_token(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Authenticate with Microsoft and retrieve an access token.

    Args:
        tenant_id (str): Azure Tenant ID.
        client_id (str): Azure Application (Client) ID.
        client_secret (str): Azure Application Secret Key.

    Returns:
        str: Access token from the response.

    Raises:
        Exception: If the authentication request fails.
    """
    # Microsoft OAuth2.0 token endpoint
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

    # Request payload
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    try:
        # Send the POST request to retrieve the token
        response = requests.post(token_url, data=data)
        response.raise_for_status()  # Raise an error for HTTP status codes >= 400
        token_response = response.json()

        # Extract and return the access token
        access_token = token_response.get("access_token")
        if not access_token:
            raise Exception("Access token not found in response.")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"Error while fetching access token: {e}")
        sys.exit(1)

