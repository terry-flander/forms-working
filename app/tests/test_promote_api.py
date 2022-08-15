import unittest
from unittest import skip
import sys
sys.path.append(".")
from app.tests.test_base import UnitTest

from app.lib.promote_api import get_form_version, increment_version

class TestPromoteApi(UnitTest):

    def test_get_form_version(self):
        result = get_form_version({"machineName": "test.1.2.3"})
        self.assertEqual(result, '1.2.3')

    def test_increment_version_patch(self):
        result = increment_version("1.2.3", '')
        self.assertEqual(result, '1.2.4')

    def test_increment_version_minor(self):
        result = increment_version("1.2.3", 'minor')
        self.assertEqual(result, '1.3.0')

    def test_increment_version_major(self):
        result = increment_version("1.2.3", 'major')
        self.assertEqual(result, '2.0.0')

if __name__ == '__main__':
    unittest.main()
