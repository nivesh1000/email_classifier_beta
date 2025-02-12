import os
import boto3
from ftplib import FTP
import json
# import tempfile

base_tmp_path = "/tmp/"


# Helper function to extract timestamp
def extract_timestamp(filename):
    try:
        parts = filename.split('_')
        if len(parts) > 3:
            timestamp = parts[-1].split('.')[0]
            return int(timestamp)
    except (IndexError, ValueError):
        return None
        
        
        
def lambda_handler(event, context):
    # FTP server details
    ftp_server = "ftp.arpjobs.com"
    ftp_user = "dsqjsjd@arpjobs.com"
    ftp_password = "e4m,a6IwE@9t"
    directory = "/nextiva"
    
    # S3 bucket to upload the file (set this as an environment variable)
    # s3_bucket = os.getenv('S3_BUCKET')
    
    # Connect to the FTP server
    ftp = FTP(ftp_server)
    ftp.login(user=ftp_user, passwd=ftp_password)
    
    # Change to the desired directory
    ftp.cwd(directory)
    
    # List files in the directory
    files = ftp.nlst()  # Returns a list of filenames in the directory
    
    

    # Filter and sort files based on timestamp
    file_timestamps = [(file, extract_timestamp(file)) for file in files if extract_timestamp(file) is not None]
    file_timestamps.sort(key=lambda x: x[1], reverse=True)
    
    # Check if there are any files to download
    if not file_timestamps:
        print("No files found that match the pattern.")
        return {'statusCode': 404, 'body': 'No files found'}
    
    # count =0
    # # Get the latest file
    # if file_timestamps:
    #     for file in  file_timestamps:
    #         count = count+1
    #         # if count<=10:
    #         #     continue
    #         latest_file = file[0]
    #         print(f"Latest file: {latest_file}")
    #         with open(latest_file, 'wb') as local_file:
    #             ftp.retrbinary(f'RETR {latest_file}', local_file.write)
        
    #         print(f"File downloaded successfully: {latest_file}")
            
    #         if count == 20:
    #             break
    # else:
    #     print("No files found that match the pattern.")
        
    latest_file = file_timestamps[0][0]
    print(f"Downloading latest file: {latest_file}")
    
    local_file_path = f'{base_tmp_path}{latest_file}'
    
    S3_BUCKET_NAME = "jsjd-nextiva-data"
    S3_KEY = f'input/{latest_file}'
    s3_client = boto3.client('s3')
    
    try:
        s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=S3_KEY)
        # If the file exists, it will not raise an exception, and we can skip ingestion
        print(f"File {latest_file} already exists in S3. Skipping ingestion.")
        return {
            'statusCode': 200,
            'body': f'File {latest_file} already exists in S3. No need to ingest again.'
        }
    except s3_client.exceptions.ClientError as e:
        # If the file does not exist, head_object will raise a 404 exception, and we proceed with ingestion
        if e.response['Error']['Code'] != '404':
            print(f"Error checking file in S3: {e}")
            return {
                'statusCode': 500,
                'body': f"Error checking file in S3: {e}"
            }
    
    # Download the latest file to a temporary location
    with open(local_file_path, 'wb') as tmp_file:
        ftp.retrbinary(f'RETR {latest_file}', tmp_file.write)
        tmp_file_path = tmp_file.name
    
    
    
    # Upload the file to S3
    
    s3_client.upload_file(tmp_file_path, S3_BUCKET_NAME, S3_KEY)
    
    print(f"File {S3_KEY} uploaded to S3 bucket {S3_BUCKET_NAME}.")
    
    # Clean up the temporary file
    os.remove(tmp_file_path)
    
    # Close the FTP connection
    ftp.quit()

    return {
        'statusCode': 200,
        'body': f'Successfully downloaded and uploaded {latest_file} to {S3_BUCKET_NAME}'
    }
