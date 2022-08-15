import unittest
from unittest import skip
import sys
sys.path.append(".")
from app.tests.test_base import UnitTest

from app.lib.formio_api import get_form

class TestFormioApi(UnitTest):

    def test_get_form(self):
        result = get_form('user/register')
        self.assertEqual(result['path'], 'user/register')


if __name__ == '__main__':
    unittest.main()
