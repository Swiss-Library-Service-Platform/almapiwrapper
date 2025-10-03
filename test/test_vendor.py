import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.acquisitions import POLine, Vendor
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

class TestVendor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Vendor('UBS-A100-1021_copy', 'UBS', 'S').delete()

    def test_update(self):
        v =  Vendor('UBS-A100-1021', 'UBS', 'S')
        name = v.data['name']
        if name == 'IFF Institut für Finanzwirtschaft und Finanzrecht':
            v.data['name'] = 'IFF Institut'
        else:
            v.data['name'] = 'IFF Institut für Finanzwirtschaft und Finanzrecht'
        name = v.data['name']
        v.update()

        self.assertEqual(v.data['name'],
                         name,
                         f'Vendor name should be {name}')
        self.assertFalse(v.error, f'Vendor update error: {v.error}')

    def test_create(self):
        v =  Vendor('UBS-A100-1021', 'UBS', 'S')
        v.data['code'] = 'UBS-A100-1021_copy'
        for account in v.data['account']:
            del account['account_id']
        _ = Vendor(zone='UBS', env='S', data=v.data).create()
        v_copy = Vendor('UBS-A100-1021_copy', zone='UBS', env='S')

        self.assertEqual('UBS-A100-1021_copy',
                         v_copy.data['code'],
                         f'Vendor code should be UBS-A100-1021')
        self.assertFalse(v.error, f'Vendor update error: {v.error}')

    def test_polines(self):
        v =  Vendor('UBS-A145-KONSORTIUM', 'UBS', 'S')
        polines = v.polines
        self.assertIsInstance(polines, list, 'Vendor polines should be a list')
        self.assertGreater(len(polines), 0, 'Vendor should have at least one PO Line')
        self.assertIsInstance(polines[0], POLine, 'Vendor polines should be a list of POLine objects')
        self.assertEqual(polines[0].data['owner']['value'], 'A100', 'POLine owner should be A100')

if __name__ == '__main__':
    unittest.main()
