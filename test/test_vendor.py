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
        Vendor('A100-1021_copy', 'UBS', 'S').delete()

    def test_update(self):
        v =  Vendor('A100-1021', 'UBS', 'S')
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
        v =  Vendor('A100-1021', 'UBS', 'S')
        v.data['code'] = 'A100-1021_copy'
        for account in v.data['account']:
            del account['account_id']
        _ = Vendor(zone='UBS', env='S', data=v.data).create()
        v_copy = Vendor('A100-1021_copy', zone='UBS', env='S')

        self.assertEqual('A100-1021_copy',
                         v_copy.data['code'],
                         f'Vendor code should be A100-1021_copy')
        self.assertFalse(v.error, f'Vendor update error: {v.error}')

if __name__ == '__main__':
    unittest.main()
