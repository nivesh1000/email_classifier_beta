import json
from token_refresher import TokenManager
# from email_fetcher import fetch_emails
from email_fetch_and_group_caller import flow_control
from datetime import datetime, timedelta
from email_fetcher import fetch_emails
from filter import classify_emails 
def generate_today_email_url() -> str:
    """
    Generate the URL to fetch emails received today using Microsoft Graph API.

    Returns:
        str: The URL for fetching today's emails.
    """
    today = datetime.utcnow()
    start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)

    # Format times in ISO 8601
    start_time = start_of_day.isoformat() + "Z"
    end_time = end_of_day.isoformat() + "Z"

    # Construct the URL for filtering emails by receivedDateTime
    url = (
        f"https://graph.microsoft.com/v1.0/me/messages?"
        f"$filter=receivedDateTime ge {start_time} and receivedDateTime le {end_time}"
        f"&$orderby=receivedDateTime DESC"
    )
    return url


def read_json_file(file_path):
    """
    Reads a JSON file and returns the data as a Python object.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or list: The data loaded from the JSON file.
    """
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file '{file_path}' is not a valid JSON file.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")



 
def lambda_handler(event, context):
    token_manager = TokenManager()
    task = event.get('task')  # Determine which task to run based on the event
    
    if task == 'refresh_tokens':
        return token_manager.refresh_tokens()
    elif task == 'fetch_emails':
        tokens=read_json_file("tokens.json")
        ACCESS_TOKEN = tokens.get("access_token")
        if not ACCESS_TOKEN:
            return {"error": "Access token not found"}
        email_url=generate_today_email_url()
        emails=fetch_emails(email_url, ACCESS_TOKEN)
        return classify_emails(emails)
    else:
        return {"error": "Invalid task specified"}
 
# def lambda_handler(event, context):
#     token_manager = TokenManager()
#     token_manager.refresh_tokens()
#     result = flow_control()
#     if result:
#         print(result)
#         return result
#     else:
#         return {"error": "Invalid task specified"}
 