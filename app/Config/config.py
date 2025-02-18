import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
MAILBOX_USER_ID = os.getenv("MAILBOX_USER_ID")
EMAIL_API_BASE_URL = os.getenv("EMAIL_API_BASE_URL", "https://graph.microsoft.com/v1.0")
SCOPES = os.getenv("SCOPES")