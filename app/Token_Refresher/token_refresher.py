import os
import requests
from dotenv import load_dotenv, set_key
from Config.config import TENANT_ID, CLIENT_ID, SCOPES


class TokenManager:
    """
    A class for managing access and refresh tokens, including refreshing and updating them in the .env file.
    """
    def __init__(self):
        # Load environment variables from .env
        load_dotenv()
        
        # Read credentials from the config module
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        self.scopes = SCOPES
        self.refresh_token = os.getenv("REFRESH_TOKEN")
        self.access_token = os.getenv("ACCESS_TOKEN")
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        # Ensure credentials are valid
        if not self.tenant_id or not self.client_id:
            raise ValueError("Missing required credentials in the configuration.")

    def refresh_tokens(self):
        """
        Refreshes the access and refresh tokens using the current refresh token.
        Updates the tokens in the .env file.
        """
        if not self.refresh_token:
            raise ValueError("Missing REFRESH_TOKEN in the environment variables.")

        # Prepare the request payload
        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": self.refresh_token,
            "scope": self.scopes
        }

        # Make the POST request to refresh the token
        response = requests.post(self.token_url, data=payload)

        if response.status_code == 200:
            # Parse the response and extract tokens
            tokens = response.json()
            new_access_token = tokens["access_token"]
            new_refresh_token = tokens.get("refresh_token", self.refresh_token)  # Use current if new not provided
            print("✅ Tokens refreshed successfully!")
            # Save the tokens to the .env file
            self.update_tokens_in_env(new_access_token, new_refresh_token)

            
            # print("New Access Token:", new_access_token)
            # print("New Refresh Token:", new_refresh_token)

        else:
            # Handle error response
            print("❌ Failed to refresh tokens:", response.status_code, response.text)
            raise Exception("Token refresh failed.")

    def update_tokens_in_env(self, access_token: str, refresh_token: str):
        """
        Updates the access and refresh tokens in the .env file.

        Args:
            access_token (str): The new access token to save.
            refresh_token (str): The new refresh token to save.
        """
        env_file = ".env"

        # Load environment variables to ensure updates are written correctly
        load_dotenv(env_file)

        # Update or create the ACCESS_TOKEN entry
        set_key(env_file, "ACCESS_TOKEN", access_token)

        # Update or create the REFRESH_TOKEN entry
        set_key(env_file, "REFRESH_TOKEN", refresh_token)

        print("✅ Tokens updated in the .env file.")
