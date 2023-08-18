import unittest

from almapiwrapper.users import User, NewUser, Loan
from almapiwrapper.record import JsonData
from almapiwrapper.inventory import Item
from almapiwrapper import config_log
import os

config_log("test.log")

if os.getcwd().endswith('test'):
    os.chdir('..')

class TestCreateUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        for primary_id in ['testLoanUser1', 'testLoanUser2']:
            u = User(primary_id, 'UBS', 'S')

            if u.data is None:

                # Create new user
                data = JsonData(filepath=f'test/data/user_{primary_id}.json')
                _ = NewUser('UBS', 'S', data).create()

        Item('996259850105504', '22202377380005504', '23202377370005504', 'UBS', 'S').scan_in('A100', 'A100_KUR')

    def test_create_loan(self):

        u = User('testLoanUser1', 'UBS', 'S')

        # Create new loan
        loan = u.create_loan('A100', 'A100_KUR', '0UBU0536413')
        self.assertFalse(u.error, 'Error during loan creation')

        self.assertEqual(u.loans[0].data['loan_id'], loan.data['loan_id'], 'Loan ID mismatch')

    def test_scan_in(self):
        u = User('testLoanUser1', 'UBS', 'S')

        # Create new loan
        loan1 = u.create_loan('A100', 'A100_KUR', '0UBU0536413')
        self.assertEqual(loan1.data['loan_status'], 'ACTIVE', 'Loan status should be ACTIVE')

        item = loan1.item.scan_in('A100', 'A100_KUR')
        self.assertEqual(item.barcode, '0UBU0536413', 'Item status should be LOAN')

        loan2 = Loan(loan1.data['loan_id'], user=u)
        self.assertEqual(loan2.data['loan_status'], 'COMPLETE', 'Loan status should be COMPLETE')

    def test_loan_error(self):
        u1 = User('testLoanUser1', 'UBS', 'S')
        loan1 = u1.create_loan('A100', 'A100_KUR', '0UBU0536413')
        self.assertFalse(u1.error, 'Unexpected error during loan creation')
        self.assertIsNotNone(loan1, 'Loan should not be None')

        u2 = User('testLoanUser2', 'UBS', 'S')
        loan2 = u2.create_loan('A100', 'A100_KUR', '0UBU0536413')
        self.assertTrue(u2.error, 'No expected error during loan creation of already loaned item')
        self.assertIsNone(loan2, 'Loan should be None')

    @classmethod
    def tearDownClass(cls):
        for primary_id in ['testLoanUser1', 'testLoanUser2']:
            u = User(primary_id, 'UBS', 'S')
            if u.data is not None:
                for loan in u.loans:
                    loan.item.scan_in('A100', 'A100_KUR')
                u.delete()

if __name__ == '__main__':
    unittest.main()
