import requests
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()
try:
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
except KeyError as e:
    print(f"Error loading environment variables: {e}")    

def delete_email(user_id: str, message_id: str):
    """
    Deletes an email from the specified user's mailbox using Microsoft Graph API.

    Args:
        access_token (str): OAuth 2.0 access token with Mail.ReadWrite permission.
        user_id (str): The user's email or user ID.
        message_id (str): The ID of the email message to delete.

    Returns:
        bool: True if the email was deleted successfully, False otherwise.
    """
    url = f"https://graph.microsoft.com/v1.0/users/{user_id}/messages/{message_id}"
    
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        
        if response.status_code == 204:
            print("Email deleted successfully.")
            return True
        else:
            print(f"Failed to delete email: {response.status_code} - {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Error deleting email: {e}")
        return False

user_id = "jsjd@cynoteck.com"
message_id = "AAMkADUyNWJkNzc1LWUzOTYtNDA3NC05YzUxLWM4YjM5YzkxMzA4OQBGAAAAAAA8gPqitF6FSbY_38fmfSv5BwAh1pkWyVTVQ6n1J3WQcgRhAAAAAAEMAAAh1pkWyVTVQ6n1J3WQcgRhAAAC_RMSAAA="
delete_email(user_id, message_id)
