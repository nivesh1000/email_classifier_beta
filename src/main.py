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
    
    # access_token=authenticate_user(TENANT_ID,CLIENT_ID,SCOPES)
    access_token='eyJ0eXAiOiJKV1QiLCJub25jZSI6Ill5LUd0MUFQb1l0MDZmRTFwLUlscXFyVWNlWjE4RWNoTEUyc3g0YThZeTQiLCJhbGciOiJSUzI1NiIsIng1dCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayIsImtpZCI6ImltaTBZMnowZFlLeEJ0dEFxS19UdDVoWUJUayJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC9lY2VmYmI2Ni1lNTcxLTRhMDQtYWQzNy04MjQ5MmVkZWM4NjAvIiwiaWF0IjoxNzM5NDQ0MTQyLCJuYmYiOjE3Mzk0NDQxNDIsImV4cCI6MTczOTQ0OTIwNCwiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFWUUFxLzhaQUFBQVI3ckNYeGxmR1NEeGNPbUc3anQ3bE92b2tKSGtVZ2tWUFpCRDUyTlV3K1cwS2liVHdPNUx5S013d3g0SWs1Z1FISllWUk1SbzlaWG45OVVORG5pQ0l2TFl2a2dwaXhSeDR2SHd2S1MyMmprPSIsImFtciI6WyJwd2QiLCJtZmEiXSwiYXBwX2Rpc3BsYXluYW1lIjoiRW1haWwtQWNjZXNzIiwiYXBwaWQiOiIyZWM0NmY0Ny03MTkyLTQ3YWYtYjY0MC1mNWNiYjZjYmY4NDkiLCJhcHBpZGFjciI6IjAiLCJmYW1pbHlfbmFtZSI6Ikt1bWFyIiwiZ2l2ZW5fbmFtZSI6Ik5pdmVzaCIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjQ5LjI0OS4xNTYuMiIsIm5hbWUiOiJOaXZlc2ggS3VtYXIiLCJvaWQiOiJkMTJlYmNiOC0wMjU5LTQ5NDctYTNmNy1kZjZlNjQxZDM4NGQiLCJwbGF0ZiI6IjgiLCJwdWlkIjoiMTAwMzIwMDM5NzI4MDVFMyIsInJoIjoiMS5BVk1BWnJ2djdISGxCRXF0TjRKSkx0N0lZQU1BQUFBQUFBQUF3QUFBQUFBQUFBQlRBTTFUQUEuIiwic2NwIjoiTWFpbC5SZWFkIG9wZW5pZCBwcm9maWxlIGVtYWlsIiwic2lkIjoiMDAyMDg4MzktYjQ4Zi1kOWZkLWMyZjYtNjQ3NjU5YWRkZjA5Iiwic2lnbmluX3N0YXRlIjpbImttc2kiXSwic3ViIjoiMzJkRVJwUjdoend4bHV5ZThzTUxuZVBoSHdVRExoakgxR1ZsQzZtZzN1MCIsInRlbmFudF9yZWdpb25fc2NvcGUiOiJBUyIsInRpZCI6ImVjZWZiYjY2LWU1NzEtNGEwNC1hZDM3LTgyNDkyZWRlYzg2MCIsInVuaXF1ZV9uYW1lIjoibml2ZXNoLmt1bWFyQGN5bm90ZWNrLmNvbSIsInVwbiI6Im5pdmVzaC5rdW1hckBjeW5vdGVjay5jb20iLCJ1dGkiOiJFVlY3RlVEclBVZXBEdlNMbHAxYUFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyJiNzlmYmY0ZC0zZWY5LTQ2ODktODE0My03NmIxOTRlODU1MDkiXSwieG1zX2lkcmVsIjoiMSAxNiIsInhtc19zdCI6eyJzdWIiOiJOTkt5WXo1RTgxdGN1cEQxZ2FpdTRYNWF0MzhWR292amJYNjVEQnkxTFVBIn0sInhtc190Y2R0IjoxMzk4ODQ5NDY2fQ.TYLqRCLStuZoGbPRsz7XWcw6B81rPex3HyFkmimxoxComArrApL2IVaNZ9rO7JA8R7KAoku7bCuKsVJ-EvE2bDMWe9eS4UbgOh4BwZUn9ScKUc6rbkVEdSqxacMfama4yRHxrxafPuUiXY9UT8kRpE36Sq65MONyEu6shHV9MFOEawUPUC2mhpGkZ1XsfYZx0GEs0ObsY_DSEAnONay7rPmoTil7mrs_wugsyFMecpBteJaU-HHNMmCcM36Z4YcnFI9HCb-JDdOjCcds9z-vjHJXa4mKjPx7kIUuAo5PvosmSwwmN15By0oVx6bigzZHD7ywRhbA7ihg2PRX2przoQ'
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
