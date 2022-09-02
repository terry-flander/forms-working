''' Original Library of APIs '''
import logging
from operator import index
import sys
import os

import json

from pyparsing import conditionAsParseAction

from app.lib.layout import calculate_layout_v1
from app.lib.layout_v2 import calculate_layout_v2

from app.lib.update_db import Timescale
import app.lib.formio_api as formio
import app.lib.jinja_api as jinja
import app.lib.promote_api as promote

from app.lib.util import setup_logger, build_error
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

always_trigger = ['update_initial_mapping', 'resource', 'promote_form', 'change_password']
conditional_trigger = ['build_json', 'create_as_design', 'create_as_built', 'update_metadata', 'build_layout', 'save_excel', 'map_data', 'save_layout', 'save_map_data']

'''
Method:
1. Check for any actions linked to the current form
2. For each action, check to see if any required trigger field has the value 'true', otherwise always execute

Note:
data -- Submission data
path -- Form name of submission
token -- Token allows new submissions to have current user ID
'''

def do_webhooks(data, path, token):
    workflows = get_workflows(path)
    response = "ok"
    app_logger.info(f'{path} Workflows: {workflows}')
    if workflows != None:
        for w in workflows:
            map_data = None
            if check_flag(data, w['trigger_field_id'], w['trigger_field_id']):
                for a in w['workflowActions']:
                    method = a['method']
                    argument = a['argument']
                    app_logger.info(f'{method} {argument}')
                    if method == 'update_initial_mapping':
                        response = webhook_update_initial_mapping(data, token, argument)

                    elif method == 'build_json':
                        response = webhook_build_json(data, argument)

                    elif method == 'update_metadata':
                        response = webhook_update_metadata(argument, data)

                    elif method == 'resource':
                        response = webhook_resource(data, path)

                    elif method == 'promote_form':
                        response = webhook_promote_form(data)

                    elif method == 'save_excel':
                        response = save_excel(path, data)
                        if map_data != None:
                            response = save_excel(argument, map_data)

                    elif method == 'change_password':
                        response = change_password(data, token)

                    elif method == 'build_layout':
                        mapped = build_layout(argument, data)
                        response = mapped[0]
                        map_data = mapped[1]

                    elif method == 'map_data':
                        mapped = template_map_data(argument, data, map_data)
                        response = mapped[0]
                        map_data = mapped[1]

                    elif method == 'save_layout':
                        response = save_layout(argument, get_id(path, data), json.dumps(map_data))

                    elif method == 'save_map_data':
                        response = webhook_update_submission(argument, data if map_data == None else map_data, token)
    
    return response

def check_flag(data, field_id, other_id):
    result = False
    if field_id == 'always':
        return True
    if field_id == 'other':
        field_id = other_id
    try:
        result = data['data'][field_id]
    except:
        debug_logger.debug(data)
    return result

def get_workflows(path):
    result = None
    try:
        sub = formio.get_submission('app-forms', path)
        if 'addWorkflow' in sub['data'] and sub['data']['addWorkflow'] == True:
            result = sub['data']['workflows']
    except Exception as ex:
        app_logger.error(ex)
    return result

'''
CREATE OR UPDATE WORKFLOW
** TODO **
    Workflow forms list to create and/or patch all connections
    based on data entered on first form of Workflow.
'''
def webhook_update_initial_mapping(data, token, argument):
   
    debug_logger.debug('save_initial_mapping...')

    path = 'initial-mapping'

    id = get_id(path, data)
    doc = build_initial_mapping(data)

    jinja.save_doc('submissions', path + '-new', id, 'json', doc[0])
    jinja.save_doc('submissions', path + '-patch', id, 'json', doc[1])
    jinja.save_doc('submissions', path + '-patch-self', id, 'json', doc[2])

    if doc[0] != 'None':
        formio.patch_submission(doc, 'id', id, token, argument)
        formio.patch_one('', doc[2], 'id', id)

    return 'ok'

''' 
CREATE JSON FILE
'''
def webhook_build_json(sub, path):

    try:
        data = sub['submission']
        doc = jinja.render_template('template_' + data['data']['jinja_template'], data)
        jinja.save_doc(f'json', path, get_id(path, data), 'json', doc)
        return 'ok'
    except Exception as ex:
        app_logger.error(ex)
        return None

def webhook_update_submission(path, data, token):

    try:
        id = get_id(path, data)
        debug_logger.debug(f'{path} {id}')
        jinja.save_doc('submissions', path, id, 'json', json.dumps(data))
        if data != None:
            formio.update_submission(data, path, 'id', id, token)
        return 'ok'
    except Exception as ex:
        app_logger.error(ex)
        return None

'''
UPDATE META-DATA FOR THIS FORM
'''
def webhook_update_metadata(path, data):

    doc = None
    result = 'ok'

    try:                
        keep_list = get_active_components(data)
        data['data']['keep_child'] = keep_list

        doc = jinja.render_template(path + '-rcs', data)

        jinja.save_doc('metadata', path, get_id(path, data), 'sql', doc)
    except Exception as ex:
        return ''

    if doc != None:
        try:
            timescale_connection = ''
            # transpara_get_groups('ops');
            # timescale_connection = 'dbname=postgres user=postgres password= host= port=5432'
            timescale = Timescale()
            con_result = timescale.connect(timescale_connection)
            if con_result != 'ok':
                result = build_error('update-metadata', con_result)
            else:
                up_result = timescale.update(doc)
                if up_result != 'ok':
                    result = build_error('update-metadata', up_result)
        
        except Exception as ex:
            debug_logger.debug(f'Unable to update Metadata {ex}')
            result = build_error('update-metadata', ex)

        finally:
            timescale.disconnect()

        return result

def get_active_components(data):
    result = []
    try:
        for f in ['F01','F02','F03','F04','F05','F06','F07','F08','F09','F10','F11','F12','F13''F14','F15']:
            if data['data'][f]:
                sensors = data['data'][f]
                for s in sensors:
                    c = s['component_id']
                    if c != '' and not c in result:
                        result.append(c)
    except Exception as ex:
        debug_logger.debug(f'{result}')
    return result

# Used by Resource Forms only
def webhook_resource(data, resource):

    jinja.save_doc('resources', resource, get_resource_value(data, 'id'), 'json', get_resource_value(data, 'jsonData'))
    return 'ok'

def webhook_promote_form(req):
  debug_logger.debug('action_promote')
  try:
    data = req['data']
    form_name = data['path']
    from_host = data['promote_from_host']
    to_host = data['promote_to_host']
    
    debug_logger.debug(f'{form_name} from {from_host} to {to_host}')

    return promote.do_promote(data)
    
  except Exception as ex:
    app_logger.error(ex)
    return 'error'

def template_map_data(argument, ref, map_data):
    result = 'ok'
    mapped = {}
    data = ref['data'] if map_data == None else map_data
    try:
        mapped = json.loads(jinja.render_template(argument, data))

    except Exception as ex:
        result = f'Unable to map data with: {argument}'
        app_logger.error(f'{result} {ex}')

    return result, mapped

def save_layout(path, id, data):

    return jinja.save_doc('layouts', path, id, 'json', data)

def save_excel(path, data):
    
    # Create the CSV input required for Excel create
    csvData = jinja.render_template(path + '-dis', data)

    # Save CSV
    jinja.save_doc('layouts', path, get_id(path, data), 'csv', csvData)

    # Convert to XLS
    jinja.write_xls_from_csv('layouts', path, get_id(path, data), 'xlsx', csvData)

    return 'ok'

def change_password(req, token):
    result = 'ok'
    data = req['data']

    new_password = data['new_password']
    new_password2 = data['new_password2']

    debug_logger.debug(f'{new_password} {new_password2}')

    # Confirm Old password valid -- Use token to validate
    current_user = formio.get_user(token)
    if current_user == None:
        return 'Current user does not exist'

    # Make sure new and confirm passwords are the same
    elif new_password != new_password2:
        result = build_error ('new_password2', "New and Confirm passwords entered do not match")

    # Update user record
    else:
        # result = formio.update_submission(data, 'user', '','',token)
        keyvalue = current_user['data']['email']
        current_user['data']['password'] = new_password
        current_user['data']['submit'] = True
        formio.update_submission(current_user, 'user', 'email', keyvalue, token)

    return result

'''
END OF WEBHOOK ENTRY POINTS
'''

'''
Expects string return and will parse using json.loads()
'''
def load_layout(path, id):
    result = ''

    try:
        jsonData = jinja.load_doc('layouts', path, id, 'json', True)
        if jsonData == None:
            jsonData = json.dumps(formio.get_submission(path, id))

        data = json.loads(jsonData)
        result = jinja.render_template(path + '-layout', data)

    except Exception as ex:
        result = f'Unable to display layout. In Mapping: Design you must first Build Design Layout'
        app_logger.error(ex)

    finally:
        return result

def build_report(report, keyvalue):

    result = ''
    error = False
    args = ''
    if report == 'report-request':
        app_logger.info('report-request')
        rep = formio.get_submission('report-request', keyvalue)
        report_data = rep['data']['report']['data']
        args = getArgs(rep)
        if args == '':
            error = True
            result = 'Unable to generate report: Missing selections'
    else:
        app_logger.info(report)
        rep = formio.get_submission('reports', report)
        report_data = rep['data']

    if not error:
        data = []
        for source in report_data['sourceSubmissions']:
            sourceData = []
            select = args
            app_logger.info(source)
            if 'selectionFields' in source:
                select += f'&select={source["selectionFields"]})'
            subs = formio.get_reference_submissions(source['app_form'], select)
            sub = json.loads(subs)
            if len(sub) == 0 or not 'data' in sub[0]:
                error = True
                result += f'Missing data for {source["app_form"]} {select}<br/>'
            else:
                for s in sub:
                    sourceData.append(s['data'])
                data.append(sourceData)

        if not error:
            result = jinja.render_report_template(report_data['templateFile'], data)

        if result == None:
            error = True
            result = 'Unable to create report'
    if error:
        app_logger.warn(result)

    return result

def getArgs(rep):
    result = ''
    selections = rep['data']['selections']
    for selection in selections:
        if selection['filterType'] == 'exact':
            result += f'&data.{selection["fieldId"]}={selection["exact"]}'
        elif selection['filterType'] == 'list' and selection["listItem"]["value"] != '':
            result += f'&data.{selection["fieldId"]}={selection["listItem"]["value"]}'
        elif selection['filterType'] == 'regex':
            result += f'&data.{selection["fieldId"]}__regex={selection["regEx"]}'
    args = f'?limit=9999{result}'
    return args

def build_layout(argument, data):
    result = 'ok'
    debug_logger.debug(f'{argument}')
    if argument == 'v2.1':
        layout = calculate_layout_v2(data['data'])
    else:
        layout = calculate_layout_v1(data['data'])
    result = layout[0]
    layout = layout[1:]
    if result == 'ok':        
        data = add_layout(data, layout)
    return result, data

def build_as_design_data(data):
    debug_logger.debug('build_as_design_data')
    layout = calculate_layout(data['data'])
    return add_layout(data, layout)

def add_layout(data, layout):
    data['data']['all_components'] = json.dumps(data['data']['allComponentsList'])
    data['data']['all_fibers'] = str(listOfValues(data['data']['allFibersList'])).replace('\'', '"')
    data['data']['fiber_layout'] = layout[0]
    data['data']['deflection'] = layout[3]
    data['data']['shear'] = layout[1]
    data['data']['bending_moment'] = layout[2]
    return data

def calculate_layout(data):
    jinja_template = data['jinja_template']
    if jinja_template == 'v2.1':
        return calculate_layout_v2(data)
    else:
        return calculate_layout_v1(data)

def build_initial_mapping(data):
    newMap = jinja.render_template('initial-mapping', data)
    patchMap = jinja.render_template('patch-submissions', data)
    selfPatchMap = jinja.render_template('patch-overview', data)
    return newMap, patchMap, selfPatchMap

def listOfValues(l):
    values = []
    for v in l:
        values.append(v['value'])
    return values


def get_id(path, data):
    try:
        index_field = formio.get_form_keyfield(path)
        return data['data'][index_field]
    except Exception as ex:
        return None

def get_resource_value(data, field_name):
    try:
        r = data['request']
        d = r['data']
        return d[field_name]
    except:
        return None
    
