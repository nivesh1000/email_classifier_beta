import requests
import json

def fetch_groups():
    url = "https://staging.jsjdmedia.com/api/groups"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for non-200 responses
        data = response.json()  # Parse JSON response
        
        # print(json.dumps(data, indent=4))  # Pretty print JSON data
        return data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None