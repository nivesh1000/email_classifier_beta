
import re
import os
import json
import msal
import boto3
import logging
import requests
import webbrowser
import pandas as pd
from datetime import datetime
import io
import random

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants for OAuth2.0 authentication and API access
SCOPES = ['User.Read','Mail.Read', 'Mail.Send','Mail.ReadWrite']
APP_ID = 'a7c0a132-7332-4d7e-a59b-879f4d227bcb'
# APP_ID = '6bed9aa0-273d-459a-96b5-0ef657c3a6ee'
current_utc_time = datetime.utcnow()
formatted_time = current_utc_time.strftime('%Y')
current_year = int(formatted_time)

base_tmp_path = "/tmp/"

# Generate a random 2-digit number
random_number = random.randint(10, 99)

s3_client = boto3.client('s3')

def generate_access_token(app_id, scopes):
    access_token_cache = msal.SerializableTokenCache()
    
    # local_filename_iniial = '/var/task/api_token_access.json'
    filename = 'api_token_access_intermidiate.json'
    S3_BUCKET_NAME = "ingest-o365-email-attatchments"
    S3_KEY = 'email_tokens_file/arp_new.json'
    
    local_file_path = f'{base_tmp_path}{filename}'
    try:
        s3_client.download_file(S3_BUCKET_NAME, S3_KEY, local_file_path)
        with open(local_file_path, 'r') as token_file:
            access_token_cache.deserialize(token_file.read())
    except s3_client.exceptions.NoSuchKey:
        print("Token file not found in S3. Starting fresh.")
    # if os.path.exists(local_filename_iniial):
    #     access_token_cache.deserialize(open(local_filename_iniial, 'r').read())

    client = msal.PublicClientApplication(client_id=app_id, token_cache=access_token_cache)

    accounts = client.get_accounts()
    if accounts:
        token_response = client.acquire_token_silent(scopes, account=accounts[0])
    else:
        flow = client.initiate_device_flow(scopes=scopes)
        print('User code :' + flow['user_code'])
        webbrowser.open(flow['verification_uri'])
        token_response = client.acquire_token_by_device_flow(flow)
        
    # Save the updated token cache to the temporary file
    with open(local_file_path, 'w') as token_file:
        token_file.write(access_token_cache.serialize())
    
    # Upload the token cache to S3
    s3_client.upload_file(local_file_path, S3_BUCKET_NAME, S3_KEY)
    print(f"file uploaded in s3--------------")

    # with open(local_file_path, 'w') as _f:
    #     _f.write(access_token_cache.serialize())
        
    # # Also save the updated token cache to the permanent file
    # with open(local_filename_iniial, 'w') as perm_file:
    #     perm_file.write(access_token_cache.serialize())
    return token_response
    

def get_emails(access_token,current_year):
    # endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime gt {current_year}-01-01T14:30:00Z"
    endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime gt {current_year}-01-01T01:30:00Z&$select=subject,receivedDateTime,sender,sentDateTime,changeKey,bodyPreview,internetMessageHeaders,body"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    emails = []
    while endpoint:
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            data = response.json()
            emails.extend(data.get('value', []))
            endpoint = data.get('@odata.nextLink')  # Get the nextLink if present
        else:
            raise Exception(f"Error fetching emails: {response.status_code} - {response.text}")
    return emails
        
# Function to convert HTML to plain text
def html_to_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

# Function to delete an email by ID
def delete_email(access_token, id_email):
    endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages/{id_email}"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.delete(endpoint, headers=headers)
    
    if response.status_code == 204:
        print(f"Email with ID {id_email} deleted successfully.")
    elif response.status_code == 404:
        print(f"Email with ID {id_email} not found. It may have already been deleted or the ID is incorrect.")
    else:
        raise Exception(f"Error deleting email: {response.status_code} - {response.text}")

def lambda_handler(event, context):
    print(f'event---------{event}')
    
    dataD = event['body']
    logger.info(type(dataD))
    logger.info(f"data : {dataD}")
    data = json.loads(dataD)
    print(f'dat_after_load--------{data}')
    change_key_delete= data["name"]
    print(f'change_key-{change_key_delete}')
    
    # Generate access token for Microsoft Graph API
    token_response = generate_access_token(APP_ID, SCOPES)
    # print(f"tokenresponse---------------------{token_response}")
    access_token = token_response['access_token']
    
    emails = get_emails(access_token,current_year)
    print(f'len_of_emails--------{len(emails)}')
    # Create an in-memory text file (using StringIO)
    file_content = io.StringIO()
    
    # S3 bucket details
    s3_bucket = 'ingest-o365-email-attatchments'
    s3_filename = 'deleted_emails.txt'
    S3_KEY = f'deleted_emails/deleted_emails_{current_utc_time}_{random_number}.txt'
    print(f'S3_KEY----------{S3_KEY}')
    
    for email in emails:
        # email_address = email['from']['emailAddress']['address']
        changeKey = email['changeKey']
        id_email = email['id']
        for i in range(len(change_key_delete)):
            if change_key_delete[i] == changeKey:
                # print(changeKey)
                file_content.write(f"Deleting email with ChangeKey: {changeKey}, email: {email}\n")
                print(f"Deleting email with ChangeKey: {changeKey}")
                
                    
                delete_mail = delete_email(access_token,id_email)
    # Move the file pointer to the beginning
    file_content.seek(0)
    
    # Upload the text file to S3
    response = s3_client.put_object(
        Bucket=s3_bucket,
        Key=S3_KEY,
        Body=file_content.read(),
        ContentType='text/plain'
    )
    # Check if upload was successful
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print(f"File successfully uploaded to S3: {s3_bucket}/{S3_KEY}")
    else:
        print("Failed to upload file to S3.")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
