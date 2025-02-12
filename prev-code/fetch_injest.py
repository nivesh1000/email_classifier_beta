import hashlib
import json
import msal
import requests
import webbrowser
import os
import imageio
import io
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from bs4 import BeautifulSoup
import mysql.connector
from mysql.connector import Error, IntegrityError
from sqlalchemy import create_engine
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Define the necessary scopes and the application ID for the Microsoft Graph API
SCOPES = ['User.Read','Mail.Read', 'Mail.Send']
# APP_ID = '6bed9aa0-273d-459a-96b5-0ef657c3a6ee'
APP_ID = 'ddcc0aae-8dd3-4540-9f71-072c0733a524'


current_utc_time = datetime.utcnow()
formatted_time = current_utc_time.strftime('%Y')
current_year = int(formatted_time)

base_tmp_path = "/tmp/"


s3_client = boto3.client('s3')
# Function to generate an access token
def generate_access_token(app_id, scopes):
    access_token_cache = msal.SerializableTokenCache()
    
    # local_filename_iniial = '/var/task/api_token_access.json'
    filename = 'api_token_access_intermidiate.json'
    S3_BUCKET_NAME = "ingest-o365-email-attatchments"
    S3_KEY = 'email_tokens_file/api_token_access_email_attatchments.json'
    
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
    endpoint = f"https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages?$filter=receivedDateTime gt {current_year}-03-01T14:30:00Z"
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




def genarate_presigned_url(source_bucket,s3_image_path):

    expires_in = 7 * 24 * 60 * 60 # 7 Day
    
    s3_key = s3_image_path

    url = boto3.client('s3').generate_presigned_url(
    ClientMethod='get_object', 
    Params={'Bucket': source_bucket, 'Key': s3_key},
    ExpiresIn=expires_in)

    return url


def download_images_from_html(modified_changeKey,html_body,sender_address,tableId,subject,connection,cursor,send_info, target_width=None, target_height=None, max_name_length=100):
    # Parse the HTML
    soup = BeautifulSoup(html_body, 'html.parser')
    # Find all image tags
    img_tags = soup.find_all('img')
    # Ensure the local folder exists
    # os.makedirs(local_folder, exist_ok=True)
    
    print(f"type of target_width------------------------{type(target_width)}")
    print(f"type of target_height------------------------{type(target_height)}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Extract the part of the sender's email before the '@'
    folder_prefix = sender_address.split('@')[0]
    
    # Define folder name based on sender address and image dimensions
    folder_name = f"{folder_prefix}_{target_height}x{target_width}"
    
    # Download each image
    for img in img_tags:
        img_url = img.get('src')
        if not img_url:
            continue
        try:
            # Generate a short filename using a hash
            img_hash = hashlib.sha256(img_url.encode()).hexdigest()
            img_extension = os.path.splitext(img_url)[1]
            if not img_extension:
                img_extension = ".jpg"  # Default to .jpg if no extension found
            img_name = f"{modified_changeKey}_{img_hash}{img_extension}"
            if len(img_name) > max_name_length:
                img_name = f"{modified_changeKey}_{img_hash[:max_name_length//2]}{img_extension}"
            # img_path = os.path.join(local_folder, img_name)
            local_file_path = f'{base_tmp_path}{img_name}'
            s3_key = f"{folder_name}/{img_name}"
            
            # Check if the image already exists in S3
            s3 = boto3.client('s3')
            source_bucket = "ingest-o365-email-attatchments"
            try:
                s3.head_object(Bucket=source_bucket, Key=s3_key)
                print(f"Already exists in S3: {img_name}")
                continue  # Skip this image
            except ClientError:
                pass  # Object does not exist
            # Check if the image already exists
            # if os.path.exists(img_path):
            #     print(f"Already downloaded: {img_url} -> {img_path}")
            #     continue
            # Download the image
            response = requests.get(img_url, stream=True, headers=headers)
            response.raise_for_status()  # Check for request errors
            # Check image dimensions
            img_data = io.BytesIO(response.content)
            try:
                image = imageio.v3.imread(img_data)
                width, height = image.shape[1], image.shape[0]
                
                # Check if the image matches the target dimensions
                if ( width != target_width) or (height != target_height):
                    print(f"Skipping {img_url} due to size {width}x{height}")
                    sql_skip = f"""INSERT INTO filters_newsleads_criteria_missed (newsFilterId,mailTo, imageHeight,imageWidth,imageInfo,email_send_time, created_at, updated_at)
                    values (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
                        
                    data_skip=(tableId,sender_address,target_height, target_width,subject,send_info)
                    
                    cursor.execute(sql_skip, data_skip)
                    connection.commit()
                    print("Record inserted successfully for criteria_missed.")
                    continue
            except Exception as e:
                print(f"Skipping {img_url} due to image read error: {e}")
                continue
            try:
                # Save the image
                # if width == target_width and height == target_height:
                with open(local_file_path, 'wb') as img_file:
                    for chunk in response.iter_content(1024):
                        img_file.write(chunk)
                        
                try:
                    s3 = boto3.client('s3')
                    # s3.download_file(source_bucket, source_key, local_file_path)
                    s3.upload_file(local_file_path, "ingest-o365-email-attatchments", f"{s3_key}")
                    print(f'uploaded file : {img_name}  at path : {s3_key}')
                    s3_path=f's3://ingest-o365-email-attatchments/{img_name}'
                    source_bucket = "ingest-o365-email-attatchments"
                    url = genarate_presigned_url(source_bucket,s3_key)
                    
                    try:
                        sql = f"""INSERT INTO filters_newsleads_data (newsFilterId,mailTo,imagePath, imageHeight,imageWidth,imageInfo,email_send_time,s3_bucket,s3_key, created_at, updated_at)
                        values (%s, %s, %s, %s, %s, %s, %s,%s,%s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
                        
                        data=(tableId,sender_address,url,target_height, target_width,subject,send_info,source_bucket,s3_key)
                        
                        
                        # cursor = connection.cursor()
                        print(f"sql----------{sql}")
                        cursor.execute(sql, data)
                        connection.commit()
                        print("Record inserted successfully")
                    
                    except IntegrityError as e:
                        print(f"IntegrityError: {e}")
                # connection.close()
                except Exception as e:
                    print(e)
                    return
            # attachments_present = True
                # print(f"Downloaded: {img_url} -> {img_path}")
            except OSError as e:
                print(f"Error: {e}")
        except requests.RequestException as e:
            print(f"Failed to download {img_url}: {e}")



def apply_filters(email, keywords, image_height,image_width,tableId,is_active,email_filter,connection,cursor):
    filtered_emails = []
    # GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'
    # headers = {
    #     'Authorization': f'Bearer {access_token}'
    # }
    # for email in emails:
    subject = email['subject'].lower()
    sender_address = email['sender']['emailAddress']['address']
    email_body = email['bodyPreview']
    changeKey = email['changeKey']
    # Replace "/" with "_"
    modified_changeKey = changeKey.replace("/", "_")
    received_info = email['receivedDateTime']
    send_info = email['sentDateTime']
    full_body_html = email['body']['content']
    email_body_plain = html_to_text(full_body_html)
    # for filter_criteria in filters:
        
    matched_keywords = [keyword.lower() for keyword in keywords if keyword.lower() in subject]
    keyword_present = bool(matched_keywords)
    # sender_matched = email_filter in sender_address
    print("match started")
    if keyword_present:
        print("in condition ")
        filtered_emails.append(email)
        # Check attachments for the filtered email
        # if extract_images_from_body(full_body_html, image_height, image_width,sender_address,tableId,subject,connection,cursor):
        if download_images_from_html(modified_changeKey,full_body_html,sender_address,tableId,subject,connection,cursor,send_info,target_width=image_width, target_height=image_height):
        # if check_email_attachments(email['id'], headers, GRAPH_API_ENDPOINT, image_height, image_width,subject,sender_address,email_body,changeKey,received_info,send_info,is_active,tableId):
            print("Attachments found for email with subject:", email['subject'])
        else:
            print("No attachments found for email with subject:", email['subject'])
    return filtered_emails


def lambda_handler(event, context):
    
    # HOST = "34.235.162.214"
    # PORT = 3306
    # USER = "staging_adbutler"
    # PASSWORD = "staging_adbutler"
    # DB = "staging_adbutler"
    # # TABLE_NAME = "automated_newsleads_filters"
    
    HOST = "54.84.90.34"
    PORT = 3306
    USER = "forge"
    PASSWORD = "9FiThZkmAk77r2rF2wZX"
    DB = "adbutler_live"
    TABLE_NAME = "automated_newsleads_filters"
    
    
    
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
    # TABLE_NAME = "nextiva_data_csv_table"
    # df = pd.read_sql_table(TABLE_NAME, engine)
    # local_file_path = f'{base_tmp_path}filter.csv'
    # df.to_csv(local_file_path)
    # s3 = boto3.client('s3')
    # s3.upload_file(local_file_path, "ingest-o365-email-attatchments", f"filter.csv")    
        
    
    df = pd.read_sql_table(TABLE_NAME, engine)
    print(f'df_shape-----------{df.shape}')
    
    df_filtered = pd.read_sql_table('filters_newsleads_data', engine)
    print(f'df_filtered_shape-----------{df_filtered.shape}')
    
    df_filtered_criteria_missed = pd.read_sql_table('filters_newsleads_criteria_missed', engine)
    print(f'df_filtered_criteria_missed_shape-----------{df_filtered_criteria_missed.shape}')
    
    
    
    
    token_response = generate_access_token(APP_ID, SCOPES)
    access_token = token_response['access_token']
    
    emails = get_emails(access_token,current_year)
    print("emails_data_fetched_by_msgraph_API")
    
    for email in emails:
        email_address = email['from']['emailAddress']['address']
        changeKey = email['changeKey']
        send_info = email['sentDateTime']
        # if changeKey in df_filtered['changeKey'].values:
        #         print(f'{changeKey} exists in the column.')
        # else:
    
        for index, row in df.iterrows():
            tableId = row['id']
            keywords = row['filterName']
            email_filter = row['filterToEmail']
            image_height = row['imageHeight']
            image_width = row['imageWidth']
            
            is_active = row['is_active']
            # filterName = row['filterName']
            
            
            
            if not df_filtered[
                (df_filtered['mailTo'] == email_address) &
                (df_filtered['imageHeight'] == image_height) &
                (df_filtered['imageWidth'] == image_width) &
                (df_filtered['email_send_time'] == send_info)
            ].empty:
                print("email attatchments already in table & s3.")
                continue
            if not df_filtered_criteria_missed[
                (df_filtered_criteria_missed['mailTo'] == email_address) &
                (df_filtered_criteria_missed['imageHeight'] == image_height) &
                (df_filtered_criteria_missed['imageWidth'] == image_width) &
                (df_filtered_criteria_missed['email_send_time'] == send_info)
            ].empty:
                print("email attatchments skipping due to criteria already checked.")
                continue
            if  email_address == email_filter:
                keyword_filter = apply_filters(email, keywords, int(image_height),int(image_width),tableId,is_active,email_filter,connection,cursor)
# print(keyword_filter)

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully inserted data in DB')
    }
