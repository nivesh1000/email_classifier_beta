import re
import os
import json
import msal
import boto3
import logging
import requests
import webbrowser
import pandas as pd
import mysql.connector
from datetime import datetime
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from mysql.connector import Error, IntegrityError


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants for OAuth2.0 authentication and API access
SCOPES = ['User.Read']
APP_ID = 'a7c0a132-7332-4d7e-a59b-879f4d227bcb'

base_tmp_path = "/tmp/"

# Get current UTC time
current_utc_time = datetime.utcnow()
# Format to ISO 8601 string
# formatted_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')
formatted_time = current_utc_time.strftime('%Y')
current_year = int(formatted_time)



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


def extract_emails(text):
    # Simple regex for extracting email addresses
    email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    return re.findall(email_regex, text)

def process_emails(email, filter_id,filter_name,filter_is_active,subject_id,body_id,email_table_id,keyword_filterId,email_email_id):
    data = []
    # for email in emails:
    subject = email['subject']
    full_body_html = email['body']['content']
    email_body_plain = html_to_text(full_body_html)
    # Remove line breaks and carriage returns
    email_body_plain = email_body_plain.replace("\r\n", " ").replace("\n", " ").replace("\xa0", " ")
    # Remove unnecessary extra spaces
    email_body_plain = re.sub(r'\s+', ' ', email_body_plain).strip()
    
    # Determine if the filter matches based on subject_id and body_id
    filter_match = False
    
    if subject_id == 1 and body_id == 1:
        if filter_name.lower() in subject.lower() or filter_name.lower() in email_body_plain.lower():
            filter_match = True
    elif subject_id == 1:
        if filter_name.lower() in subject.lower():
            filter_match = True
    elif body_id == 1:
        if filter_name.lower() in email_body_plain.lower():
            filter_match = True

    # Check if the email matches the filter criteria
    
    # if filter_name.lower() in subject.lower() or filter_name.lower() in email_body_plain.lower():
    if filter_match:
        sender_address = email['sender']['emailAddress']['address']
        changeKey = email['changeKey']
        received_info = email['receivedDateTime']
        send_info = email['sentDateTime']
        bodyPreview = email['bodyPreview']
        
        
        # Extract email addresses from the plain text body
        extracted_emails = extract_emails(bodyPreview)
        if not extracted_emails:
            extracted_emails.append("")
        
        for extracted_email in extracted_emails:
            data.append((email_table_id,sender_address,send_info,received_info,changeKey,subject,email_body_plain,filter_is_active,1,extracted_email,filter_id,keyword_filterId,email_email_id))
    return data


# Function to post response data
def post_queries_to_api(access_token,json_data):
    # Define the API endpoint and headers for the POST request
    api_url = 'https://dashboard.jsjdmedia.com/api/get-filter'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    try:
        # Send the POST request with the JSON data and headers
        response = requests.post(api_url, headers=headers, json=json_data)
        response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
        print('Data successfully sent to API.')
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response JSON
            response_data = response.json()
        return response_data
    except requests.exceptions.HTTPError as err:
        # Handle HTTP errors
        print(f'HTTP error occurred: {err}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'HTTP error occurred: {err}')
        }
    except Exception as e:
        # Handle other exceptions
        print(f'Other error occurred: {e}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Other error occurred: {e}')
        }
# Function to extract the "To" email address
def extract_to_email(email):
    headers = email.get('internetMessageHeaders', [])
    
    # Loop through headers to find the "To" field
    for header in headers:
        if header.get('name') == 'To':
            value = header.get('value')
            
            # Use regex to extract the email inside angle brackets < >
            match = re.search(r'<([^>]+)>', value)
            if match:
                return match.group(1)  # Extract the email address from < >

            # If no angle brackets, return the value as is
            return value.strip('<>')
    
    return None

# Lambda function handler
def lambda_handler(event, context):
    # HOST = "34.235.162.214"
    # PORT = 3306
    # USER = "staging_adbutler"
    # PASSWORD = "staging_adbutler"
    # DB = "staging_adbutler"
    
    
    HOST = "54.84.90.34"
    PORT = 3306
    USER = "forge"
    PASSWORD = "9FiThZkmAk77r2rF2wZX"
    DB = "adbutler_live"
    TABLE_NAME = "filters_mail_data"
    
    connection = mysql.connector.connect(host=HOST, port=PORT,user=USER,passwd=PASSWORD, db=DB)
    cursor = connection.cursor()
    
    # Connect to the database
    try:
        engine = create_engine(f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")
        logging.info("Database connection established")
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to connect to the database')
        }
    df = pd.read_sql_table(TABLE_NAME, engine)

    # Generate access token for Microsoft Graph API
    token_response = generate_access_token(APP_ID, SCOPES)
    print(f"tokenresponse---------------------{token_response}")
    access_token = token_response['access_token']
    emails = get_emails(access_token,current_year)
    
    print(f"len_of_emails-----------{len(emails)}")
    
    # Prepare the query
    query = "SELECT emailId FROM automated_replies_emails WHERE deleted_at IS NULL;"
    
    email_dict = {'emailList': []}  # Initialize an empty dictionary
    cursor.execute(query)  # Execute the query
    results = cursor.fetchall()  # Fetch all results
    # Loop through the results and append each email_id to the emailList
    for row in results:
        email_dict['emailList'].append(row[0])
    print(email_dict)
    filter_data = post_queries_to_api(access_token,email_dict)
    
    print(f"filter_dat------------{filter_data}")
    
    
    filtered_data = []
    # Process input data
    for item in filter_data:
        # Check if filterData exists in the current item
        if "filterData" in item:
            filtered_data.append(item)
            
    print(f"len_of_filtered_data---{filtered_data}")
    count = 0
    sql_data = []
    for email in emails:
        try:
            count = count+1
            print(count)
            to_email = extract_to_email(email)
            # email_address = email['from']['emailAddress']['address']
            changeKey = email['changeKey']
            subject = email['subject']
            # Check if the subject contains any of the specified keywords
            if any(keyword in subject for keyword in ["RE:", "Re:", "FW:", "FWD"]):
                # print(f"keyword find in subject and skipping")
                print(f"changeKey-{changeKey}")
                continue  # Skip to the next email in the loop
            
            # print("check start in filter")
            # Loop through filtered emails
            for filters in filter_data:
                if filters['filterInfo']:
                    if filters['emailId'] == to_email:
                        # email_address = filters['emailId']
                        # print(email_address)
                        email_tables = filters['filterInfo']['email_tables']
                        for table in email_tables:
                            email_table_id = table['tableId']
                            email_email_id = table['emailId']
                            # print(email_table_id)
                            for filter_item in table['tables']:
                                for filter_entry in filter_item['filters']:
                                    filter_id = filter_entry['filterId']
                                    # print(filter_id)
                                    filterOn_Body = filter_entry['filter_info']['filterOnBody']
                                    # print(filterOn_Body)
                                    filterOn_Subject = filter_entry['filter_info']['filterOnSubject']
                                    # print(filterOn_Subject)
                                    for keyword_entry in filter_entry['filter_info']['keywords']:
                                        keyword_filterId = keyword_entry['filterId']
                                        # print(keyword_filterId)
                                        filter_name = keyword_entry['keyword']
                                        filter_is_active = keyword_entry['is_active']
                                        # keywords.append(keyword)
                                        # print(filter_name)
                                        if not df[
                                            (df['filterTableId'] == filter_id) &
                                            (df['changeKey'] == changeKey)
                                        ].empty:
                                            continue
                                        sql_data.extend(process_emails(email, filter_id,filter_name,filter_is_active,filterOn_Subject,filterOn_Body,email_table_id,keyword_filterId,email_email_id))
                
        except Exception as e:
            continue
        
    print(f"sql_data----------{len(sql_data)}")
    # print(f"sql_data----------{sql_data}")
    
    try:
        sql_query = """INSERT INTO filters_mail_data 
                       (filterTableId, mailTo, sentTime, receiveTime, changeKey, subject, mailBody, mail_status, error_code, error_email,filterId,filterKeywordId,emailId, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""

        cursor.executemany(sql_query, sql_data)  # Use `executemany` to insert multiple rows at once
        connection.commit()  # Commit all changes at once
        logging.info(f"{len(sql_data)} records inserted successfully")
    except mysql.connector.Error as err:
        logging.error(f"Error executing SQL queries: {err}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully inserted data in DB')
    }
  



# import re
# import os
# import json
# import msal
# import boto3
# import logging
# import requests
# import webbrowser
# import pandas as pd
# import mysql.connector
# from datetime import datetime
# from bs4 import BeautifulSoup
# from sqlalchemy import create_engine
# from mysql.connector import Error, IntegrityError


# # Set up logging
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# # Constants for OAuth2.0 authentication and API access
# SCOPES = ['User.Read','Mail.Read', 'Mail.Send','Mail.ReadWrite']
# APP_ID = 'a7c0a132-7332-4d7e-a59b-879f4d227bcb'

# base_tmp_path = "/tmp/"

# # Get current UTC time
# current_utc_time = datetime.utcnow()
# # Format to ISO 8601 string
# # formatted_time = current_utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')
# formatted_time = current_utc_time.strftime('%Y')
# current_year = int(formatted_time)




# s3_client = boto3.client('s3')

# def generate_access_token(app_id, scopes):
#     access_token_cache = msal.SerializableTokenCache()
    
#     # local_filename_iniial = '/var/task/api_token_access.json'
#     filename = 'api_token_access_intermidiate.json'
#     S3_BUCKET_NAME = "ingest-o365-email-attatchments"
#     S3_KEY = 'email_tokens_file/arp_new.json'
    
#     local_file_path = f'{base_tmp_path}{filename}'
#     try:
#         s3_client.download_file(S3_BUCKET_NAME, S3_KEY, local_file_path)
#         with open(local_file_path, 'r') as token_file:
#             access_token_cache.deserialize(token_file.read())
#     except s3_client.exceptions.NoSuchKey:
#         print("Token file not found in S3. Starting fresh.")
#     # if os.path.exists(local_filename_iniial):
#     #     access_token_cache.deserialize(open(local_filename_iniial, 'r').read())

#     client = msal.PublicClientApplication(client_id=app_id, token_cache=access_token_cache)

#     accounts = client.get_accounts()
#     if accounts:
#         token_response = client.acquire_token_silent(scopes, account=accounts[0])
#     else:
#         flow = client.initiate_device_flow(scopes=scopes)
#         print('User code :' + flow['user_code'])
#         webbrowser.open(flow['verification_uri'])
#         token_response = client.acquire_token_by_device_flow(flow)
        
#     # Save the updated token cache to the temporary file
#     with open(local_file_path, 'w') as token_file:
#         token_file.write(access_token_cache.serialize())
    
#     # Upload the token cache to S3
#     s3_client.upload_file(local_file_path, S3_BUCKET_NAME, S3_KEY)
#     print(f"file uploaded in s3--------------")

#     # with open(local_file_path, 'w') as _f:
#     #     _f.write(access_token_cache.serialize())
        
#     # # Also save the updated token cache to the permanent file
#     # with open(local_filename_iniial, 'w') as perm_file:
#     #     perm_file.write(access_token_cache.serialize())
#     return token_response

# def get_emails(access_token,current_year):
#     # endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime gt {current_year}-01-02T14:30:00Z"
#     endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime gt 2024-09-25T14:30:00Z&$select=subject,receivedDateTime,sender,sentDateTime,changeKey,bodyPreview,internetMessageHeaders,body"
#     headers = {
#         'Authorization': f'Bearer {access_token}'
#     }
#     emails = []
#     while endpoint:
#         response = requests.get(endpoint, headers=headers)
#         if response.status_code == 200:
#             data = response.json()
#             emails.extend(data.get('value', []))
#             endpoint = data.get('@odata.nextLink')  # Get the nextLink if present
#         else:
#             raise Exception(f"Error fetching emails: {response.status_code} - {response.text}")
#     return emails
        
        
# # Function to convert HTML to plain text
# def html_to_text(html_content):
#     soup = BeautifulSoup(html_content, 'html.parser')
#     return soup.get_text()


# def extract_emails(text):
#     # Simple regex for extracting email addresses
#     email_regex = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
#     return re.findall(email_regex, text)

# def process_emails(filter_email,email, filter_id,filter_name,filter_is_active,subject_id,body_id,email_table_id,keyword_filterId,email_email_id):
#     print("in process email function")
#     data = []
#     # for email in emails:
#     subject = email['subject']
#     full_body_html = email['body']['content']
#     email_body_plain = html_to_text(full_body_html)
#     print("fetched email text plain")
#     bodyPreview = email['bodyPreview']
#     # Determine if the filter matches based on subject_id and body_id
#     filter_match = False
    
#     if subject_id == 1 and body_id == 1:
#         if filter_name.lower() in subject.lower() or filter_name.lower() in email_body_plain.lower() or filter_name.lower() in bodyPreview.lower():
#             filter_match = True
#     elif subject_id == 1:
#         if filter_name.lower() in subject.lower() :
#             filter_match = True
#     elif body_id == 1:
#         if filter_name.lower() in email_body_plain.lower():
#             filter_match = True
    
#     print(f"filter match ----------{filter_match}")

#     # Check if the email matches the filter criteria
    
#     # if filter_name.lower() in subject.lower() or filter_name.lower() in email_body_plain.lower():
#     if filter_match:
#         sender_address = email['sender']['emailAddress']['address']
#         changeKey = email['changeKey']
#         received_info = email['receivedDateTime']
#         send_info = email['sentDateTime']
        
        
        
#         # Extract email addresses from the plain text body
#         extracted_emails = extract_emails(bodyPreview)
#         if not extracted_emails:
#             extracted_emails.append("")
        
#         for extracted_email in extracted_emails:
#             data.append((email_table_id,sender_address,send_info,received_info,changeKey,subject,email_body_plain,filter_is_active,1,extracted_email,filter_id,keyword_filterId,email_email_id))
#             print(data)
#     return data


# # Function to post response data
# def post_queries_to_api(access_token,json_data):
#     # Define the API endpoint and headers for the POST request
#     api_url = 'https://dashboard.jsjdmedia.com/api/get-filter'
#     headers = {
#         'Authorization': f'Bearer {access_token}',
#         'Content-Type': 'application/json'
#     }
#     try:
#         # Send the POST request with the JSON data and headers
#         response = requests.post(api_url, headers=headers, json=json_data)
#         response.raise_for_status()  # Raise an exception for bad responses (4xx or 5xx)
#         print('Data successfully sent to API.')
#         # Check if the request was successful
#         if response.status_code == 200:
#             # Parse the response JSON
#             response_data = response.json()
#         return response_data
#     except requests.exceptions.HTTPError as err:
#         # Handle HTTP errors
#         print(f'HTTP error occurred: {err}')
#         return {
#             'statusCode': 500,
#             'body': json.dumps(f'HTTP error occurred: {err}')
#         }
#     except Exception as e:
#         # Handle other exceptions
#         print(f'Other error occurred: {e}')
#         return {
#             'statusCode': 500,
#             'body': json.dumps(f'Other error occurred: {e}')
#         }

# # Function to extract the "To" email address
# def extract_to_email(email):
#     headers = email.get('internetMessageHeaders', [])
    
#     # Loop through headers to find the "To" field
#     for header in headers:
#         if header.get('name') == 'To':
#             # Return the value (email address)
#             return header.get('value').strip('<>')  # Strip '<>' to get just the email address
#     return None


# # Lambda function handler
# def lambda_handler(event, context):
#     # HOST = "34.235.162.214"
#     # PORT = 3306
#     # USER = "staging_adbutler"
#     # PASSWORD = "staging_adbutler"
#     # DB = "staging_adbutler"
    
    
#     HOST = "54.84.90.34"
#     PORT = 3306
#     USER = "forge"
#     PASSWORD = "9FiThZkmAk77r2rF2wZX"
#     DB = "adbutler_live"
#     TABLE_NAME = "filters_mail_data"
    
#     connection = mysql.connector.connect(host=HOST, port=PORT,user=USER,passwd=PASSWORD, db=DB)
#     cursor = connection.cursor()
    
#     # Connect to the database
#     try:
#         engine = create_engine(f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")
#         logging.info("Database connection established")
#     except Exception as e:
#         logging.error(f"Error connecting to the database: {e}")
#         return {
#             'statusCode': 500,
#             'body': json.dumps('Failed to connect to the database')
#         }
#     df = pd.read_sql_table(TABLE_NAME, engine)

#     # Generate access token for Microsoft Graph API
#     token_response = generate_access_token(APP_ID, SCOPES)
#     print(f"tokenresponse---------------------{token_response}")
#     access_token = token_response['access_token']
#     emails = get_emails(access_token,current_year)
    
#     print(f"len_of_emails-----------{len(emails)}")

#     # Use a set comprehension to gather unique email addresses
#     # email_address_set = {email.get('from', {}).get('emailAddress', {}).get('address')
#     #     for email in emails if email.get('from', {}).get('emailAddress', {}).get('address')}
    
#     # print(f"len----------{len(email_address_set)}")  # Length of unique email addresses
    
#     # # Create the dictionary in one step using list comprehension
#     # email_dict = {"emailList": [email for i, email in enumerate(email_address_set)]}
#     # # New email to add
#     # new_email = 'csuite@industry411.com'
    
#     # # Append the new email to the 'emailList'
#     # email_dict['emailList'].append(new_email)
#     email_dict = {
#         'emailList': [
#             'postmaster@nationpizza.com',
#             'MAILER-DAEMON@GAGGLE.NET',
#             'csuite@industry411.com',
#             'case@arpnewsletters.com',
#             'asps@arpnewsletters.com',
#             'appa@arpnewsletters.com',
#             'tps@arpnewsletters.com',
#             'bomafw@arpnewsletters.com',
#             'ors@arpnewsletters.com',
#             'massachusettsbankersassociation@arpnewsletters.com',
#             'ddw@arpnewsletters.com',
#             'wsae@arpnewsletters.com',
#             'isac@arpnewsletters.com',
#             'ilapps@arpnewsletters.com',
#             'iddba@arpnewsletters.com',
#             'iafc@arpnewsletters.com',
#             'cpta@arpnewsletters.com',
#             'ava@arpnewsletters.com',
#             'aocoo-hns@arpnewsletters.com',
#             'aic@arpnewsletters.com',
#             'affi@arpnewsletters.com',
#             'acoe@arpnewsletters.com',
#             'aaspa@arpnewsletters.com',
#             'txoga@arpnewsletters.com',
#             'aaenp@arpnewsletters.com',
#             'ibpsa@arpnewsletters.com',
#             'rla@arpnewsletters.com',
#             'tascs@arpnewsletters.com',
#             'aasa@arpnewsletters.com',
#             'nsba@arpnewsletters.com',
#             'woema@arpnewsletters.com',
#             'cpa@arpnewsletters.com',
#             'museum@industry411.com',
#             'np@industry411.com',
#             'arp@arpnewsletters.com',
#             'marketing@industry411.com',
#             'hfm@industry411.com',
#             'dentistry@industry411.com',
#             'surgicalaesthetics@industry411.com',
#             'schoolprincipals@industry411.com',
#             'no-reply@associationrevenuepartners.com',
#             'optometry@industry411.com',
#             'interiordesign@industry411.com',
#             'athleticdirectors@industry411.com',
#             'cybersecurity@industry411.com',
#             'watertreatment@industry411.com',
#             'hr@industry411.com',
#             'orthopaedic@industry411.com',
#             'nachiaramonti@rosineyecare.com',
#             'cmm@binyonvision.com'
#         ]
#     }

#     print(f"emasil_dict-------{email_dict}")
#     filter_data = post_queries_to_api(access_token,email_dict)
    
#     print(f"filter_dat------------{filter_data}")
    
    
#     filtered_data = []
#     # Process input data
#     for item in filter_data:
#         # Check if filterData exists in the current item
#         if "filterData" in item:
#             filtered_data.append(item)
            
#     print(f"len_of_filtered_data---{filtered_data}")
    
#     sql_data = []
#     batch_size = 10  # Set batch size for ingestion
#     counter = 0 
#     for email in emails:
#         try:
#             to_email = extract_to_email(email)
#             email_address = email['from']['emailAddress']['address']
#             changeKey = email['changeKey']
#             full_body_html = email['body']['content']
#             # Loop through filtered emails
#              # Loop through filtered emails
#             for filters in filter_data:
#                 if filters['filterInfo']:
#                     fiternew = filters['emailId']
#                     # filteremaulcheck = f'mailto:{fiternew}'
#                     if fiternew == to_email:
#                         print("condition matched")
#                     # print(f"email address matched----{email_address}")
#                     # email_address = filters['emailId']
#                     # print(email_address)
#                         filter_email = filters['emailId']
#                         email_tables = filters['filterInfo']['email_tables']
#                         for table in email_tables:
#                             email_table_id = table['tableId']
#                             email_email_id = table['emailId']
#                             # print(email_table_id)
#                             for filter_item in table['tables']:
#                                 for filter_entry in filter_item['filters']:
#                                     filter_id = filter_entry['filterId']
#                                     # print(filter_id)
#                                     filterOn_Body = filter_entry['filter_info']['filterOnBody']
#                                     # print(filterOn_Body)
#                                     filterOn_Subject = filter_entry['filter_info']['filterOnSubject']
#                                     # print(filterOn_Subject)
#                                     for keyword_entry in filter_entry['filter_info']['keywords']:
#                                         keyword_filterId = keyword_entry['filterId']
#                                         # print(keyword_filterId)
#                                         filter_name = keyword_entry['keyword']
#                                         filter_is_active = keyword_entry['is_active']
#                                         # keywords.append(keyword)
#                                         # print(filter_name)
#                                         if not df[
#                                             (df['filterId'] == filter_id) &
#                                             (df['changeKey'] == changeKey)
#                                         ].empty:
#                                             continue
#                                         sql_data.extend(process_emails(filter_email,email, filter_id,filter_name,filter_is_active,filterOn_Subject,filterOn_Body,email_table_id,keyword_filterId,email_email_id))
#                                         counter += 1  # Increment the counter for each processed email
                                    
#                                         # Check if batch size is reached
#                                         if counter == batch_size:
#                                             # Ingest the data here (for example, save to DB or file)
#                                             try:
#                                                 sql_query = """INSERT INTO filters_mail_data 
#                                                               (filterTableId, mailTo, sentTime, receiveTime, changeKey, subject, mailBody, mail_status, error_code, error_email,filterId,filterKeywordId,emailId, created_at, updated_at)
#                                                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
                                        
#                                                 cursor.executemany(sql_query, sql_data)  # Use `executemany` to insert multiple rows at once
#                                                 connection.commit()  # Commit all changes at once
#                                                 logging.info(f"{len(sql_data)} records inserted successfully")
#                                             except mysql.connector.Error as err:
#                                                 logging.error(f"Error executing SQL queries: {err}")
#                                             # print(f"Ingested batch of {batch_size} emails.")
                                            
#                                             # Reset the sql_data list and counter after ingestion
#                                             sql_data = []
#                                             counter = 0
                
#         except Exception as e:
#             continue
        
#     # print(f"sql_data----------{len(sql_data)}")
    
#     try:
#         sql_query = """INSERT INTO filters_mail_data 
#                       (filterTableId, mailTo, sentTime, receiveTime, changeKey, subject, mailBody, mail_status, error_code, error_email,filterId,filterKeywordId,emailId, created_at, updated_at)
#                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""

#         cursor.executemany(sql_query, sql_data)  # Use `executemany` to insert multiple rows at once
#         connection.commit()  # Commit all changes at once
#         logging.info(f"{len(sql_data)} records inserted successfully")
#     except mysql.connector.Error as err:
#         logging.error(f"Error executing SQL queries: {err}")
    
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Successfully inserted data in DB')
#     }
  
