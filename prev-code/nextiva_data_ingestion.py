
import pandas as pd
import boto3
import mysql.connector
import json
from pathlib import Path
from sqlalchemy import create_engine
from urllib.parse import unquote_plus
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# logging.basicConfig(level=logging.INFO)


# # Read the data from the csv file 
# def read_data_from_s3(csv_file):
#     df = pd.read_csv(csv_file,header=None)
#     columns_to_select = [0, 5, 6, 8, 9, 10, 11, 13, 18, 120, 156]
#     # Custom column names
#     custom_column_names = ["recordid", "call_direction", "callingnumber", "callednumber", 
#                       "starttime", "usertimezone", "answerindicator", "releasetime", 
#                       "callcategory", "userid", "codec_usage"]

#     # Assign the custom column names to the DataFrame
#     df.columns = [f"col_{i}" for i in range(df.shape[1])]  # Assign temporary names to avoid conflict
#     for idx, col_name in zip(columns_to_select, custom_column_names):
#         df.rename(columns={f"col_{idx}": col_name}, inplace=True)
#     # Get the column names corresponding to the indices
#     column_names = df.columns[columns_to_select]
#     # Select the columns by names
#     selected_columns_df= df[custom_column_names]
#     # Now selected_columns will contain only the specified columns
#     return selected_columns_df

# def read_data_from_s3(csv_file):
#     df = pd.read_csv(csv_file)
#     columns_to_select = ["recordid","call_direction","callingnumber","callednumber","starttime","usertimezone","answerindicator","releasetime","callcategory","userid","codec_usage"]
#     # Get the column names corresponding to the indices
#     # column_names = df.columns[columns_to_select]
#     # print(f"{column_names}")
#     # Select the columns by names
#     selected_columns_df= df[columns_to_select]
#     # Now selected_columns will contain only the specified columns
#     return selected_columns_df

def extract_time_from_filename(filename):
    try:
        # Split the filename by underscores and extract the last part before the .csv
        timestamp_str = filename.split('_')[-1].replace('.csv', '')
        # Convert to a datetime object (assuming the timestamp is in milliseconds)
        dt = datetime.utcfromtimestamp(int(timestamp_str) / 1000)
        # Extract and return only the time part as a string
        return dt.strftime('%H:%M:%S')
    except Exception as e:
        logging.error(f"Error extracting time from filename: {e}")
        return None
        

def read_data_from_s3_v1(csv_file):
    try:
        df = pd.read_csv(csv_file, header=None)
        columns_to_select = [0, 5, 6, 8, 9, 10, 11, 13, 18, 120, 156]
        custom_column_names = ["recordid", "call_direction", "callingnumber", "callednumber", 
                              "starttime", "usertimezone", "answerindicator", "releasetime", 
                              "callcategory", "userid", "codec_usage"]

        df.columns = [f"col_{i}" for i in range(df.shape[1])]  
        for idx, col_name in zip(columns_to_select, custom_column_names):
            df.rename(columns={f"col_{idx}": col_name}, inplace=True)
        
        selected_columns_df = df[custom_column_names]
        # Convert specific columns from float to int
        columns_to_convert = ["callingnumber", "callednumber","starttime","releasetime"]
        selected_columns_df[columns_to_convert] = selected_columns_df[columns_to_convert].apply(pd.to_numeric, errors='coerce').fillna(0)
        selected_columns_df[columns_to_convert] = selected_columns_df[columns_to_convert].astype(int)
        return selected_columns_df
    except Exception as e:
        print(f"Error reading data from CSV: {e}")
        return None

def read_data_from_s3_v2(csv_file):
    try:
        df = pd.read_csv(csv_file)
        columns_to_select = ["recordid", "call_direction", "callingnumber", "callednumber", 
                             "starttime", "usertimezone", "answerindicator", "releasetime", 
                             "callcategory", "userid", "codec_usage"]

        selected_columns_df = df[columns_to_select]
        columns_to_convert = ["callingnumber", "callednumber","starttime", "releasetime"]
        selected_columns_df[columns_to_convert] = selected_columns_df[columns_to_convert].apply(pd.to_numeric, errors='coerce').fillna(0)
        selected_columns_df[columns_to_convert] = selected_columns_df[columns_to_convert].astype(int)
        return selected_columns_df
    except Exception as e:
        print(f"Error reading data from CSV: {e}")
        return None
    


def read_data_from_s3(csv_file):
    try:
        # Read the first row to check for header information
        df = pd.read_csv(csv_file, nrows=0)  # Read without data, only headers

        # If columns contain the expected header names, go to the second condition
        expected_headers = ["recordid", "call_direction", "callingnumber", "callednumber", 
                            "starttime", "usertimezone", "answerindicator", "releasetime", 
                            "callcategory", "userid", "codec_usage"]

        if all(header in df.columns for header in expected_headers):
            print("in 2nd condition")
            return read_data_from_s3_v2(csv_file)
        else:
            print("in 1st condition")
            return read_data_from_s3_v1(csv_file)
    except Exception as e:
        print(f"Error determining the CSV file format: {e}")
        return None


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
    
    TABLE_NAME = "nextiva_data_csv_table"
    
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
    
    
    # S3 bucket parameters
    # source_bucket = "jsjd-nextiva-data"
    # source_key = "input/947389_604_cdr_1717514451001.csv"

    base_tmp_path = "/tmp/"
    for record in event["Records"]:
        
        source_bucket = record["s3"]["bucket"]["name"]
        # source_key = record["s3"]["object"]["key"]
        source_key = unquote_plus(record['s3']['object']['key'])
        filename = Path(source_key).name
        local_file_path = f'{base_tmp_path}{filename}'
        
        # extract csv_time hour
        timestamp=extract_time_from_filename(filename)

        # Connect to S3 and download the file
        s3 = boto3.client('s3')
        try:
            s3.download_file(source_bucket, source_key, local_file_path)
            logging.info(f'Downloaded file: {source_key} locally at path: {local_file_path}')
        except Exception as e:
            logging.error(f"Error downloading file from S3: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to download file from S3')
            }
    
        # Read the CSV file
        try:
            # df = pd.read_csv(local_file_path)
            df_nextiva = read_data_from_s3(local_file_path)
            logging.info(f'DataFrame shape: {df_nextiva.shape}')
            # Convert the 'start_time' and 'end_time' columns to datetime format
            # df_nextiva['starttime'] = pd.to_datetime(df_nextiva['starttime'], format='%Y%m%d%H%M%S')
            # df_nextiva['releasetime'] = pd.to_datetime(df_nextiva['releasetime'], format='%Y%m%d%H%M%S')
            
            
            df_nextiva['data_end_hour'] = timestamp
            df_nextiva['created_at'] = datetime.utcnow()
            df_nextiva['updated_at'] = datetime.utcnow()
            # Calculate the difference between the two columns and store it in a new column
            # df_nextiva['call_duration'] = df_nextiva['releasetime'] - df_nextiva['starttime']
            logging.info(f'timestamp added: {df_nextiva.shape}')
            
        except Exception as e:
            logging.error(f"Error reading CSV file: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to read CSV file')
            }
    
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
    
        # Insert DataFrame into the database
        try:
            df_nextiva.to_sql(TABLE_NAME, con=engine, if_exists='append', index=False)
            logging.info(f"Data successfully inserted into table: {TABLE_NAME}")
        except Exception as e:
            logging.error(f"Error inserting data into the database: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps('Failed to insert data into the database')
            }
    
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully inserted data into the database')
    }
