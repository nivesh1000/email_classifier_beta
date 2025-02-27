import os
import json
import requests
import boto3
from config import TENANT_ID, CLIENT_ID, SCOPES


class TokenManager:
    """
    A class for managing access and refresh tokens, including refreshing and updating them in a JSON file.
    """
    def __init__(self):
        
        # Read credentials from the config module
        self.tenant_id = TENANT_ID
        self.client_id = CLIENT_ID
        # self.refresh_token = REFRESH_TOKEN
        self.scopes = SCOPES
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        # Ensure credentials are valid
        if not self.tenant_id or not self.client_id:
            raise ValueError("Missing required credentials in the configuration.")

    def refreshing_token(self,tokens):
        """
        Refreshes the access and refresh tokens using the current refresh token.
        Updates the tokens in the JSON file.
        """
        self.refresh_token = tokens["REFRESH_TOKEN"]

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
            updated_tokens = response.json()
            new_access_token = updated_tokens["access_token"]
            new_refresh_token = updated_tokens.get("refresh_token", self.refresh_token)  # Use current if new not provided
            print("✅ Tokens refreshed successfully!")
            # Save the tokens to the JSON file
            self.update_ssm_parameters(new_access_token, new_refresh_token)

        else:
            # Handle error response
            print("❌ Failed to refresh tokens:", response.status_code, response.text)
            raise Exception("Token refresh failed.")


    def update_ssm_parameters(self, access_token, refresh_token):
        """Update ACCESS_TOKEN and REFRESH_TOKEN in AWS SSM Parameter Store as String"""
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))

        try:
            # Update ACCESS_TOKEN as String
            ssm.put_parameter(
                Name="ACCESS_TOKEN",
                Value=access_token,
                Type="String",  # Now using "String" instead of "SecureString"
                Overwrite=True  # Allow updates
            )

            # Update REFRESH_TOKEN as String
            ssm.put_parameter(
                Name="REFRESH_TOKEN",
                Value=refresh_token,
                Type="String",
                Overwrite=True
            )

            return {"message": "Parameters updated successfully"}

        except Exception as e:
            print(f"Error updating SSM parameters: {e}")
            return {"error": str(e)}
