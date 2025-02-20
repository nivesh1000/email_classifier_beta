import requests
from bs4 import BeautifulSoup



def fetch_emails(email_url: str, access_token: str) -> None:
    """
    Fetch emails from Microsoft Graph API, handling pagination.

    Args:
        email_url (str): The initial URL to fetch emails.
        access_token (str): The access token for authenticating the API request.

    Raises:
        Exception: If the API request fails.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    next_url = email_url  # Start with the initial URL

    try:
        while next_url:  # Keep iterating until there are no more pages
            response = requests.get(next_url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                emails = data.get("value", [])

                if not emails:
                    print("No emails found.")
                    return

                # Process the current batch of emails
                for email in emails:
                    print(f"Subject: {email.get('subject', 'No subject')}")
                    print(f"From: {email.get('from', {}).get('emailAddress', {}).get('address', 'N/A')}")

                    # Handle 'toRecipients' safely
                    to_recipients = email.get("toRecipients", [])
                    if to_recipients:
                        to_address = to_recipients[0].get("emailAddress", {}).get("address", "N/A")
                    else:
                        to_address = "N/A"
                    print(f"To: {to_address}")

                    print(f"Received: {email.get('receivedDateTime', 'Unknown time')}")

                    # Extract and clean email body
                    raw_body = email.get("body", {}).get("content", "No body available")
                    clean_body = BeautifulSoup(raw_body, "html.parser").get_text()
                    print(f"Body:\n{clean_body.strip()[0:20]}")
                    print("-" * 80)

                # Check if there's a next page
                next_url = data.get("@odata.nextLink", None)

            else:
                print("Failed to fetch emails:", response.json())
                break

    except requests.exceptions.RequestException as e:
        print(f"🚨 Network Error: {e}")
        raise
