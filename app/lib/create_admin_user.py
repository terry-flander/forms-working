'''
run this program to create new admin user or change admin user password

python3 create_admin_user.py user password

'''
import requests
import os
import json
import shutil
import sys

def get_args():
    FORMIO_URL = os.environ.get('FORMIO_URL')

    args = { \
            "local_host": "http://3.25.74.169:3001",
            "admin_user": "remote_access@example.com",
            "admin_password": "remote_password"
        }

    args_local = { \
            "local_host": "http://" + FORMIO_URL,
            "admin_user": "admin@example.com",
            "admin_password": "CHANGEME"
        }

    return args

def get_token(host, admin_user, admin_password):
    url = f'{host}/user/login'
    payload = {
        'data': {
            'email': admin_user,
            'password': admin_password
            }
        }

    token = ''
    try:
        r = requests.post(url, json=payload)
        token = r.headers['x-jwt-token']
    except Exception as ex:
        print({ex})
    return token

def update_submission(host, token, data):
    submission_id = get_submission_id(host, token)
    url = f'{host}/admin/submission'
    r = {}
    try:
        if submission_id == None:
            r = requests.post(url, json=data, headers={"x-jwt-token": token})
        else:
            r = requests.put(f'{url}/{submission_id}', json=data, headers={"x-jwt-token": token})
    except Exception as ex:
        print(f'{ex} {r}')
    return submission_id

def get_submission_id(host, token):
    result = None
    index_field = None
    key_value = "email"
    try:
        if index_field != None:
            url = f'{host}/admin/exists?data.{index_field}={key_value}'
            r = requests.get(url, headers={"x-jwt-token": token})
            if r.text != 'Not found':
                result = r.json()['_id']
    except Exception as ex:
        print(f'look error: {ex}')

    return result

args = get_args()
local_host  = args['local_host']
local_token = get_token(local_host, args['admin_user'], args['admin_password'])

'''
Check for command line arguments as user and password
'''
if len(sys.argv) == 3:
    email = sys.argv[1]
    password = sys.argv[2]
    data = {"data": {
        "email": email,
        "password": password
    }}
    update_submission(local_host, local_token, data)

    print('** Done')
else:
    print ('usage:  python3 ./app/lib/create_admin_user.py user password')
