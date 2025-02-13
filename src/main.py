from utilities.authenticate import authenticate_user
from datetime import datetime, timezone, timedelta
from utilities.email_fetcher import emails_fetcher
from bs4 import BeautifulSoup

# Function to get today's start and end time in ISO 8601 format (UTC)
def get_today_time_range():
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day.isoformat().replace('+00:00', 'Z'), end_of_day.isoformat().replace('+00:00', 'Z')



def main():
    SCOPES = ["Mail.Read"]
    CLIENT_ID = "2ec46f47-7192-47af-b640-f5cbb6cbf849"
    TENANT_ID = "ecefbb66-e571-4a04-ad37-82492edec860"
    access_token=authenticate_user(TENANT_ID,CLIENT_ID,SCOPES)
    start_time, end_time = get_today_time_range()
    email_url = (
        f"https://graph.microsoft.com/v1.0/me/messages?"
        f"$filter=receivedDateTime ge {start_time} and receivedDateTime lt {end_time}"
        f"&$orderby=receivedDateTime DESC"
    )
    emails=emails_fetcher(access_token,email_url)
    for email in emails:
        print(f"Subject: {email.get('subject')}")
        print(f"From: {email.get('from', {}).get('emailAddress', {}).get('address')}")
        print(f"To: {email.get('toRecipients', [{}])[0].get('emailAddress', {}).get('address')}")
        print(f"Received: {email.get('receivedDateTime')}")

        # Extract email body
        raw_body = email.get("body", {}).get("content", "No body available")
        clean_body = BeautifulSoup(raw_body, "html.parser").get_text()

        print(f"Body:\n{clean_body.strip()[:500]}")  # Trim long emails to 500 chars
        print("-" * 80)
        




if __name__ == "__main__":
    main()
