'''
run this program to initialize (re-initialise) local host forms and required submissions

python3 clone_data.py

'''
import requests
import os

def get_args():
    FORMIO_URL = os.environ.get('FORMIO_URL')

    args = { \
            "clone_form_tag": 'clone-form',
            "clone_submissions_tag": 'clone-submissions',
            "local_host": "http://" + FORMIO_URL,
            "repo_host": "http://54.79.191.17:3001",
            "admin_user": "admin@example.com",
            "admin_password": "CHANGEME",
            "local_user": "local@example.com",
            "local_password": "P@ssword1"
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

def update_form(path, host, token, data):
    try:
        if check_form(path, host, token) == None:
            url = f'{host}/form'
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

def update_submission(path, data, host, token):
    submission_id = get_submission_id(path, host, token)
    url = f'{host}/{path}/submission'
    try:
        if submission_id == None:
            r = requests.post(url, json=data, headers={"x-jwt-token": token})
        else:
            r = requests.put(f'{url}/{submission_id}', json=data, headers={"x-jwt-token": token})
    except Exception as ex:
        print(ex)
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

def get_forms_by_tags(tags, host, token):
    result = []
    url = f'{host}/form?tags={tags}&sort=path&&limit=9999'
    r = requests.get(url, headers={"x-jwt-token": token})
    for f in r.json():
        result.append(f)
    return result

def get_submissions_for_path(path, host, token):
    result = []
    url = f'{host}/{path}/submission?limit=9999'
    r = requests.get(url, headers={"x-jwt-token": token})
    for l in r.json():
        if bool(l['data']):
            l['data']['path'] = path
            result.append(l)
    return result

'''
Do the clone process:
1. get arguments from config file
2. get repo_host forms by tag
3. for each form create or update in local_host
4. get list of forms where all submissions are to be cloned
5. for each form, get all submissions for form
6. for each submission create or update in local_host
7. create user with full access
8. done
'''

args = get_args()
repo_host = args['repo_host']
local_host  = args['local_host']
repo_token = get_token(repo_host, args['admin_user'], args['admin_password'])
local_token = get_token(local_host, args['admin_user'], args['admin_password'])

print(f'** Get Forms and Submissions from {args["repo_host"]} to {args["local_host"]}')
forms_to_pull = get_forms_by_tags(args['clone_form_tag'], repo_host, repo_token)
for form in forms_to_pull:
    path = form['path']
    print(path)
    update_form(path, local_host, local_token , form)

print('** Get submissions')
submissions_to_pull = get_forms_by_tags(args['clone_submissions_tag'], repo_host, repo_token)
for form in submissions_to_pull:
    path = form['path']
    print(path, end='')
    submissions_to_pull = get_submissions_for_path(path, repo_host, repo_token)
    for submission in submissions_to_pull:
        print('.', end='')
        update_submission(path, submission, local_host, local_token)
    print()
print(f'** Create local user with Admin - user: {args["local_user"]} password: {args["local_password"]}')
data = {"data": {
        "accessGroups": [
        "allForms", 
        "allowDelete", 
        "allowCopy", 
        "admin"
        ],
        "accessRoles": [
            "ADMIN"
        ],
        "email": args["local_user"],
        "password": args["local_password"]
    }}
update_submission('user', data, local_host, local_token)
print('** Done')
