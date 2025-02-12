import mysql.connector
from mysql.connector import Error, IntegrityError
from sqlalchemy import create_engine
import pandas as pd
import json

import boto3
from urllib.parse import urlparse
from botocore.exceptions import NoCredentialsError
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def genarate_presigned_url(source_bucket,s3_image_path):

    expires_in = 1 * 24 * 60 * 60 # 7 Day
    
    s3_key = s3_image_path

    url = boto3.client('s3').generate_presigned_url(
    ClientMethod='get_object', 
    Params={'Bucket': source_bucket, 'Key': s3_key},
    ExpiresIn=expires_in)

    return url
    
# # Function to extract bucket name and object key from a presigned URL
# def extract_bucket_key_from_url(url):
#     parsed_url = urlparse(url)
#     path_parts = parsed_url.path.lstrip('/').split('/')
#     bucket_name = path_parts[0]
#     object_key = '/'.join(path_parts[1:])
#     return bucket_name, object_key
    
# Function to refresh presigned URLs in the DataFrame
def refresh_presigned_urls(df, url_column,connection,cursor):
    for index, row in df.iterrows():
        old_url = row[url_column]
        un_id = row['id']
        bucket_name = row['s3_bucket']
        object_key = row['s3_key']
        # bucket_name, object_key = extract_bucket_key_from_url(old_url)
        print(f"{bucket_name}----------{object_key}")
        new_url = genarate_presigned_url(bucket_name, object_key)
        record_id_column = 'id'
        table_name = 'filters_newsleads_data'
        query = f"UPDATE {table_name} SET {url_column} = %s WHERE {record_id_column} = %s"
        cursor.execute(query, (new_url, un_id))
        connection.commit()
        print(f"presigned url updated in DB.")
    cursor.close()

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
        
    # df = pd.read_sql_table(TABLE_NAME, engine)
    # local_file_path = f'{base_tmp_path}filter.csv'
    # df.to_csv(local_file_path)
    # s3 = boto3.client('s3')
    # s3.upload_file(local_file_path, "ingest-o365-email-attatchments", f"filter.csv")    
        
    
    
    df_filtered = pd.read_sql_table('filters_newsleads_data', engine)
    print(f'df_filtered_shape-----------{df_filtered.shape}')
    
    # Refresh presigned URLs
    refresh_presigned_urls(df_filtered, 'imagePath',connection,cursor)

        # for index, row in df.iterrows():
        #     tableId = row['id']
        #     keywords = row['imagePath']

    return {
        'statusCode': 200,
        'body': json.dumps('Successfully updated data in DB')
    }

