import os
from dotenv import load_dotenv, set_key
from msal import PublicClientApplication
from Config.config import TENANT_ID, CLIENT_ID, SCOPES
from typing import Optional


class UserAuthenticator:
    _instance = None

    @staticmethod
    def get_instance():
        """
        Retrieve the singleton instance of UserAuthenticator.

        Returns:
            UserAuthenticator: The singleton instance.
        """
        if UserAuthenticator._instance is None:
            raise Exception("UserAuthenticator is not initialized. Use the constructor.")
        return UserAuthenticator._instance

    def __init__(self):
        """
        Initialize the UserAuthenticator singleton. Reads credentials from the config module.
        """
        if UserAuthenticator._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            UserAuthenticator._instance = self

        # Read credentials directly from config
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        self.scopes = SCOPES

        # Validate credentials
        if not self.tenant_id or not self.client_id:
            raise ValueError("Missing required credentials in the environment variables.")

        # Initialize MSAL PublicClientApplication
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.app = PublicClientApplication(self.client_id, authority=self.authority)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

        # Load environment variables
        load_dotenv()

    def authenticate_user(self) -> str:
        """
        Authenticate the user using the MSAL device flow and return the access token.

        Returns:
            str: The access token.

        Raises:
            Exception: If the authentication flow fails.
        """
        if self.access_token:
            print("Reusing existing access token.")
            return self.access_token

        # Step 1: Initiate Device Flow
        flow = self.app.initiate_device_flow(self.scopes)
        print(f"Go to: {flow['verification_uri']} and enter this code: {flow['user_code']}")

        try:
            token_response = self.app.acquire_token_by_device_flow(flow)
            if "access_token" not in token_response:
                raise Exception(f"Authentication failed: {token_response.get('error_description')}")

            print("Successfully authenticated!")
            self.access_token = token_response["access_token"]
            self.refresh_token = token_response.get("refresh_token")  # Get refresh token if available

            # Save both access and refresh tokens to the .env file
            self.save_tokens_to_env(self.access_token, self.refresh_token)

            return self.access_token
        except Exception as e:
            print(f"Authentication error: {e}")
            raise

    def save_tokens_to_env(self, access_token: str, refresh_token: Optional[str]):
        """
        Save or update the access and refresh tokens in the .env file.

        Args:
            access_token (str): The access token to save.
            refresh_token (Optional[str]): The refresh token to save (if available).
        """
        env_file = ".env"

        # Load environment variables to ensure updates are written correctly
        load_dotenv(env_file)

        # Update or create the ACCESS_TOKEN entry
        set_key(env_file, "ACCESS_TOKEN", access_token)

        # Update or create the REFRESH_TOKEN entry if it exists
        if refresh_token:
            set_key(env_file, "REFRESH_TOKEN", refresh_token)

        print("Access and refresh tokens saved/updated in the .env file.")
