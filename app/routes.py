
"""Routes for parent Flask app."""

from operator import index
from flask import Flask
from flask import Flask, render_template, request, session, send_file
from flask import current_app as app
from jinja2 import TemplateNotFound

from werkzeug.exceptions import HTTPException
import os

import json
import logging
import sys
import app.lib.webhook as wh
import app.lib.formio_api as formio
import app.lib.jinja_api as jinja

from app.lib.util import setup_logger
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

TESTING = False

@app.route('/')
def home():
  if get_session_logged_in() == None:
    return render_template('login.html')
  else:
    return renderWithMenus(request, "home/index.html", None)

@app.route('/profile.html')
def route_profile():
  path = 'user'
  keyvalue = session['current_user']
  app_logger.info(f'{path} {keyvalue}')
  if get_session_logged_in() == None:
    app_logger.info(f'{session.get("logged_in")} - {session.get("access")}')
    return home()

  f = formio.get_form(path)
  if f == {}:
    return f'Unable to find form: {path}'
  else:
    desc = f["title"]
    ops_portal_url = os.environ.get('OPS_PORTAL_URL')
    view_access = formio.get_access_list(session['access_object'], 'view', 'full')
    form_access = formio.get_access_list(session['access_object'], 'form', 'full')
    sidenav = formio.get_menu_layout('sidenav')

    return render_template('home/profile.html', path=path, keyvalue=keyvalue, desc=desc, ops_portal_url=ops_portal_url
    ,view_access=view_access, form_access=form_access, sidenav=sidenav, segment='')


@app.route('/<template>')
def route_template(template):

  try:

    if get_session_logged_in() == None:
      return render_template('login.html')
      
    if not template.endswith('.html'):
        template += '.html'

    return renderWithMenus(request, "home/" + template, None)

  except TemplateNotFound:
    return render_template('home/page-404.html'), 404

  except Exception as ex:
    app_logger.error(ex)
    return render_template('home/page-500.html'), 500

@app.route('/env', methods=['GET'])
def show_env():
  if get_session_logged_in() == None:
    return home()
  env = '<style> \
          table, th, td { \
            border: 1px solid white; \
            border-collapse: collapse; \
          } \
          th, td { \
            background-color: #96D4D4;} \
        </style> \
    <table> \
    <tr><th>Configuration Key</th><th>Value</th></tr>'
  for k in app.config:
    env += '<tr><td>' + k + '</td><td>' + str(app.config[k]) + '</td></tr>'
  env += '</table>'
  return env

@app.route('/login', methods=['POST'])
def do_admin_login():
  login = request.form

  session['environment_title'] = os.environ.get('ENVIRONMENT_TITLE')

  userName = login['username']
  password = login['password']
  session['logged_in'] = None
  session['token'] = ''
  session['access'] = ''
  session['access_object'] = ''
  session['loginMessage'] = 'Username/Password invalid'
  session['current_user'] = userName

  login = formio.get_new_login(userName, password)
  if login != None:
    session['token'] = login[0]
    session['access'] = login[1]
    session['access_object'] = login[2]
    session['logged_in'] = 'true'
  return home()

@app.route('/logout')
def logout():
  session['logged_in'] = None
  session['token'] = ''
  session['access'] = ''
  session['access_object'] = ''
  session['loginMessage'] = ''
  session['environment_title'] = os.environ.get('ENVIRONMENT_TITLE')

  return home()

@app.route('/tool/<tag>', methods=['GET'])
def tool(tag):
  if get_session_logged_in() == None:
    return home()

  if tag == 'view':    
    data = formio.get_submission('view', 'view_browse')
    return renderWithMenus(request, 'view.html', data['data'])
  else:
    data = formio.get_submissions(tag, session['access_object'])
    return renderWithMenus(request, tag + '.html', data)

@app.route('/admin', methods=['GET'])
def admin():
  if get_session_logged_in() == None:
      return home()

  view_access = formio.get_access_list(session['access_object'], 'view', 'full')
  form_access = formio.get_access_list(session['access_object'], 'form', 'full')
  return render_template('admin-2.html', form_access=form_access, view_access=view_access, segment='admin')

@app.route('/tool/reference/<refid>', methods=['GET'])
def tool_reference(refid):
    if get_session_logged_in() == None:
        return home()

    if not get_form_access(refid):
        return 'Access to form not allowed'

    f = formio.get_form(refid)
    if f != None:
        data = formio.get_reference_submissions(refid, None)
        data[0]['title'] = f["title"]
        return renderWithMenus(request, 'references.html', data)

    else:
        return f'No form exists for {refid}'

'''
View setup and submissions request for datatable support

required arguments:
  path -- View ID from Resource
  page -- page number to return starting with 1
  page_length -- number of submissions to return
'''
@app.route('/view/<view_id>', methods=['GET'])
def view(view_id):
    if get_session_logged_in() == None:
        return home()
    
    if not get_form_access('view'):
        return 'Access to view not allowed'

    data = formio.get_view_layout(view_id)

    if data != None:
        return renderWithMenus(request, 'view.html', data['data'])
    else:
        return f'No view exists for {view_id}'

def renderWithMenus(request, form, data):
    sidenav = formio.get_menu_layout('sidenav')
    segment = get_segment(request)
    view_access = formio.get_access_list(session['access_object'], 'view', 'full')
    form_access = formio.get_access_list(session['access_object'], 'form', 'full')
    return render_template(form, data=data, view_access=view_access, form_access=form_access, segment=segment, sidenav=sidenav)

# Helper - Extract current page name from request
def get_segment(request):
  try:
    segment = request.path.split('/')[-1]

    if segment == '':
      segment = 'index'

    return segment

  except:
    return None

@app.route('/get_submissions_paged', methods=['GET'])
def submissions_paged():
    app_logger.info(f'paging...')
    if get_session_logged_in() == None:
        return home()
    try:
      path = request.args.get('path')
      page_length = request.args.get('length')
      fields = request.args.get('fields')
      formats = request.args.get('formats')
      sorts = request.args.get('sorts')
      draw = request.args.get('draw')
      start = request.args.get('start')

      app_logger.info(f'paging: {path} {page_length} {start}')
      if not get_form_access(path):
          return 'Access to form not allowed'

      f = formio.get_form(path)
      if f != None:
          rows = formio.get_submissions_paged(path, start, page_length, fields, formats, sorts, session['access_object'])
          records = formio.get_paged_count(path)
          return json.dumps({
              "draw": draw,
              "recordsTotal": records,
              "recordsFiltered": records,
              "data": rows })
      else:
          app_logger.warn(f'No form exists for {path}')
          return f'No form exists for {path}'
    except Exception as ex:
      app_logger.error(ex)
      return ex

@app.route('/edit/<path>/<keyvalue>', methods=['GET'])
def edit_submission(path, keyvalue):
  app_logger.info(f'{path} {keyvalue}')
  if get_session_logged_in() == None:
    app_logger.info(f'{session.get("logged_in")} - {session.get("access")}')
    return home()

  if not get_form_access(path):
    return 'Access to form not allowed'

  f = formio.get_form(path)
  if f == {}:
    return f'Unable to find form: {path}'
  else:
    desc = f["title"]
    ops_portal_url = os.environ.get('OPS_PORTAL_URL')
    return render_template('edit_submission.html', path=path, keyvalue=keyvalue, desc=desc, ops_portal_url=ops_portal_url)

@app.route('/edit/reference/<path>/<keyvalue>', methods=['GET'])
def edit_reference(path, keyvalue):
  if get_session_logged_in() == None:
    return home()

  if not get_form_access(path):
    return 'Access to form not allowed'

  f = formio.get_form(path)
  desc = f["title"]
  ops_portal_url = os.environ.get('OPS_PORTAL_URL')
  return render_template('edit_reference.html', path=path, keyvalue=keyvalue, desc=desc, ops_portal_url=ops_portal_url)

@app.route('/action/submission', methods=['POST'])
def copy_reference():
  if get_session_logged_in() == None:
    return home()

  data = json.loads(request.json)
  action = data['action']
  path = data['path']
  keyfield = data['keyfield']
  id = data['id']
  app_logger.info(f'Action: {action} path: {path} keyfield: {keyfield} id: {id}')

  if (action == 'rename'):
    new_id = data['new_id']
    token = get_session_value('token')
    return formio.rename_reference(keyfield, id, new_id, token)

  elif (action == 'copy'):
    try:
      new_id = data['new_id']
      # Check for duplicate
      if formio.get_submission_id(path, keyfield, new_id) != 'new':
        return f'Reference {new_id} already exists'
      from_submission = formio.get_submission(path, id)
      new_submission = update_copy(from_submission, keyfield, new_id)
      token = get_session_value('token')
      new_reference = formio.update_submission(new_submission, path, keyfield, new_id, token)
      if new_id in new_reference['data'].values():
        app_logger.info('Copy successful')
        return "Copy Successful"
      else:
        app_logger.warn(new_reference)
        return new_reference
    except Exception as ex:
      app_logger.error(ex)
      return "Error: Check Log"

  elif action == 'delete':
    # Check that exists to delete
    if formio.get_submission_id(path, keyfield, id) == 'new':
      return f'Reference {id} does not exist'
    else:
      resp = formio.delete_submission(path, keyfield, id)
      return resp
      
  else:
    return 'Unrecognised Action'

def update_copy(ref, keyfield, new_id):
    ref['data'][keyfield] = new_id
    if 'id2' in ref['data']:
      ref['data']['id2'] = new_id
    return ref


@app.route('/view/<path>/<keyvalue>', methods=['GET'])
def view_layout(path, keyvalue):
    if get_session_logged_in() == None:
      return home()

    return wh.load_layout(path, keyvalue)
   
@app.route('/view_dis/<path>/<keyvalue>', methods=['GET'])
def view_dis(path, keyvalue):
    if get_session_logged_in() == None:
      return home()

    fileName = jinja.get_full_file_name('layouts', path, keyvalue, 'xlsx')
    app_logger.info(f'Looking for: {fileName}')

    if jinja.file_exists(fileName):
      return send_file(fileName)
    else:
      return '<h1>Download DIS Spreadsheet</h1><h2>No Excel file has been generated. You must Validate and Save with the Update As-Design/As-Build checked</h2>'
  
@app.route('/view_json/<path>/<keyvalue>', methods=['GET'])
def view_json(path, keyvalue):
    if get_session_logged_in() == None:
      return home()

    fileName = 'json/' + path + '-' + keyvalue + '.json'
    app_logger.info(fileName)
    if jinja.file_exists(fileName):
      return send_file(fileName)
    else:
      return '<h1>Download DIS JSON</h1><h2>No JSON file exists</h2>'
  
@app.route('/doc/<doc_id>', methods=['GET'])
def render_doc(doc_id):
 
  doc_sub = formio.get_submission('documents', doc_id)
  wrap_sub = formio.get_submission('documents', 'manual-wrapper')
  sidenav = formio.get_menu_layout('manual')

  if doc_sub != None:
    document_content = doc_sub['data']['document_content']
    if wrap_sub != None:
      wrapper_content = wrap_sub['data']['document_content']
    else:
      wrapper_content = '{{document_content}}'
    html = wrapper_content.replace('{{document_content}}',document_content)
    return jinja.render_doc(html, data=sidenav)
  else:
    return render_template('home/page-404.html'), 404
  
@app.route('/app_log/<log_type>', methods=['GET'])
def app_log(log_type):
    if get_session_logged_in() == None:
      return home()
    if not log_type in ['app_info', 'app_debug', 'webserver']:
      return render_template('app_log.html')
    else:
      fileName = f'./tmp/{log_type}.log'
      app_logger.info(fileName)
      log = jinja.load_file(fileName, False).splitlines()
      return render_template('app_log_content.html', log=reversed(log))
  
@app.route('/log/<path>/<keyvalue>', methods=['GET'])
def change_log(path, keyvalue):
    if get_session_logged_in() == None:
      return home()

    jsonData = formio.load_change_log(path, keyvalue)
    return render_template('change_log.html', data=jsonData, keyvalue=keyvalue)

@app.route('/promote_log', methods=['GET'])
def promote_log():
    if get_session_logged_in() == None:
      return home()

    jsonData = formio.load_promote_log()
    return render_template('promote_log.html', data=jsonData)

@app.route('/report/<report>/<keyvalue>', methods=['GET'])
def view_report(report, keyvalue):

  if get_session_logged_in() == None:
    return home()

  return wh.build_report(report, keyvalue)

@app.route('/formio/<path>/submission/<keyvalue>', methods=['GET'])
def formio_get_submission(path, keyvalue):

  if get_session_logged_in() == None:
    return home()

  return formio.get_submission(path, keyvalue)

@app.route('/formio/<path>/submission/<keyvalue>', methods=['PUT', 'POST'])
def formio_update_submission(path, keyvalue):

  app_logger.info(f'{path} {keyvalue}')
  if get_session_logged_in() == None:
    return home()
  
  form_access = formio.get_access_list(session['access_object'], 'form', 'full')
  if not path in form_access:
    r = wh.build_error(path, 'You do not have permission to update submissions on this form')
    return r, 400

  company_access = formio.get_access_list(session['access_object'], 'company', 'full')

  token = get_session_value('token')
  try:
    update_result = formio.update_submission(request.json, path, keyvalue, token, company_access)
    debug_logger.debug(f'{update_result}')
  except Exception as ex:
    debug_logger.error(f'{ex}')

  if update_result[0] != 'ok':
    return update_result[1], 400

  if update_result[0] == 'ok':
    r = wh.do_webhooks(request.json, path, token)
    if r != 'ok':
      app_logger.info(r)
      return r, 400

  return update_result[1]

@app.route('/formio/reference/<path>/submission/<keyvalue>', methods=['GET'])
def formio_get_reference_submission(path, keyvalue):

  if get_session_logged_in() == None:
    return home()

  return formio.get_submission(path, keyvalue)

@app.route('/formio/table/<keyvalue>', methods=['GET'])
def formio_get_table_json_data(keyvalue):

  if get_session_logged_in() == None:
    return home()
  path = 'tables'
  data = formio.get_submission(path, keyvalue)
  try:
    if data != None:
      data = data['data']['json_data']
      selections = json.loads(data)
      debug_logger.debug(selections)
  except Exception as ex:
    debug_logger.error(ex)

  return data

@app.route('/formio/reference/<path>/submission/<keyvalue>', methods=['PUT', 'POST'])
def formio_update_reference_submission(path, keyvalue):
  
  if get_session_logged_in() == None:
    return home()

  token = get_session_value('token')
  try:
    result = formio.update_submission(request.json, path, keyvalue, token)
  except Exception as ex:
    app_logger.err(f'{ex}')
  
  if result != None:
    r = wh.do_webhooks(request.json, path, token)
    if r != 'ok':
      app_logger.info(r)
      return r, 400
      
  return result

@app.route('/action/layout/<path>', methods=['POST'])
def action_get_layout(path):
  
  jsonData = json.loads(request.data)

  return wh.save_layout(path, jsonData)

@app.route('/formio/<path>', methods=['GET'])
def formio_get_form(path):
  
  if not get_form_access(path):
    return 'Access to form not allowed'

  return formio.get_form(path)

@app.route('/formio/reference/<path>', methods=['GET'])
def formio_get_reference_form(path):
  
  if not get_form_access(path):
    return 'Access to form not allowed'

  return formio.get_form(path)

@app.route('/formio/form/<path>/submission', methods=['GET'])
def formio_get_reference_submissions(path):
  submission_args = None
  try:
    index_field = formio.get_form_keyfield(path)
    limit = request.args.get('limit', default = '999', type = str)
    skip = request.args.get('skip', default = '0', type = str)
    id__regex = request.args.get('data.id__regex', default = '', type = str)
    submission_args = f'?limit={limit}&skip={skip}&sort=data.{index_field}' # &data.id__regex={id__regex}'
  except:
    submission_args = None

  debug_logger.info(f'{path} {submission_args}')
  
  result = formio.get_reference_submissions(path, submission_args)
  return result

def get_session_logged_in():
  if (not session.get('logged_in') or session.get('logged_in') == None) and not TESTING:
    return None
  else:
    return 'true'

def get_form_access(path):
  form_access = formio.get_access_list(session['access_object'], 'form', 'read')
  return formio.check_form(path, form_access)

def get_session_value(id):
  if (not session.get('logged_in') or session.get('logged_in') == None) and not TESTING:
    return None
  else:
    return session.get(id)
