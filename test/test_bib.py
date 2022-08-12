import unittest
import sys
import os

from almapiwrapper.inventory import IzBib, NzBib, Holding, Item
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")


class TestBib(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        IzBib('991043825829705501', 'UBS', 'S', from_nz_mms_id=True).delete()
        Item(barcode='03124510_NEW', zone='HPH', env='S').delete()

        _ = [hol.delete() for hol in IzBib('991000975799705520', zone='HPH', env='S').get_holdings()
             if hol.holding_id != '2234409340005520']

        item = Item(barcode='03124510_NEW_2', zone='HPH', env='S')
        if item.error is False:
            item.holding.delete(force=True)

    def test_get_bib(self):

        # Get the data
        bib = IzBib('991000975799705520', 'HPH', 'S')
        title = bib.data.find('.//datafield[@tag="245"]/subfield[@code="a"]').text

        self.assertEqual(title, 'Je veux un python pour mon anniversaire',
                         'Title not corresponding to "Je veux un python pour mon anniversaire"')

        nz_mms_id = bib.get_nz_mms_id()

        self.assertEqual(nz_mms_id, '991043825829705501',
                         'NZ MMS ID not found (should be "991043825829705501")')

    def test_copy_from_nz(self):

        # Get the data from NZ id of a not existing record in IZ
        bib = IzBib('991043825829705501', 'UBS', 'S', from_nz_mms_id=True)

        self.assertTrue(bib.error,
                        'No error when fetching a not existing record in IZ from a NZ MMS ID: 991043825829705501')

        # Test copy record in IZ
        bib = IzBib('991043825829705501', 'UBS', 'S', from_nz_mms_id=True, copy_nz_rec=True)

        self.assertFalse(bib.error,
                         'Error when copying a record from a NZ  to IZ: MMS ID 991043825829705501')

        IzBib('991043825829705501', 'UBS', 'S', from_nz_mms_id=True).delete()

    def test_get_holdings_and_items(self):
        # Get holdings
        hols = IzBib('991043825829705501', 'HPH', 'S', from_nz_mms_id=True).get_holdings()

        self.assertGreater(len(hols), 1, "Error, not at least two holdings found")

        # Get items
        items = hols[0].get_items()

        self.assertTrue('03124510' in items[0].barcode, "Error, barcode item should start with '03124510'")

    def test_get_from_barcode(self):

        # Get the data from NZ id of a not existing record in IZ
        item = Item(barcode='NOT_EXISTING_BARCODE', zone='HPH', env='S')

        self.assertTrue(item.error,
                        'No error when fetching a not existing barcode in IZ')

        # Test with an existing barcode
        item = Item(barcode='03124510', zone='HPH', env='S')

        self.assertFalse(item.error,
                         'Error when fetching an item by barcode')

        self.assertEqual(item.holding.bib.mms_id, '991000975799705520',
                         'MMS ID of the bib record is not "991000975799705520"')

    def test_duplicate_item(self):

        # Get the item data
        item1 = Item(barcode='03124510', zone='HPH', env='S')

        # Change barcode
        item1.barcode = '03124510_NEW'

        item2 = Item(holding=item1.holding, data=item1.data, create_item=True)

        self.assertFalse(item2.error, 'No error when duplicating an item in IZ')
        self.assertEqual(item2.barcode, '03124510_NEW', 'Barcode of the duplicated item is not "03124510_NEW"')

        Item(barcode='03124510_NEW', zone='HPH', env='S').delete()

    def test_change_library_item(self):
        # Get the item data
        item1 = Item(barcode='03124510', zone='HPH', env='S')

        # Change barcode
        item1.barcode = '03124510_NEW_2'
        item1.library = 'hph_bjnju'
        item1.location = 'bjnjudoc'

        hol1 = item1.holding
        hol1.library = 'hph_bjnju'
        hol1.location = 'bjnjudoc'

        hol2 = Holding(bib=item1.bib, data=hol1.data, create_holding=True)
        item2 = Item(holding=hol2, data=item1.data, create_item=True)

        self.assertFalse(item2.error, 'No error when duplicating an item in IZ')
        self.assertEqual(item2.barcode, '03124510_NEW_2', 'Barcode of the duplicated item is not "03124510_NEW_2"')

        Item(barcode='03124510_NEW_2', zone='HPH', env='S').holding.delete(force=True)

    def test_create_holding(self):
        # Get the item data
        holding1 = Holding('991000975799705520', '2234409340005520', 'HPH', 'S')

        # Duplicate holding
        holding2 = Holding(bib=holding1.bib, data=holding1.data, create_holding=True)

        self.assertEqual(holding2.data.find('.//datafield[@tag="852"]/subfield[@code="b"]').text, 'hph_bjnbe')

        # Delete duplicated holding
        holding2.delete()

    def test_update_bib_record(self):

        # Get some bib record
        bib = NzBib('991043825829705501', 'S')

        # Change the title
        bib.data.find('.//datafield[@tag="245"]/subfield[@code="a"]') \
                .text = 'Je ne veux plus de python pour mon anniversaire'

        bib.update()

        bib = NzBib('991043825829705501', 'S')
        title = bib.data.find('.//datafield[@tag="245"]/subfield[@code="a"]').text

        self.assertFalse(bib.error, 'No error when updating an item in NZ')
        self.assertEqual(title,
                         'Je ne veux plus de python pour mon anniversaire',
                         'Le titre ne correspond pas à la modification')

        # Load the original record from disk to restore the title
        data = XmlData(filepath='test/data/nz_record_orig.xml')
        bib = NzBib('991043825829705501', 'S', data=data)
        bib.update()

        # Check if the record have been updated
        bib = NzBib('991043825829705501', 'S')
        title = bib.data.find('.//datafield[@tag="245"]/subfield[@code="a"]').text

        self.assertFalse(bib.error, 'No error when updating an item in NZ')
        self.assertEqual(title,
                         'Je veux un python pour mon anniversaire',
                         'Original title not restored')

    @classmethod
    def tearDownClass(cls):
        IzBib('991043825829705501', 'UBS', 'S', from_nz_mms_id=True).delete()
        Item(barcode='03124510_NEW', zone='HPH', env='S').delete()
        item = Item(barcode='03124510_NEW_2', zone='HPH', env='S')
        if item.error is False:
            item.holding.delete(force=True)

        _ = [hol.delete() for hol in IzBib('991000975799705520', zone='HPH', env='S').get_holdings()
             if hol.holding_id != '2234409340005520']


if __name__ == '__main__':
    unittest.main()
