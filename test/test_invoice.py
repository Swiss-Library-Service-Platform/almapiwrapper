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

class TestInvoice(unittest.TestCase):
    # @classmethod
    # def setUpClass(cls):
    #     invoice = Invoice(invoice_number='PO-UBS-4828001_copy', zone='UBS', env='S').delete()

    def test_update(self):
        invoice =  Invoice(invoice_number='PO-UBS-4828001', zone='UBS', env='S')
        initial_voucher_date = invoice.data['payment']['voucher_date']
        if initial_voucher_date == '2023-04-10Z':
            new_date = '2023-05-10Z'
        else:
            new_date = '2023-04-10Z'

        invoice.data['payment']['voucher_date'] = new_date

        invoice_updated = invoice.update()
        self.assertEqual(invoice_updated.data['payment']['voucher_date'],
                         new_date,
                         f'Voucher date should be {new_date}')
        self.assertFalse(invoice_updated.error, f'Invoice update error: {invoice_updated.error}')

    @unittest.skip
    def test_create(self):
        invoice =  Invoice(invoice_number='PO-UBS-4828001', zone='UBS', env='S')
        invoice.invoice_number = 'PO-UBS-4828001_copy'
        new_invoice = Invoice(data=invoice.data, zone='UBS', env='S').create()

        self.assertEqual('PO-UBS-4828001_copy',
                         new_invoice.invoice_number,
                         f'Invoice number should be PO-UBS-4828001_copy')
        self.assertFalse(new_invoice.error, f'Invoice create error: {new_invoice.error}')

if __name__ == '__main__':
    unittest.main()
