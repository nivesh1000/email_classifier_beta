import json
import requests

from logger import EmailParser

logger = EmailParser.get_logger()


def delete_emails(emails_to_remove, access_token):
    """
        Delete emails using email id
    """

    if not emails_to_remove:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No emails provided"})
        }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    base_url = ""

    for email in emails_to_remove:
        try:
            url = f"{base_url}/{email}"
            response = requests.delete(url, headers=headers)
            if response.status_code == 204:
                logger.info(f"successfully deleted email: {email}")
            else:
                logger.error(f"Failed to delete email: {
                             email} - Status: {response.status_code}, Error: {response.text}")

        except requests.exceptions.Timeout:
            logger.error(f"Timeout occurred while deleting: {email}")

        except requests.exceptions.ConnectionError:
            logger.error(f"connection error while deleting: {email}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting: {
                         email}: {str(e)}")

    return {
        "statusCode": 200,
        "body": json.dumps({"sucess": "Successfully deleted emails"})
    }
