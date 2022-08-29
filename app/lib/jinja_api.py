''' Routines to create jinja formatted documents '''
import logging
import os

from jinja2 import Environment, FileSystemLoader, UndefinedError, select_autoescape, Template, TemplateSyntaxError, TemplateError, BaseLoader
from pathlib import Path
import pandas as pd
import xlsxwriter

from app.lib.util import setup_logger
# from app.routes import app_log
debug_logger = setup_logger('debug', 'tmp/app_info.log', logging.DEBUG)
app_logger = setup_logger('info', 'tmp/app_info.log', logging.INFO)

templateLoader = FileSystemLoader(searchpath=["./app/templates/jinja/", "./tmp/test/path/"])
env = Environment(loader=templateLoader, trim_blocks=True, lstrip_blocks=True)

def render_template(template, data):
    templateFile = template + ('' if template.endswith('.jinja') else '.jinja')
    app_logger.info(f'template: {templateFile}')
    try:
        template = env.get_template(templateFile + ('' if templateFile.endswith('.jinja') else '.jinja'))
        return template.render(data=data)
    except TemplateSyntaxError as ex:
        app_logger.warning(f'{ex.message} line {ex.lineno} name {ex.name} filename: {ex.filename}')
        return None
    except TemplateError as ex:
        app_logger.warning({ex})
        return None
    except Exception as ex:
        app_logger.error(f'{templateFile} {ex}')
        return None

def render_report_template(templateFile, data):
    debug_logger.debug(f'template: {templateFile}')
    try:
        template = env.get_template(templateFile + ('' if templateFile.endswith('.jinja') else '.jinja'))
        return template.render(data=data)
    except Exception as ex:
        app_logger.error(ex)
        return None

def render_doc(doc_content, data={}):
      rtemplate = Environment(loader=BaseLoader()).from_string(doc_content)
      return rtemplate.render(data=data)

def save_doc(dir, path, file_name, ext, doc):
    result = 'ok'
    if doc != None:
        try:
            fileName = get_file_name(dir, path, file_name, ext)
            t = open(fileName, 'w')
            t.write(doc)
            t.close()
            debug_logger.debug(fileName)

        except Exception as ex:
            result = f'Unable to save Document as {fileName}'
            app_logger.error(ex)

    return result

def file_exists(fileName):
    return os.path.isfile(fileName)

def load_doc(dir, path, file_name, ext, mustExist=True):
    result = None
    try:
        fileName = get_file_name(dir, path, file_name, ext)
        t = open(fileName, 'r')
        result = t.read()
        t.close()
        debug_logger.debug(f'from {fileName}')
    except Exception as ex:
        if mustExist == True:
            debug_logger.debug(f'Not found: Required {fileName}')
            result = None
        else:
            debug_logger.debug(f'Not found: Optional {fileName}')
            result = ''
    finally:
        return result


def load_file(fileName, mustExist=True):
    result = None
    try:
        t = open(fileName, 'r')
        result = t.read()
        t.close()
    except Exception as ex:
        if mustExist == True:
            debug_logger.debug(f'Not found: Required {fileName}')
            result = None
        else:
            debug_logger.debug(f'Not found: Optional {fileName}')
            result = ''
    finally:
        return result

def write_xls_from_csv(dir, path, file_name, ext, csvData):

    try:
        fileName = get_file_name(dir, path, file_name, ext)
        debug_logger.debug(f'save XLS to {fileName}')
        writer = pd.ExcelWriter(fileName, engine='xlsxwriter')
        tab = ''
        sheet = ''
        for l in csvData.split('\n'):
            if tab == '':
                tab = l
            elif l == '.':
                df = pd.DataFrame([x.split(',') for x in sheet.split('\n')])
                df.to_excel(writer, sheet_name=tab, index=False, header=False)
                tab = ''
                sheet = ''
            else:
                sheet += l + '\n'
        writer.save()

    except Exception as ex:
        app_logger.error(ex)

def get_full_file_name(dir, path, file_name, ext):
    return os.getcwd() + "/" + get_file_name(dir, path, file_name, ext)

def get_file_name(dir, path, file_name, ext):
    try:
        create_directory(dir, path)
        return f'tmp/{dir}/{path}/{file_name}.{ext}'
    except Exception as ex:
        app_logger.error(ex)
        return None

def remove_file(dir, path, file_name, ext):
    try:
        file_name = get_file_name(dir, path, file_name, ext)
        os.remove(file_name)
    except Exception as ex:
        app_logger.error(ex)
        return None

def create_directory(dir, path):
    try:
        Path(f'tmp/{dir}/{path}').mkdir(parents=True, exist_ok=True)
    except Exception as ex:
        app_logger.error(ex)
        return None

def remove_directory(dir):
    try:
        os.removedirs(dir)
    except Exception as ex:
        app_logger.error(ex)
        return None
