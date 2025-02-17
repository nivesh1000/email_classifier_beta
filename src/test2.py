import jwt
import base64
import time
import os
from dotenv import load_dotenv, set_key

# Load the .env file
load_dotenv()

# Get the JSON file path from the .env file
env_path = os.getenv('.env')

# Your token
token = "eyJ0eXAiOiJKV1QiLCJub25jZSI6Ii1wRWxRUVIzRjFiLXdHQzJzWTNOX3Vva0ZaVmpDWm1tc3YySFRoaGFhMWMiLCJhbGciOiJSUzI1NiIsIng1dCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayIsImtpZCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lY2VmYmI2Ni1lNTcxLTRhMDQtYWQzNy04MjQ5MmVkZWM4NjAvIiwiaWF0IjoxNzM5NTA1NzQ4LCJuYmYiOjE3Mzk1MDU3NDgsImV4cCI6MTczOTUwOTk1OCwiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFWUUFxLzhaQUFBQXZiKzh6UDBvWlVCcEZlV1NCb3U2N2FOd2ZYSGsyV01EVkh0R1ZxZWxCbUxHQXRhaXV1WWRoMUFoL2pRMUorR2hFZkZ5WU9TdnhJZ0xrbkdnL0VIdUdDUzRyUmtYU2hLNzkwSWhaa1p4VVVJPSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwX2Rpc3BsYXluYW1lIjoiRW1haWwtQWNjZXNzIiwiYXBwaWQiOiIyZWM0NmY0Ny03MTkyLTQ3YWYtYjY0MC1mNWNiYjZjYmY4NDkiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6Ikt1bWFyIiwiZ2l2ZW5fbmFtZSI6Ik5pdmVzaCIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjQ5LjI0OS4xNTYuMiIsIm5hbWUiOiJOaXZlc2ggS3VtYXIiLCJvaWQiOiJkMTJlYmNiOC0wMjU5LTQ5NDctYTNmNy1kZjZlNjQxZDM4NGQiLCJwbGF0ZiI6IjgiLCJwdWlkIjoiMTAwMzIwMDM5NzI4MDVFMyIsInJoIjoiMS5BVk1BWnJ2djdISGxCRXF0TjRKSkx0N0lZQU1BQUFBQUFBQUF3QUFBQUFBQUFBQlRBTTFUQUEuIiwic2NwIjoiTWFpbC5SZWFkIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMDAyMDg4MzktYjQ4Zi1kOWZkLWMyZjYtNjQ3NjU5YWRkZjA5Iiwic2lnbmluX3N0YXRlIjpbImttc2kiXSwic3ViIjoiMzJkRVJwUjdoend4bHV5ZThzTUxuZVBoSHdVRExoakgxR1ZsQzZtZzN1MCIsInRlbmFudF9yZWdpb25fc2NvcGUiOiJBUyIsInRpZCI6ImVjZWZiYjY2LWU1NzEtNGEwNC1hZDM3LTgyNDkyZWRlYzg2MCIsInVuaXF1ZV9uYW1lIjoibml2ZXNoLmt1bWFyQGN5bm90ZWNrLmNvbSIsInVwbiI6Im5pdmVzaC5rdW1hckBjeW5vdGVjay5jb20iLCJ1dGkiOiJmZWVlalJtSkxrYVIwSTRzakRFR0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2lkcmVsIjoiMSA0IiwieG1zX3N0Ijp7InN1YiI6Ik5OS3lZejVFODF0Y3VwRDFnYWl1NFg1YXQzOFZHb3ZqYlg2NURCeTFMVUEifSwieG1zX3RjZHQiOjEzOTg4NDk0NjZ9.BImPct3M1UB_hx2n97WegK35K2oLn-6cB4o5xxWcn_KuGYc_53D5ELSy-9cf-FPMCz5vuH6RG5hILGsTrkCRM0ET_n_fXKHN6vpl-VCMZn-rACUkq7iVFV-n8cJbQPTtWENcCOnnRY8w6DnKM0ccKR9XVL2sTUEKSjZ3c5DUei4aeFYUzKncwSSY7yP2VqEhiitjUjb-Ud52VGrGW9OngzrCTfHFIBf9mYxcalcg7Y9mXGXCcWeNLSE11tGySUs89mytfRYqZpq1Q7uWTcccQaw877rXuWoSBxEz9Hi7wWoNjpfQDspYi9evKn_N6CLyyeVB3IfGQJmeHrZ4nCJMZA"
token = os.getenv("ACCESS_TOKEN")
# Decode the token without verifying the signature
decoded_token = jwt.decode(token, options={"verify_signature": False})

# Extract the expiry time
expiry_time = decoded_token.get("exp")

# Get the current time
current_time = int(time.time())

# Calculate the remaining time (in seconds)
remaining_time_seconds = expiry_time - current_time

if remaining_time_seconds > 0:
    # Convert to minutes and hours
    remaining_minutes = remaining_time_seconds // 60
    remaining_hours = remaining_minutes // 60

    print(f"Token will expire in: {remaining_time_seconds} seconds")
    print(f"Token will expire in: {remaining_minutes} minutes")
    print(f"Token will expire in: {remaining_hours} hours")
else:
    print("Token has already expired!")


def check_refresh_token_expiry(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            import time
            current_time = int(time.time())
            if current_time >= exp:
                return "Refresh token is expired."
            return f"Refresh token is valid. Expires in {exp - current_time} seconds."
        return "No expiration info available in the token."
    except Exception as e:
        return f"Unable to decode token: {e}"

import jwt
refresh_token = os.getenv("REFRESH_TOKEN")
print(check_refresh_token_expiry(refresh_token))



