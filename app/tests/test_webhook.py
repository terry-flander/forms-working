import unittest
from unittest import skip
import sys
sys.path.append(".")
import os
import json
from app.tests.test_base import UnitTest

from app.lib.webhook import get_resource_value, get_index_id

class TestWebhook(UnitTest):

    def test_get_resource_value(self):
        result = get_resource_value(self.request, 'structure_id')
        self.assertEqual(result, 'structure_id')

    def test_get_index_id(self):
        result = get_index_id(self.data)
        self.assertEqual(result, 'index_id')

if __name__ == '__main__':
    unittest.main()
