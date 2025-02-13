import requests

# Azure AD tenant and application details
tenant_id = "ecefbb66-e571-4a04-ad37-82492edec860"  # Replace with your Azure AD tenant ID
client_id = "2ec46f47-7192-47af-b640-f5cbb6cbf849"  # Replace with your application's client ID
client_secret = "Kl48Q~7Tl1y7Z3CkLkWMIo75hqMXzdQIsxUSza-5"  # Replace with your application's client secret
# refresh_token = '1.AVMAZrvv7HHlBEqtN4JJLt7IYEdvxC6Sca9HtkD1y7bL-ElTAM1TAA.AgABAwEAAABVrSpeuWamRam2jAF1XRQEAwDs_wUA9P-oH8fV0zIbKbXIIfAq96pMvDHeLKqVHRKcIvfGalAwzXcB3foZ7t0a8L9_r50jGElnycX_ldknzQt0g0R3UsBwA0GbWVjd3QIzQxNfpj8EeDV-epiSb31Qm0sA68Eyc0cQkcAjyITl3WErspSScHjRfrtdJQf3V8HAyIME00AHRn9HsxGxID-obL4Xtku1VmR5RjrwFbi0S1WCSFegThQR5PnHqIKSO7ENPxQW0Nv_e1TS2-SIx_Ev2QUpcZUCsAlD_dOlOpMALHu2cFI6QH-8wQRLdl8j0fn6hLJC_oYEgcVO0_BLnWsapX5ppYoRFZu2W0YGTvXhslzWB129IUlkZL3JLKYo7CvqdsmNEuiPMdGjQTpRAaIyzIRZoRMlJSl4Alr6xWcCtHIkpBoRbcNaMR8YTZHI0xmyIRAedsdVKGz6zGeUKpJermGsKb2t4kqUGKbs8SVoZSW4gbHeK4P_c5-BczHdamyBuots6b5wFbs9k4nCdSxa8SpZlasROd_P7FPASJLx6Fo9LulyTavq5rCJpRP_TkdPKsEk3764o0S1PwJ8-ZcwGA_fGXJIgvAQTSTwDrjIO4brcN85pOrc4h9L2iMpMetrYIXdwqGuMGONh1VlWI5jXa9BrXCrtkuwEP9cX6KPgaSMsm55nh0TjaJNRRX96LVnSAxTwudBQCV1qIgJk2FqStxdKAghEIqwCVX6pI0sdYvMQcbLaCRh-4KkqR2rs3ve8RwLdWRWtxZBB9S6DbTnwKToDyNSeYJJkwVzPvBHVcp0iXjHZPZvLWE7tJ4PIw1R1EmnMOdc8-ab-J5dx8XsTSTQyqJMwxs8FQ529PM9riPjbJdmaN2gFA'
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"

# Request payload to refresh the token
payload = {
    "grant_type": "refresh_token",
    "client_id": client_id,
    "refresh_token": refresh_token,
    "scope": "https://graph.microsoft.com/.default"  # Replace with your app's required scopes
}

# Make the request to refresh the token
response = requests.post(token_url, data=payload)

# Handle the response
if response.status_code == 200:
    tokens = response.json()
    new_access_token = tokens["access_token"]
    new_refresh_token = tokens.get("refresh_token", refresh_token)  # May return a new refresh token
    print("New Access Token:", new_access_token)
    print("New Refresh Token:", new_refresh_token)
else:
    print("Failed to refresh token:", response.status_code, response.text)
