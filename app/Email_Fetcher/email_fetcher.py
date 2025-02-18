import requests
import time
import os
import logging
from Authenticator.authenticator import UserAuthenticator
# import email_parser

logger = logging.getLogger()
logger.setLevel("INFO")

class EmailFetcher:

	def __init__(self):
		self.authenticator = UserAuthenticator.get_instance() # To Be Updated
		self.next_link = None
		
	def fetch_emails(self):
		
		# Token time check? 
		
		access_token = self.authenticator.generate_token()

		# Use stored graph link:
		graph_url = self.next_link if self.next_link else "https://graph.microsoft.com/v1.0/me/messages"

		params = {
			"$filter"="",
			"$top":5,
		}
		headers = {
			"Authorization": f"Bearer {access_token}",
		}
		try:
			response = requests.get(graph_url, headers = headers, params = params)
			data = response.json
			self.next_link = data.get("@odata.nextLink")  # Store next page link
			return 
		except requests.RequestException as e:
			logging.error(f"Failed to fetch emails: {str(e)}")