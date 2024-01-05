import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.config import RecSet, NewLogicalSet, NewItemizedSet, Job, Reminder, fetch_reminders
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

class TestNewLogicalSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        RecSet(name='TEST_RRE_123', zone='NZ', env='S').delete()
        RecSet(name='TEST_RRE_123b', zone='NZ', env='S').delete()

    def test_create(self):
        s1 = NewLogicalSet('NZ',
                       'S',
                       'TEST_RRE_123',
                       'TEST_RRE_123',
                       'BIB_MMS where BIB_MMS ((all CONTAIN "991082448539705501"))',
                       'raphael.rey@slsp.ch',
                       True)
        s1 = s1.create()
        self.assertEqual(type(s1).__name__, 'LogicalSet')
        members = s1.get_members()

        self.assertEqual(len(members), 1, f'It should one member, {len(members)} available')

        self.assertEqual(s1.get_content_type(),
                         'BIB_MMS',
                         f'Content type should be "BIB_MMS", it is {s1.get_content_type()}.')

        s2 = RecSet(name='TEST_RRE_123', zone='NZ', env='S')

        members = s2.get_members()

        self.assertEqual(len(members), 1, f'It should one member, {len(members)} available')

        s2.delete()

    def test_create_2(self):
        data = XmlData(filepath='test/data/set_NZ_TEST_RRE_123b1.xml')
        s1 = NewLogicalSet('NZ',
                           'S',
                           data=data)
        s1 = s1.create()
        self.assertEqual(type(s1).__name__, 'LogicalSet')

        members = s1.get_members()

        self.assertEqual(len(members), 1, f'It should one member, {len(members)} available')


class TestNewItemizedSet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s1 = RecSet(zone='NZ',
                    env='S',
                    name='TEST_RRE_1234')
        s1.delete()
        s2 = RecSet(zone='NZ',
                    env='S',
                    name='TEST_RRE_1234_itemized')
        s2.delete()
        s3 = RecSet(zone='NZ',
                    env='S',
                    name='TEST_RRE_123456_itemized')
        s3.delete()


    def test_create(self):

        # Create a logical set
        s1 = NewLogicalSet('NZ',
                           'S',
                           'TEST_RRE_1234',
                           'TEST_RRE_123',
                           'BIB_MMS where BIB_MMS ((all CONTAIN "991082448539705501"))',
                           'raphael.rey@slsp.ch',
                           True)
        s1 = s1.create()
        self.assertEqual(type(s1).__name__, 'LogicalSet')
        members = s1.get_members()

        self.assertEqual(len(members), 1, f'It should one member, {len(members)} available')

        self.assertEqual(s1.get_content_type(),
                         'BIB_MMS',
                         f'Content type should be "BIB_MMS", it is {s1.get_content_type()}.')

        # Create an itemized set from a logical set
        s2 = NewItemizedSet(zone='NZ', env='S', from_logical_set=s1)
        s3 = s2.create()
        time.sleep(4)
        self.assertEqual(type(s3).__name__, 'ItemizedSet')

        members_2 = s3.get_members()

        self.assertEqual(len(members_2), 1, f'It should one member, {len(members_2)} available')

        self.assertEqual(s3.get_content_type(),
                         'BIB_MMS',
                         f'Content type should be "BIB_MMS", it is {s3.get_content_type()}.')

        s3.add_members(['991125596919705501'])
        members_3 = s3.get_members()

        self.assertEqual(len(members_3), 2, f'It should one member, {len(members_3)} available')

        s1.delete()
        s3.delete()

    def test_create_empty(self):
        # Create an empty itemized set
        s1 = NewItemizedSet(zone='NZ', env='S', content='BIB_MMS', name='TEST_RRE_123456_itemized')
        s1 = s1.create()

        mms_ids = ['991090586569705501', '991125596919705501']
        # mms_ids = pd.read_csv('test/data/recset_test_mms_ids.csv', dtype=str)['MMS ID'].tolist()
        s1.add_members(mms_ids, fail_on_invalid_id=False)

        s2 = RecSet(zone='NZ',
                    env='S',
                    name='TEST_RRE_123456_itemized')
        members = s2.get_members()
        self.assertEqual(len(members), len(mms_ids), f'It should {len(mms_ids)} members, {len(members)} available')

        s1.delete()


if __name__ == '__main__':
    unittest.main()
