import unittest
import sys
sys.path.append(".")

from app.lib.jinja_api import save_doc, remove_directory, remove_file

class UnitTest(unittest.TestCase):

    def setUp(self):
        self.template = {
                "data": {
                "eloque_id": "{{data.eloque_id}}",
                "structure_id": "{{data.structure_id}}",
                "asset_name": "{{data.asset_name}}",
                "fiasset_status": "{{data.fiasset_status}}"
                }
            }
        self.data = {
                "data": {
                "eloque_id": "eloque_id",
                "structure_id": "structure_id",
                "asset_name": "asset_name",
                "fiasset_status": "fiasset_status"
                }
            }
        self.request = {
                "request": {
                    "data": {
                        "eloque_id": "eloque_id",
                        "structure_id": "structure_id",
                        "asset_name": "asset_name",
                        "fiasset_status": "fiasset_status"
                    }
                }
            }
        self.doc = 'testing, 1, 2, 3...'
        self.dir = 'test'
        self.path = 'path'
        self.file_name ='file_name'
        self.ext = 'ext'
        s = save_doc(self.dir, self.path, self.file_name, self.ext, self.doc)
    
    def tearDown(self):
        remove_file(self.dir, self.path, self.file_name, self.ext)
        remove_directory(f'tmp/{self.dir}/{self.path}')

if __name__ == '__main__':
    unittest.main()
