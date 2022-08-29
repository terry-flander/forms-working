''' Routines to promote forms between hosts '''
import logging
from operator import index
import os
from jinja2 import Undefined
import requests
import sys
import os
import json
from os import walk

import app.lib.formio_api as formio
import app.lib.jinja_api as jinja

from app.lib.util import setup_logger
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

def do_promote(data):
    try:
        args = get_args(data)

        if args['promote_type'] == 'form':
            promote_form(data, args)
        elif args['promote_type'] == 'singleSubmission' or args['promote_type'] == 'allSubmissions':
            if args["to_form"] == None:
                return 'Form does not exist to Promote To Host'
            else:
                submissions = get_submissions_for_path(args)
                return promote_submissions(data, args, submissions)
        else:
            return 'Promote Type not recognised'

    except Exception as ex:
        app_logger.error(ex)

    finally:
        return "ok"

def get_args(data):
    try:
        path = get_val(data, 'path')
        from_host = get_val(data, 'promote_from_host')
        to_host = get_val(data, 'promote_to_host')
        promote_type = get_val(data, 'promote_type')
        index_field = get_val(data, 'index_field')
        key_value = get_val(data, 'key_value')
        update_version = get_val(data, 'update_version')

        from_data = get_hosts_data(from_host)
        to_data = get_hosts_data(to_host)

        from_token = get_token(from_data)
        to_token = get_token(to_data)

        from_form = get_form(path, from_data, from_token)
        to_form = get_form(path, to_data, to_token)

        from_id = from_form['_id']
        to_id = None
        if to_form != None:
            to_id = to_form['_id']

        args = { \
                "path": path,
                "from_host": from_host,
                "to_host": to_host,
                "promote_type": promote_type,
                "index_field": index_field,
                "key_value": key_value,
                "update_version": update_version,
                "from_data": from_data,
                "to_data": to_data,
                "from_token": from_token,
                "to_token": to_token,
                "from_form": from_form,
                "to_form": to_form,
                "from_id": from_id,
                "to_id": to_id
            }
        return args

    except Exception as ex:
        app_logger.error(ex)
        return "{}"

def promote_form(data, args):
    try:
        from_data = args["from_data"]
        to_data = args["to_data"]
        path = args["path"]
        from_token =args["from_token"]
        to_token =args["to_token"]
        from_form =args["from_form"]
        to_form =args["to_form"]
        from_id =args["from_id"]
        to_id =args["to_id"]
        update_version =args["update_version"]
        

        if to_form != None:
            debug_logger.debug(f'Update form: {to_id} from {from_id} to {to_id}')
        else:
            debug_logger.debug(f'New form from {from_id} to {to_id}')

        # change urls in form
        old_form = json.dumps(from_form)
        old_form = old_form.replace(get_val(from_data, 'url'), get_val(to_data, 'url'))

        # get version number to be promoted
        new_form = json.loads(old_form)

        _version = increment_version(get_form_version(new_form), update_version)
        new_form['_version'] = _version
        new_form['machineName'] = path + '.' + _version
        del new_form['_id']

        jinja.save_doc('form_versions', path, _version, 'json', json.dumps(new_form))

        # Update form with new version number in FROM
        update_form(path, from_data, from_token, new_form, from_id)

        # Update or create form in TO
        res = update_form(path, to_data, to_token, new_form, to_id)

        data['description'] += "\n" + json.dumps(res, sort_keys=True, indent=4)
        data['version'] = _version

        formio.log_promote(data)

    except Exception as ex:
        app_logger.error(ex)

    finally:
        return "ok"

def get_form_version(form):
    ver = form['machineName'].split('.')
    if len(ver) < 4:
        _version = '0.0.0'
    else:
        _version = '.'.join(ver[len(ver) - 3:])
    return _version

def promote_submissions(data, args, submissions):
    try:

        # get from submission by ID
        to_data = args["to_data"]
        path = args["path"]
        index_field = args["index_field"]
        to_token =args["to_token"]
        from_form =args["from_form"]
        _form_version = get_form_version(from_form)

        for form_submission in submissions:
            key_value = form_submission['data'][index_field]
            debug_logger.debug(f'{path}, {index_field}, {key_value}')
            form_submission['data']['_form_version'] = _form_version
            form_submission = data_changes(index_field, key_value, form_submission)
            res = update_submission(to_data, path, index_field, key_value, to_token, form_submission)

            data['description'] += "\n" + json.dumps(res, sort_keys=True, indent=4)
            if "_version" in res['data']:
                data['version'] = f'{_form_version} ({res["data"]["_version"]})'
            log = formio.log_promote(data)

    except Exception as ex:
        app_logger.error(ex)

    finally:
        return "ok"

def data_changes(index_field, key_value, data):
    if index_field == 'email':
        data['data']['password'] = 'CHANGEME'
    return data
    
def get_hosts_data(host):
    req = formio.get_submission('formio-hosts', host)
    return req['data']

def increment_version(_ver, part):
    result = ''
    version = _ver.split('.')
    major = 0 if len(_ver) == 0 else version[0]
    minor = 0 if len(version) < 2 else version[1]
    patch = 0 if len(version) < 3 else version[2]
    debug_logger.debug(version)
    if part == 'major':
        major = int(major) + 1
        minor = 0
        patch = 0
    elif part == 'minor':
        minor = int(minor) + 1
        patch = 0
    else:
        patch = int(patch) + 1
    result = str(major) + '.' + str(minor) + '.' + str(patch)
    return result

def get_val(data, key_field):
    try:
        return data[key_field]
    except:
        return ''

def get_token(req):
    url = get_ip(req)  + 'user/login'
    admin_user = get_val(req, 'admin_user')
    admin_password = get_val(req, 'admin_password')
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
        app_logger.error({ex})
    return token

# Get Form by Form Path
def get_form(path, host, token):

    # Use form path to determine field to match
    try:
        url = get_ip(host) + path
        debug_logger.debug(f'{url}')
        r = requests.get(url, headers={"x-jwt-token": token})
        return r.json()
    except Exception as ex:
        app_logger.error(ex)
        return None

# Update Form by ID or New
def update_form(path, host, token, data, id):

    # Use form path to determine field to match
    try:
        if id == None:
            debug_logger.debug(f'NEW {path} on ' + str(get_val(host, 'id')))
            r = requests.post(get_ip(host) + 'form', json=data, headers={"x-jwt-token": token})
        else:
            debug_logger.debug(f'UPDATE {path} on {str(get_val(host, "id"))}')
            r = requests.put(get_ip(host) + path, json=data, headers={"x-jwt-token": token})
        return r.json()
    except Exception as ex:
        app_logger.error(ex)
        return None

def get_version_list():
    result = []

    for (dirpath, dirnames, filenames) in walk('tmp'):
        result.extend((dirpath, dirnames, filenames))

    debug_logger.debug(result)
    return result

def get_submissions_for_path(args):
    result = []
    try:
        promote_type = args['promote_type']
        host = args["from_data"]
        path = args["path"]
        token =args["from_token"]
        index_field = args["index_field"]

        if promote_type == 'singleSubmission':
            key_value = args["key_value"]
            result.append(get_submission(host, path, index_field, key_value, token))
        else:
            url = f'{get_ip(host)}{path}/submission?limit=9999'
            app_logger.info(f'all submissions: {url}')
            r = requests.get(url, headers={"x-jwt-token": token})
            for l in r.json():
                if bool(l['data']):
                    result.append(l)
    except Exception as ex:
        app_logger.error(ex)
    return result

# Use form path to determine field to match
def get_submission(host, path, index_field, key_value, token):
    debug_logger.debug(f'{host} {path}, {index_field} {key_value}')

    submission_id = get_submission_id(host, path, index_field, key_value, token)
    if submission_id != None:
        url = get_ip(host) + path + '/submission/' + submission_id
        r = requests.get(url, headers={"x-jwt-token": token})
        return r.json()
    else:
        return None

def get_submission_id(host, path, index_field, key_value, token):
    url = get_ip(host) + path + f'/exists?data.{index_field}={key_value}'
    this_id = None
    r = requests.get(url, headers={"x-jwt-token": token})
    if r.text != 'Not found':
        this_id = r.json()['_id']
    return this_id

def update_submission(host, path, index_field, key_value, token, data):
    submission_id = get_submission_id(host, path, index_field, key_value, token)

    url = get_ip(host) + path + '/submission'
    if submission_id != None:
        debug_logger.debug(f'update {path}, {key_value}')
        r = requests.put(url + '/' + submission_id, json=data, headers={"x-jwt-token": token})
        action = 'update'
    else:
        debug_logger.debug(f'new {path}')
        r = requests.post(url, json=data, headers={"x-jwt-token": token})
        action = 'new'
    return r.json()

def get_ip(host):
    try:
        return 'http://' + get_val(host,'url') + ':' + str(get_val(host, 'port')) + '/'
    except Exception as ex:
        app_logger.error(f'Bad host: {host} {ex}')
        return ''
