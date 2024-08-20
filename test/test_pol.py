import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.inventory import Item
from almapiwrapper.acquisitions import POLine, Vendor, Invoice, fetch_invoices
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')


class TestPOLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        item = Item(barcode='A1002624931', zone='UBS', env='S')
        if item.data.find('.//po_line') is not None:
            pol_number = item.data.find('.//po_line').text
            pol = POLine(pol_number, zone='UBS', env='S')
            _ = pol.data
        else:
            pol = None

        if pol is None or pol.error is True:
            data = JsonData(filepath='test/data/pol_test1.json')
            pol = POLine(data=data, zone='UBS', env='S').create()
            item = Item(barcode='A1002624931', zone='UBS', env='S')
            item.data.find('.//po_line').text = pol.pol_number
            item.update()

    def test_update(self):
        item = Item(barcode='A1002624931', zone='UBS', env='S')
        pol_number = item.data.find('.//po_line').text
        pol = POLine(pol_number, zone='UBS', env='S')
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
        item = Item(barcode='A1002624931', zone='UBS', env='S')
        pol_number = item.data.find('.//po_line').text
        pol = POLine(pol_number, zone='UBS', env='S')
        items = pol.get_items()
        self.assertNotEqual(len(items), 0, 'No item found')

        self.assertEqual(items[0].barcode, 'A1002624931', 'Item barcode should be A1111000')

    def test_get_vendor(self):
        item = Item(barcode='A1002624931', zone='UBS', env='S')
        pol_number = item.data.find('.//po_line').text
        pol = POLine(pol_number, zone='UBS', env='S')
        vendor = pol.get_vendor()
        self.assertIsInstance(vendor, Vendor, 'Vendor should be an instance of Vendor')
        self.assertEqual(vendor.vendor_code, 'A100-1043', 'Vendor code should be "A100-1043"')


if __name__ == '__main__':
    unittest.main()
