import msal
import json
import os
from config import CLIENT_ID, TENANT_ID, CERT_THUMBPRINT, PRIVATE_KEY_PATH
from logger import logger

class OutlookAuthenticator:
    _instance = None  
    _token = None  

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OutlookAuthenticator, cls).__new__(cls)
        return cls._instance  

    def get_token(self):
        if not self._token:
            self._token = self._fetch_token()
        return self._token

    def _fetch_token(self):
        try:
            with open(PRIVATE_KEY_PATH, "r") as key_file:
                private_key = key_file.read()

            app = msal.ConfidentialClientApplication(
                CLIENT_ID,
                authority=f"https://login.microsoftonline.com/{TENANT_ID}",
                client_credential={"thumbprint": CERT_THUMBPRINT, "private_key": private_key},
            )

            scopes = ["https://graph.microsoft.com/.default"]
            result = app.acquire_token_for_client(scopes=scopes)

            if "access_token" in result:
                logger.info("Successfully obtained access token.")
                return result["access_token"]
            else:
                logger.error(f"Failed to get token: {json.dumps(result, indent=2)}")
                return None
        except Exception as e:
            logger.error(f"Error in authentication: {str(e)}")
            return None
