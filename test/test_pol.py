import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.acquisitions import POLine, Vendor, Invoice, fetch_invoices
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

def create_pol():
    """Used after refreshing the sandbox to create a new POLine"""
    pol = POLine('A100-800098', 'UBS', 'P')
    pol.data["fund_distribution"][0]['fund_code']['value'] = 'Fundforall'
    pol.data["acquisition_method"] = {'value': 'TECHNICAL'}
    pol_copy = POLine(data=pol.data, zone='UBS', env='S').create()
    invoice = Invoice

class TestPOLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = JsonData(filepath='test/data/pol_test2.json')

    def test_update(self):
        pol =  POLine('131268', 'UBS', 'S')
        reclaim_interval = pol.data['reclaim_interval']
        if reclaim_interval == '60':
            pol.data['reclaim_interval'] = '30'
        else:
            pol.data['reclaim_interval'] = '60'
        reclaim_interval = pol.data['reclaim_interval']
        pol.update()

        self.assertEqual(pol.data['reclaim_interval'],
                         reclaim_interval,
                         f'POL reclaim interval should be {reclaim_interval}')

    def test_get_items(self):
        pol =  POLine('131268', 'UBS', 'S')
        items = pol.get_items()
        self.assertNotEqual(len(items), 0, 'No item found')

        self.assertEqual(items[0].barcode, 'A1111000', 'Item barcode should be A1111000')

    def test_get_vendor(self):
        pol =  POLine('131268', 'UBS', 'S')
        vendor = pol.get_vendor()
        self.assertIsInstance(vendor, Vendor, 'Vendor should be an instance of Vendor')
        self.assertEqual(vendor.vendor_code, 'A100-1043', 'Vendor code should be "A100-1043"')


if __name__ == '__main__':
    unittest.main()
