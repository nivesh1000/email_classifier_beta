from typing import List, Dict
import requests
from bs4 import BeautifulSoup


def fetch_emails(email_url: str, access_token: str) -> List[Dict]:
    """
    Fetch emails from Microsoft Graph API, handling pagination.

    Args:
        email_url (str): The initial URL to fetch emails.
        access_token (str): The access token for authenticating the API request.

    Returns:
        List[Dict]: A list of dictionaries containing email details.

    Raises:
        Exception: If the API request fails.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    next_url = email_url  # Start with the initial URL
    email_list = []  # To store email data

    try:
        while next_url:  # Keep iterating until there are no more pages
            response = requests.get(next_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                emails = data.get("value", [])

                if not emails:
                    print("No emails found.")
                    return email_list

                # Process the current batch of emails
                for email in emails:
                    # Extract required fields
                    email_id = email.get("id", "Unknown ID")
                    from_address = email.get("from", {}).get("emailAddress", {}).get("address", "N/A")
                    to_recipients = email.get("toRecipients", [])
                    to_address = (
                        to_recipients[0].get("emailAddress", {}).get("address", "N/A")
                        if to_recipients else "N/A"
                    )
                    subject = email.get("subject", "No subject")
                    raw_body = email.get("body", {}).get("content", "No body available")
                    clean_body = BeautifulSoup(raw_body, "html.parser").get_text().strip()

                    # Append the email dictionary to the list
                    email_list.append({
                        "email_id": email_id,
                        "to": to_address,
                        "from": from_address,
                        "subject": subject,
                        "body": clean_body,
                        "group": ""  # Empty for now
                    })

                # Check if there's a next page
                next_url = data.get("@odata.nextLink", None)

            else:
                print("Failed to fetch emails:", response.json())
                break

    except Exception as e:
        print("An error occurred:", str(e))

    return email_list
