''' Routines giving access to form.io APIs '''
from distutils.log import debug
import logging
import json
import requests
import os
import html
import unicodedata

from pathlib import Path
import subprocess
from subprocess import check_output
from datetime import datetime

from app.lib.util import setup_logger, build_error
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

'''
Shared Static Names for parts of the application
'''
FORMIO_URL = os.environ.get('FORMIO_URL')

ADMIN_USER = os.environ.get('ADMIN_USER')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

def get_new_login(userName, password):
  url = f'http://{FORMIO_URL}/user/login'
  payload = {'data': {'email': userName,'password': password}}
  r = requests.post(url, json=payload)
  try:
    token = r.headers['x-jwt-token']
    data = get_submission('user',userName)
    groups = ''
    access_object = ''
    if 'accessGroups' in data['data']:
      groups = data['data']['accessGroups']
    if 'accessRoles' in data['data']:
      access_object = build_access_object(data)
    app_logger.info(f'User: {userName} - Login Successful')
    return token, groups, access_object
  except Exception as ex:
    app_logger.warn(f'{userName} - Invalid Login Attempt {ex}')
    return None

def build_access_object(data):
    result = {
        "ro_form_list": [],
        "full_form_list": [],
        "ro_company_list": [],
        "full_company_list": [],
        "ro_view_list": [],
        "full_view_list": []

    }
    try:
        for r in data['data']['accessRoles']:
            role = get_submission('access-roles', r)
            debug_logger.debug(role)
            result['ro_form_list'].extend(role['data']['form_read_only_access'])
            result['full_form_list'].extend(role['data']['form_full_access'])
            result['ro_company_list'].extend(role['data']['company_read_only_access'])
            result['full_company_list'].extend(role['data']['company_full_access'])
            result['ro_view_list'].extend(role['data']['view_read_only_access'])
            result['full_view_list'].extend(role['data']['view_full_access'])

    except Exception as ex:
        app_logger.warn(f'Unable to build Access Matrix {ex}')

    return result

def get_access_list(access_object=None, type='form', mode='read'):
    result = []
    if access_object != None:
        try:
            if type == 'form':
                if mode == 'read':
                    result = access_object['full_form_list'] + access_object['ro_form_list']
                elif mode == 'full':
                    result = access_object['full_form_list']
            elif type == 'company':
                if mode == 'read':
                    return access_object['full_company_list'] + access_object['ro_company_list']
                elif mode == 'full':
                    return access_object['full_company_list']
            elif type == 'view':
                if mode == 'read':
                    return access_object['full_view_list'] + access_object['ro_view_list']
                elif mode == 'full':
                    return access_object['full_view_list']
        except:
            result = []
    return result

def get_formio_login():
    token = None
    if token == None:
        url = f'http://{FORMIO_URL}/user/login'
        payload = {'data': {'email': ADMIN_USER, 'password': ADMIN_PASSWORD}}
        token = ''
        try:
            r = requests.post(url, json=payload)
            token = r.headers['x-jwt-token']
        except Exception as ex:
            app_logger.error(ex)
    return token

def update_submission(data, path, keyvalue, user_token, company_access=None):
    if company_access != None and not check_company(data, company_access):
        return 'error', build_error(keyvalue, 'You do not have permission to update this submission')

    index_field = get_form_keyfield(path)
    token = get_formio_login()
    submission_id = get_submission_id(path, index_field, keyvalue)
    bi = None
    try:
        if submission_id != 'new':
            bi = get_submission(path, keyvalue)
            debug_logger.debug(f'update {path} {keyvalue}')
            url = f'http://{FORMIO_URL}/{path}/submission/{submission_id}'
            r = requests.put(url, json=data, headers={"x-jwt-token": token})
            action = 'update'
        else:
            debug_logger.debug(f'new {path}')
            url = f'http://{FORMIO_URL}/{path}/submission'
            r = requests.post(url, json=data, headers={"x-jwt-token": token})
            action = 'new'
        debug_logger.debug(r.status_code)
        if not r.status_code in [200, 201]:
            debug_logger.debug(r.json())
        logEvent(bi, r, path, action, "auto-log", user_token)
        return 'ok', r.json()

    except Exception as ex:
        debug_logger.debug(f'Update Failed: {ex}')
        return 'error', ex

def patch_submission(data, keyvalue, user_token, paths=None):
    newDoc = json.loads(data[0])
    patchDoc = json.loads(data[1])
    token = get_formio_login()
    if paths == None:
        paths = f''
    for path in paths.split(","):
        index_field = get_form_keyfield(path)
        submission_id = get_submission_id(path, index_field, keyvalue)
        bi = None
        if submission_id != 'new':
            bi = get_submission(path, keyvalue)
            url = f'http://{FORMIO_URL}/{path}/submission/{submission_id}'
            debug_logger.debug(f'patching {url}')
            r = requests.patch(url, json=patchDoc, headers={"x-jwt-token": token})
            if 'name' in r.json():
                debug_logger.debug(r.json()['name'])
            else:
                debug_logger.debug('--success')
            action = 'update'
        else:
            debug_logger.debug(f'new {path}')
            url = f'http://{FORMIO_URL}/{path}/submission'
            r = requests.post(url, json=newDoc, headers={"x-jwt-token": token})
            action = 'new'
            logEvent(bi, r, path, action, "auto-log", user_token)
    return r.json()

def patch_one(path, data, keyvalue):
    debug_logger.debug(f'{path} {keyvalue}')
    patchDoc = json.loads(data)
    try:
        index_field = get_form_keyfield(path)
        token = get_formio_login()
        submission_id = get_submission_id(path, index_field, keyvalue)
        url = f'http://{FORMIO_URL}/{path}/submission/{submission_id}'
        debug_logger.debug(f'patching {url}')
        r = requests.patch(url, json=patchDoc, headers={"x-jwt-token": token})
        if 'name' in r.json():
            debug_logger.debug(r.json()['name'])
        else:
            debug_logger.debug('--success')
        return r.json()
    except Exception as ex:
        app_logger.error(ex)
        return None

def rename_reference(keyfield, id, new_id, user_token):
    result = 'ok'
    '''
    * TODO : Rewrite this to take input list of forms from workflow?
    for path in [<path-list>]:
        if get_submission_id(path, keyfield, new_id) != 'new':
            return f'Reference {new_id} already exists'
        from_submission = get_submission(path, id)
        if from_submission != '':
            new_submission = update_copy(from_submission, keyfield, new_id)
            update_reference = update_submission(new_submission, path, keyfield, new_id, user_token)
            new_reference = update_reference[1]
            if check_reference(new_reference['data'], keyfield, new_id) == None:
                app_logger.warn(f'{new_id} not in {new_reference["data"]}')
                return new_reference
    
    # Copy existing to new all worked. Delete original submissions.
    if result == 'ok':
        for path in [<path-list>]:
            delete_submission(path, keyfield, id)
    '''
    return result

def update_copy(ref, keyfield, new_id):
    ref['data'][keyfield] = new_id
    if 'id2' in ref['data']:
      ref['data']['id2'] = new_id
    return ref

def check_reference(data, keyfield, new_id):
    try:
        return data[keyfield] == new_id
    except:
        return None

def delete_submission(path, keyvalue):
    result = ''
    try:
        index_field = get_form_keyfield(path)
        token = get_formio_login()
        submission_id = get_submission_id(path, index_field, keyvalue)
        if submission_id != 'new':
            debug_logger.debug(f'{path}, {keyvalue}')
            url = f'http://{FORMIO_URL}/{path}/submission/{submission_id}'
            r = requests.delete(url, headers={"x-jwt-token": token})
            result = "Delete successful"
        else:
            result = "Submission not found"
    except Exception as ex:
        result = f'Error: {ex}'

    app_logger.info(result)
    return result

# Validate submission before add/update
def validate_submission(data, path):
    token = get_formio_login()
    debug_logger.debug(path)
    url = f'http://{FORMIO_URL}/{path}/validate'
    r = requests.post(url, json=data, headers={"x-jwt-token": token})
    if r.status_code == 200:
        return 'ok'
    else:
        debug_logger.debug(r.text)
        return r.text

def create_submission(path, keyvalue):
    index_field = get_form_keyfield(path)
    debug_logger.debug(f'{path}, {index_field}={keyvalue}')
    token = get_formio_login()
    submission_id = get_submission_id(path, index_field, keyvalue)
    if submission_id == 'new':
        debug_logger.debug(f'new {path} / {index_field} = {keyvalue}')
        data = {
            "data": {
                index_field: keyvalue
            }
        }
        url = f'http://{FORMIO_URL}/{path}/submission'
        r = requests.post(url, json=data,  headers={"x-jwt-token": token})
        return r.json()
    else:
        debug_logger.debug(f'path {path} index_field: {index_field} keyvalue: {keyvalue} id: not found')
        return ''
    
# Use form path to determine field to match
def get_submission(path, keyvalue):
    index_field = get_form_keyfield(path)
    debug_logger.debug(f'{path}, {index_field}={keyvalue}')
    token = get_formio_login()
    submission_id = get_submission_id(path, index_field, keyvalue)
    if submission_id != 'new':
        url = f'http://{FORMIO_URL}/{path}/submission/{submission_id}'
        r = requests.get(url, headers={"x-jwt-token": token})
        return r.json()
    else:
        debug_logger.debug(f'path {path} index_field: {index_field} keyvalue: {keyvalue} id: not found')
        return ''

def get_submission_id(path, index_field, keyvalue):
    debug_logger.debug(f'{path} {index_field} "{keyvalue}"')
    token = get_formio_login()
    url = f'http://{FORMIO_URL}/{path}/exists?data.{index_field}={keyvalue}'
    this_id = 'new'
    r = requests.get(url, headers={"x-jwt-token": token})
    if r.text != 'Not found':
        this_id = r.json()['_id']
    return this_id

# Get Form by Form Path
def get_form(path):
    debug_logger.debug(path)
    # Use form path to determine field to match
    try:
        token = get_formio_login()
        url = f'http://{FORMIO_URL}/{path}'
        r = requests.get(url, headers={"x-jwt-token": token})
        return r.json()
    except Exception as ex:
        app_logger.error(ex)
        return None

# Get Form keyfield
def get_form_keyfield(path):
    debug_logger.debug(path)
    result = 'id'
    # Use form path to determine field to match
    try:
        token = get_formio_login()
        url = f'http://{FORMIO_URL}/app-forms/submission?data.id={path}&select=data.keyfield'
        r = requests.get(url, headers={"x-jwt-token": token})
        result = r.json()[0]['data']['keyfield']
    except Exception as ex:
        app_logger.error(ex)
        result = None
    return result

# Get Forms by tags
def get_forms_by_tags(tags):
    debug_logger.debug(tags)
    # Use form path to determine field to match
    token = get_formio_login()
    result = []
    url = f'http://{FORMIO_URL}/form?tags={tags}&select=path,tags'
    r = requests.get(url, headers={"x-jwt-token": token})
    for f in r.json():
        result.append(f)
    return result

# Get Submissions for tagged forms
def get_submissions(tags, access_object=None):
    token = get_formio_login()
    found = []
    paths = get_forms_by_tags(tags)
    company_access = get_access_list(access_object, 'company', 'read')
    form_access = get_access_list(access_object, 'form', 'read')
    for form in paths:
        path = form['path']
        if check_form(path, form_access):
            tags = form['tags']
            debug_logger.debug(f'{path} {tags}')
            url = f'http://{FORMIO_URL}/{path}/submission?limit=9999&sort=data.structure_id'
            r = requests.get(url, headers={"x-jwt-token": token})
            for l in r.json():
                if bool(l['data']) and check_company(l['data'], company_access):
                    l['data']['path'] = path
                    l['data']['tags'] = tags
                    found.append(l["data"])
    return found

# Set Jinja values for View HTML
def get_view_layout(view_id):
    result = ''
    try:
        result = get_submission('view', view_id)
        debug_logger.debug(f'browse_id: {view_id}')
    except Exception as ex:
        app_logger.error(ex)

    return result

# Set Jinja values for Menu
def get_menu_layout(menu_id):
    result = ''
    try:
        result = get_submission('menus', menu_id)
        debug_logger.debug(f'_id: {menu_id}')
    except Exception as ex:
        app_logger.error(ex)

    return result

# Get Submissions for form with paging
def get_submissions_paged(path, start, page_length, fields='', formats='', sorts='', access_object=None):
    token = get_formio_login()
    result = []
    company_access = get_access_list(access_object, 'company', 'read')
    form_access = get_access_list(access_object, 'form', 'read')
    skip =  start
    field_list = fields.split(",")
    format_list = formats.split(',')
    sort_list = sorts.split(',')
    data_fields = ''
    sort_fields = ''
    data_values = ''
    data_value = ''
    load = ''
    for c in range(0, len(field_list)):
        if c > 0:
            data_fields += ','
        data_fields += 'data.' + field_list[c]
        if sort_list[c] != 'none':
            if sort_fields != '':
                sort_fields += ','
            if sort_list[c] == 'desc':
                sort_fields += '-'
            sort_fields += 'data.' + field_list[c]

    try:
        url = f'http://{FORMIO_URL}/{path}/submission?select={data_fields}&skip={skip}&limit={page_length}&sort={sort_fields}'
        debug_logger.debug(f'skip {skip} limit {page_length} fields: {field_list} formats: {format_list}')
        r = requests.get(url, headers={"x-jwt-token": token})
        for l in r.json():
            data_values = ''
            for c in range(0, len(field_list)):
                if c > 0:
                    data_values += ','
                data_value = f'"{field_list[c].replace(".","_")}" : "{get_value(l, field_list[c], format_list[c])}"'
                data_values += data_value
            load = "{" + data_values + "}"
            result.append(json.loads(load))
    except Exception as ex:
        app_logger.error(f'values {data_values} \n Error: {ex} \n {data_value} \n {load}')

    return result

# Count Submissions for form with paging
def get_paged_count(path):
    token = get_formio_login()
    result = 0
    try:
        url = f'http://{FORMIO_URL}/{path}/submission?select=_id&limit=9999'
        r = requests.get(url, headers={"x-jwt-token": token})
        for l in r.json():
            result += 1
    except Exception as ex:
        result = 0

    debug_logger.debug(f' {path} count: {result}')

    return result

def get_value(data, field, format):
    result = ''
    try:
        result = get_v(data['data'], field)
        if field == 'promoteDateTime':
            result = result[0:19].replace('T',' ')
        elif field in ['logComment', 'logFirstChange']:
            result = html.escape(remove_control_characters(result)).replace('\\&', "&")
        elif field in ['description']:
            result = result.split("\n")[0]
    except:
        result = ''
    return result

def get_v(data, field):
    result = ''
    d = data
    for f in field.split('.'):
        app_logger.info(f'field {f} data {d} result {result}')
        result = d[f]
        d = result
    return result

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def check_company(data, access):
    result = True # Allow any without company ID -- for now
    try:
        if 'asset_owner' in data:
            debug_logger.debug(f'asset_owner: {data["asset_owner"]} access: {access}')
            result = data['asset_owner'] in access
    except Exception as ex:
        app_logger.error(f'Error: {ex} with data: {data} access: {access}')
        result = False
    return result

def check_form(path, access):
    result = False
    try:
        if '*' in access:
            result = True
        else:
            result = path in access
    except Exception as ex:
        app_logger.error(f'Error: {ex} with path: {path} access: {access}')
    return result

def check_view(view, access):
    result = False
    try:
        if '*' in access:
            result = True
        else:
            result = view in access
    except Exception as ex:
        app_logger.error(f'Error: {ex} with view: {view} access: {access}')
    return result

# Get Reference Submissions for path
def get_reference_submissions(path, submission_args):
    token = get_formio_login()
    debug_logger.debug(path)
    if path == 'user':
        url = f'http://{FORMIO_URL}/{path}/submission?select=data.email,data.accessGroups&limit=9999'
        debug_logger.debug(f'user: {url}')
    elif submission_args != None:
        url = f'http://{FORMIO_URL}/{path}/submission{submission_args}'
        debug_logger.debug(f'reference: {url}')
    else:
        url = f'http://{FORMIO_URL}/{path}/submission?select=data.id,data.description,data.name&limit=9999'
        debug_logger.debug(f'all: {url}')
    r = requests.get(url, headers={"x-jwt-token": token})

    if submission_args == None:
        return build_list(path, r)
    else:
        return json.dumps(r.json())

def build_list(path, r):
    found = []
    # Add new first
    found.append({"path": path, "id": "** New **", "description": "Add"})
    for l in r.json():
        if bool(l['data']):
            if path == 'user':
                res_id = l["data"]['email']
                desc = ''
                if 'accessGroups' in l["data"]:
                    for a in l["data"]['accessGroups']:
                        if desc != '':
                            desc += ','
                        desc += a
                else:
                    desc = 'No Groups'
            else:
                res_id = l["data"]['id']
                desc = get_reference_description(l)
            found.append({"path": path, "id": res_id, "description": desc})
    return found

def get_user_email(token):
    data = get_user(token)
    if data != None:
        result = data['data']["email"]
    else:
        result = 'webhook'
    return result

def get_reference_description(l):
    if 'description' in l['data']:
        return l['data']['description']
    elif 'name' in l['data']:
        return l['data']['name']
    else:
        return 'unknown'


def get_user(token):
    result = None
    try:
        if token != 'webhook':
            url = f'http://{FORMIO_URL}/current'
            res = requests.get(url, headers={"x-jwt-token": token})
            result = res.json()
    except Exception as ex:
        app_logger.warn(f'token error: {result}')
    return result

def logEvent(bi, res, path, action, comment, token):
    # Assemble data for log
    data = res.json()
    logFormVersion = 0
    logUser = 'unknown'
    logDateTime = '?'
    keyfield = get_form_keyfield(path)
    try:
        id = data['data'][keyfield]
        logFormVersion = data['data']['_version']
        logUser = get_user_email(token)
        logDateTime = data['modified']
    except Exception as ex:
        return ''

    changes = get_changes(bi, data)
    eventData = \
        {
            "data": {
                "id": id, 
                "logFormVersion": logFormVersion,
                "form_name": path,
                "logDateTime": logDateTime,
                "logUser": logUser,
                "logAction": action,
                "logComment": changes
            }
        }
    try:
        admin_token = get_formio_login()
        url = f'http://{FORMIO_URL}/change-log/submission'
        debug_logger.debug(f'{url}')
        r = requests.post(url, json=eventData, headers={"x-jwt-token": admin_token})
        return r.json()
    except Exception as ex:
        debug_logger.error(ex)
        return None

def get_changes(bi, ai):
    diff = ''
    
    Path(f'./tmp').mkdir(parents=True, exist_ok=True)
    try:
        if bi != None:
            t = open('./tmp/bi.json', 'w')
            t.write(json.dumps(bi['data'], indent=4))
            t.close()
            t = open('./tmp/ai.json', 'w')
            t.write(json.dumps(ai['data'], indent=4))
            t.close()
            diff = get_diff()
        else:
            debug_logger.debug(f'missing bi[data]')
            
    except Exception as ex:
        app_logger.error(ex)
    
    return diff

def get_diff():
    output = ""
    command="diff -yiwB --suppress-common-lines ./tmp/bi.json ./tmp/ai.json"
    try:
        debug_logger.debug(f'diff')
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        encoding = 'utf-8'
        output = out.decode(encoding).replace("\n","<br>").replace("\"", "'")
    except Exception as ex:
        app_logger.error(ex)

    return output    

def load_change_log(path, id):
    debug_logger.debug(f'{path} {id}')
    token = get_formio_login()
    found = []
    url = f'http://{FORMIO_URL}/{path}/submission?data.id={id}&limit=999&sort=-data.logDateTime'
    r = requests.get(url, headers={"x-jwt-token": token})
    for l in r.json():
        if bool(l['data']):
            found.append( 
            {
                "path": path, 
                "id": id, 
                "logFormVersion": getLogValue(l,'logFormVersion','')[0],
                "form_name": getLogValue(l, 'form_name', '')[0],
                "logDateTime": getLogValue(l, 'logDateTime', '')[0],
                "logAction": getLogValue(l, 'logAction', '')[0],
                "logComment": getLogValue(l, 'logComment', '')[0],
                "logUser": getLogValue(l, 'logUser', '')[0],
                "logFirstChange": getLogValue(l, 'logComment', '')[1]
                }
            )
    return found

def getLogValue(l, fieldName, dflt):
    result = ''
    firstChange = ''
    try:
        result = l['data'][fieldName]
    except Exception:
        result = dflt

    if fieldName == 'logDateTime':
        result = result[0:19].replace('T',' ')
    elif fieldName == 'logComment':
        newresult = ''
        firstChange = ''
        for l in result.split("<br"):
            c = l.replace('>','').split('|')
            newresult += '<tr><td>'
            if len(c) == 2:
              newresult += c[0].strip() + '</td><td>' + c[1].strip()
              if firstChange == '':
                  firstChange = c[1].strip()
            else:
              newresult += '</td><td>' + c[0].strip()
              if firstChange == '':
                  firstChange = c[0].strip()
            newresult += '</td></tr>'
        result = newresult
    return result, firstChange

def load_promote_log():
    token = get_formio_login()
    found = []
    url = f'http://{FORMIO_URL}/form-promote/submission?limit=999&sort=-data.promoteDateTime'
    r = requests.get(url, headers={"x-jwt-token": token})
    for l in r.json():
        if bool(l['data']):
            found.append(
            {
                "path": getValue(l, 'path', ''),
                "promoteDateTime": getValue(l, 'promoteDateTime', ''),
                "promoteUser": getValue(l, 'promoteUser', ''),
                "version": getValue(l,'version',''),
                "promote_from_host": getValue(l,'promote_from_host',''),
                "promote_to_host": getValue(l,'promote_to_host',''),
                "description": getValue(l, 'description', ''),
                "promote_type": getValue(l, 'promote_type', ''),
                "key_value": getValue(l, 'key_value', '')
            })
    return found

def log_promote(data):
    # Assemble data for log
    result = ''
    try:
        promoteData = \
            {
                "data": {
                    "path": data['path'],
                    "promoteDateTime": getCurrentDate(),
                    "promoteUser": data['promoteUser'],
                    "version": data['version'],
                    "promote_from_host": data['promote_from_host'],
                    "promote_to_host": data['promote_to_host'],
                    "description": data['description'],
                    "promote_type": data['promote_type'],
                    "key_value": data['key_value'] if "key_value" in data else ""
                }
            }
    except Exception as ex:
        app_logger.error(ex)
        result = ex

    try:
        token = get_formio_login()
        url = f'http://{FORMIO_URL}/form-promote/submission'
        r = requests.post(url, json=promoteData, headers={"x-jwt-token": token})
        result = r.json()

    except Exception as ex:
        app_logger.error(ex)
        result = ex

    finally:
        return result

def getValue(l, fieldName, dflt):
    result = ''
    try:
        result = l['data'][fieldName]
        if result and fieldName == 'promoteDateTime':
            result = result[0:19].replace('T',' ')
        elif result and fieldName == 'description':
            result = result.replace("\n", "<br/>").replace(" ", "&nbsp;")
    except Exception:
        result = dflt

    return result

def getCurrentDate():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")
