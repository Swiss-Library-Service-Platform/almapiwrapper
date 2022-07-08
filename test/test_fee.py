import unittest
import sys
import os

from almapiwrapper.users import User, NewUser, Fee
from almapiwrapper.record import JsonData
from almapiwrapper import config_log

config_log("test.log")


class TestCreateUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        u = User('TestFeeUser1', 'UBS', 'S')

        if u.data is None:
            # Create new user
            data = JsonData(filepath='test/data/user_testFeeUser1.json')
            u = NewUser('UBS', 'S', data).create()

    def test_create_fee(self):

        u = User('TestFeeUser1', 'UBS', 'S')

        # Create new fee
        data = JsonData(filepath='test/data/fee_test1.json')
        f1 = Fee(user=u, data=data, create_fee=True)

        self.assertFalse(f1.error, 'Error during fee creation')
        self.assertNotEqual(len(u.fees), 0, 'No fee created')

        # Check amount of the fee
        f2 = Fee(user=u, fee_id=f1.fee_id)
        self.assertEqual(f2.data['balance'], 20, 'Amount should be "20.0"')

        # pay the fee
        f2.operate('pay')
        self.assertEqual(f2.data['status']['value'], 'CLOSED', 'Unable to pay the fine')

    @classmethod
    def tearDownClass(cls):
        u = User('TestFeeUser1', 'UBS', 'S')
        if u.data is not None:
            for fee in u.fees:
                fee.operate('waive')
            u.delete()


if __name__ == '__main__':
    unittest.main()
