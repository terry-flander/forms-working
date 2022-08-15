import unittest
from unittest import skip
import sys
sys.path.append(".")
import os
import json
from app.tests.test_base import UnitTest

from app.lib.jinja_api import get_file_name, get_full_file_name, save_doc, load_doc, \
    file_exists, remove_file,  render_template

class TestJinjaApi(UnitTest):

    def test_get_file_name(self):
        result = get_file_name(self.dir, self.path, self.file_name, self.ext)
        self.assertEqual(result, 'tmp/test/path/file_name.ext')

    def test_get_full_file_name(self):
        result = get_full_file_name(self.dir, self.path, self.file_name, self.ext)
        self.assertEqual(result, os.getcwd() + "/" + 'tmp/test/path/file_name.ext')

    def test_load_doc(self):
        result = load_doc(self.dir, self.path, self.file_name, self.ext)
        self.assertEqual(result, self.doc)

    def test_file_exists(self):
        file_name = get_file_name(self.dir, self.path, self.file_name, self.ext)
        result = file_exists(file_name)
        self.assertEqual(result, True)

    def test_render_template(self):

        save_doc(self.dir, self.path, self.file_name, 'jinja', json.dumps(self.template))

        result = render_template(self.file_name, self.data)
        self.assertEqual(result, json.dumps(self.data))
        remove_file(self.dir, self.path, self.file_name, 'jinja')

if __name__ == '__main__':
    unittest.main()
