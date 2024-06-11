import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.acquisitions import POLine, Vendor, Invoice, InvoiceLine, fetch_invoices
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

class TestInvoice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        invoice = Invoice(invoice_number='20000077919999', zone='UBS', env='S')
        _ = invoice.data
        if invoice.error is True:
            data = JsonData(filepath='test/data/invoice_test1.json')
            invoice = Invoice(data=data, zone='UBS', env='S').create()

        if 'invoice_lines' not in invoice.data or invoice.data['invoice_lines']['total_record_count'] == 0:
            data = JsonData(filepath='test/data/invoice_test1.json')
            invoice_line_data = data.content['invoice_lines']['invoice_line'][0]
            invoice_line = InvoiceLine(invoice_id=invoice.invoice_id,
                                       data=invoice_line_data,
                                       zone='UBS',
                                       env='S').create()


    def test_update(self):
        invoice =  Invoice(invoice_number='20000077919999', zone='UBS', env='S')
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
        invoice =  Invoice(invoice_number='20000077919999', zone='UBS', env='S')
        invoice.invoice_number = '20000077919999_copy'
        new_invoice = Invoice(data=invoice.data, zone='UBS', env='S').create()

        self.assertEqual('PO-UBS-4828001_copy',
                         new_invoice.invoice_number,
                         f'Invoice number should be PO-UBS-4828001_copy')
        self.assertFalse(new_invoice.error, f'Invoice create error: {new_invoice.error}')

    def test_get_invoice_lines(self):
        invoice =  Invoice(invoice_number='20000077919999', zone='UBS', env='S')
        invoice_lines = invoice.get_invoice_lines()
        self.assertNotEqual(len(invoice_lines), 0, 'No invoice line found')

        # self.assertEqual(invoice_lines[0].invoice_line_id, '2000007791-1', 'Invoice line id should be 2000007791-1')


if __name__ == '__main__':
    unittest.main()
