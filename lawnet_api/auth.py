import os
from getpass import getpass
from dotenv import load_dotenv
import requests
import base64
import json

load_dotenv()

def auth():
    client_id = os.getenv('LN_CLIENT_ID')
    client_secret = os.getenv('LN_CLIENT_SECRET')

    if not client_id:
        client_id = getpass('Enter client_id: ')    
    if not client_secret:
        client_secret = getpass('Enter client_secret: ')    

    authorisation = client_id + ':' + client_secret
    authorisation = 'Basic ' + base64.b64encode(authorisation.encode('utf-8')).decode('utf-8')

    headers = {
        'Authorization': authorisation,
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type':'client_credentials',
        'client_id':client_id,
        'client_secret':client_secret
    }

    url = 'https://api.sal.sg/uat-legalresearch/oauth/token'

    response = requests.post(url, headers=headers, data=data, timeout=30)
    response.raise_for_status()

    return response
