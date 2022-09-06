'''
run this program to export all forms and data into directory structure and zip

python3 backup_data.py

'''
import requests
import os
from pathlib import Path
import json
import shutil
from datetime import datetime
import sys

def get_args():
    FORMIO_URL = os.environ.get('FORMIO_URL')
    args = { \
            "local_host": "http://" + FORMIO_URL,
            "admin_user": "admin@example.com",
            "admin_password": "CHANGEME",
            "backup_dir": "backups",
            "skip_paths": ["admin"]
        }
    return args

def update_config(dir, mode):
    full_file = f'{dir}/version.conf'
    result = ''
    if mode == 'incremental':
        if os.path.exists(full_file):
            t = open(full_file, 'r')
            last_incremental = t.read()
            result = f'&modified__gt={last_incremental}'
            t.close()

        # Save with current date/time
        current = datetime.utcnow().strftime("%Y-%m-%dT%H:%M")
        t = open(full_file, 'w')
        t.write(current)
        t.close()
    else:
        result = ''
    print(f'Cutoff Date: {result}')
    return result

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

def get_forms(host, token, skip_paths, cutoff_date):
    result = []
    url = f'{host}/form?sort=path&&limit=9999{cutoff_date}'
    r = requests.get(url, headers={"x-jwt-token": token})
    for f in r.json():
        if not f['path'] in skip_paths:
            result.append(f)
    return result

def get_submissions_for_path(path, host, token, cutoff_date):
    result = []
    url = f'{host}/{path}/submission?limit=9999{cutoff_date}'
    r = requests.get(url, headers={"x-jwt-token": token})
    for l in r.json():
        if bool(l['data']):
            l['data']['path'] = path
            result.append(l)
    return result

def get_file_name(dir, path, file_name, ext):
    try:
        create_directory(dir, path)
        return f'{dir}/tmp/{path}/{file_name}.{ext}'
    except Exception as ex:
        return None

def create_directory(dir, path):
    try:
        Path(f'{dir}/tmp/{path}').mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        return None

def save_data(dir, path, file_name, ext, data):
    result = 'ok'
    if data != None:
        try:
            fileName = get_file_name(dir, path, file_name, ext)
            t = open(fileName, 'w')
            json.dump(data, t)
            t.close()

        except Exception as ex:
            result = f'Unable to save Document as {fileName}'

    return result

'''
Do the backup process:
1. get all forms list
2. for each form save to {args.backup_dir}/tmp/forms
3. get all submissions for form and save to {args.backup_dir}/tmp/submissions/{path}
4. zip {args.backup_dir}/tmp to {args.backup_dir}/backup_{today}.zip
5. rm -r {args.backup_dir}/tmp
6. done
'''

args = get_args()
local_host  = args['local_host']
local_token = get_token(local_host, args['admin_user'], args['admin_password'])
backup_dir = args['backup_dir']
timestamp = f'{datetime.today().strftime("%Y%m%d_%H%M")}'

script_args = sys.argv[1:]
mode = script_args[0]

print(f'** {mode} backup forms and submissions from {local_host}')
cutoff_date = update_config(backup_dir, mode)

backup_started = False
forms_to_pull = get_forms(local_host, local_token, args['skip_paths'], cutoff_date)
print('Backup forms...')
for form in forms_to_pull:
    backup_started = True
    path = form['path']
    if path == 'admin':
        next
    print(path)
    save_data(backup_dir, 'forms', path, 'json', form)

print('Backup submissions...')
submissions_to_pull = get_forms(local_host, local_token, args['skip_paths'], '')
for form in submissions_to_pull:
    path = form['path']
    if path == 'admin':
        next

    submissions_to_pull = get_submissions_for_path(path, local_host, local_token, cutoff_date)
    if len(submissions_to_pull) > 0:
        print(path, end='')
        backup_started = True
        for submission in submissions_to_pull:
            print('.', end='')
            index_field = submission['_id']
            save_data(backup_dir, path, index_field, 'json', submission)
        print()

if backup_started:
    output_filename = f'{backup_dir}/{mode}_{timestamp}'
    shutil.make_archive(output_filename, 'zip', f'{backup_dir}/tmp')
    shutil.rmtree(f'{backup_dir}/tmp')
else:
    print ("No changes for incremental backup")

print('** Done')
