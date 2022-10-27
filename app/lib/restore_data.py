'''
run this program to import all forms and data from directory structure

python3 restore_data.py

'''
import requests
import os
import json
import shutil
import sys

def get_args():
    FORMIO_URL = os.environ.get('FORMIO_URL')

    args = { \
            "local_host": "http://" + FORMIO_URL,
            "admin_user": "admin@example.com",
            "admin_password": "CHANGEME",
            "restore_dir": "tmp/restore"
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
        print(ex)
    return token

def update_form(path, host, token, data):
    try:
        if check_form(path, host, token) == None:
            url = f'{host}/form'
            del data['_id']
            r = requests.post(url, json=data, headers={"x-jwt-token": token})
        else:
            url = f'{host}/{path}'
            del data['_id']
            r = requests.put(url, json=data, headers={"x-jwt-token": token})
        return 'ok' # r.json()
    except Exception as ex:
        print(f'Exception: {ex}')
        return None

def check_form(path, host, token):
    result = None
    r = {}
    try:
        url = f'{host}/{path}'
        r = requests.get(url, headers={"x-jwt-token": token})
        if r.status_code == 200 and '_id' in r.json():
            result = path
        else:
            result = None
    except Exception as ex:
        print(f'check_form: {path} {ex} {r}')
    return result

def update_submission(path, host, token, data):
    submission_id = get_submission_id(path, host, token)
    url = f'{host}/{path}/submission'
    r = {}
    try:
        if submission_id == None:
            if path == 'user':
                url = url.replace('submission', 'register')
                data['data']['password'] = 'CHANGEME'
                r = requests.post(url, json=data, headers={"x-jwt-token": token})
            else:
                r = requests.post(url, json=data, headers={"x-jwt-token": token})
        else:
            r = requests.put(f'{url}/{submission_id}', json=data, headers={"x-jwt-token": token})
    except Exception as ex:
        print(f'{ex} {r}')
    return submission_id

def get_submission_id(path, host, token):
    result = None
    index_field = None
    key_value = get_form_keyfield(path, host, token)
    try:
        if index_field != None:
            url = f'{host}/{path}/exists?data.{index_field}={key_value}'
            r = requests.get(url, headers={"x-jwt-token": token})
            if r.text != 'Not found':
                result = r.json()['_id']
    except Exception as ex:
        print(f'look error: {ex}')

    return result

def get_form_keyfield(path, host, token):
    result = 'id'
    # Use form path to determine field to match
    try:
        url = f'http://{host}/app-forms/submission?data.id={path}&select=data.keyfield'
        r = requests.get(url, headers={"x-jwt-token": token})
        result = r.json()[0]['data']['keyfield']
    except Exception as ex:
        result = None
    return result

def get_data(dir, path):
    result = []
    files = next(os.walk(f'{dir}/{path}'), (None, None, []))[2]  # [] if no file
    for file in files:
        full_file = f'{dir}/{path}/{file}'
        if os.path.exists(full_file):
            try:
                t = open(f'{dir}/{path}/{file}', 'r')
                f = t.read()
                result.append(f)
            except Exception:
                print('x', end='')
    return result

'''
Do the Restore process:
1. get all forms from backup directory
2. for each form update_form
3. get all submissions for form and update submission
4. done
'''

args = get_args()
local_host  = args['local_host']
local_token = get_token(local_host, args['admin_user'], args['admin_password'])
restore_dir = args['restore_dir']

'''
Check for command line argument as a zip file
If there is one and it is a zip file, unzip and set restore_dir
'''
script_args = sys.argv[1:]
if len(script_args) > 0:
    shutil.unpack_archive(script_args[0], restore_dir, 'zip')

    print(f'** Get Forms from {restore_dir} to load into {local_host}')
    forms_to_load = get_data(restore_dir, 'forms')
    for form in forms_to_load:
        data = json.loads(form)
        path = data['path']
        if path == 'admin':
            next
        print(path, end='')

        update_form(path, local_host, local_token, data)

        submissions_to_load = get_data(restore_dir, path)
        for submission in submissions_to_load:
            print('.', end='')
            data = json.loads(submission)
            update_submission(path, local_host, local_token, data)
        print()

    shutil.rmtree(f'{restore_dir}')
    print('** Done')
else:
    print ('usage:  python3 ./app/lib/restore_data.py <backupFile>.zip ')
