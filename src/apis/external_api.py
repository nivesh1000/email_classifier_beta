import requests
from config import FILTER_API_URL, PARSED_DATA_API_URL
from logger import logger

def fetch_filters():
    """Fetch parsing filters from external API."""
    try:
        response = requests.get(FILTER_API_URL)
        response.raise_for_status()  
        filters = response.json()
        logger.info("Successfully fetched filters from external API.")
        return filters
    except requests.RequestException as e:
        logger.error(f"Error fetching filters: {e}")
        return []

def send_parsed_data(parsed_data):
    """Send parsed data to external API."""
    try:
        response = requests.post(PARSED_DATA_API_URL, json=parsed_data)
        response.raise_for_status()  
        logger.info("Successfully sent parsed data to external API.")
    except requests.RequestException as e:
        logger.error(f"Error sending parsed data: {e}")
