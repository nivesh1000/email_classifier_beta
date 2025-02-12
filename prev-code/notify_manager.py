
import boto3
# import os
# import pymysql
# import logging
from urllib.request import Request, urlopen
import urllib3

# def lambda_handler(event, context):
#     api_url = "https://dashboard.jsjdmedia.com/sent-close-emails"
#     response = urlopen(api_url)
#     # api_output = response.json()
#     print(response)
#     print("Notifiation emials sent to ")


def lambda_handler(event, context):
    api_url = "https://dashboard.jsjdmedia.com/sent-close-emails"
    http = urllib3.PoolManager()
    response = http.request('GET',api_url)
    print(response)
    print("Notifiation emials sent to ")    
