import requests


def emails_fetcher(access_token,email_url):
    headers = lambda: {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(email_url, headers=headers())
        if response.status_code == 200:
            emails = response.json().get("value", [])
            return emails
        else:
            print("Failed to fetch emails:", response.json())
            return []

    except requests.exceptions.RequestException as e:
        print(f"Network Error: {e}")