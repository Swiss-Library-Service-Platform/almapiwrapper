import unittest
from dateutil import parser
from datetime import timedelta
from almapiwrapper.users import User, NewUser, Loan, Request
from almapiwrapper.record import JsonData
from almapiwrapper.inventory import Item
from almapiwrapper import config_log
import os

config_log("test.log")

if os.getcwd().endswith('test'):
    os.chdir('..')

class TestRequest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        for primary_id in ['testRequestUser1',]:
            u = User(primary_id, 'UBS', 'S')

            if u.data is None:

                # Create new user
                data = JsonData(filepath=f'test/data/user_{primary_id}.json')

                user = NewUser('UBS', 'S', data).create()


        # Item('996259850105504', '22202377380005504', '23202377370005504', 'UBS', 'S').scan_in('A100', 'A100_KUR')
        # Item('9953896770105504', '22315547880005504', '23315547870005504', 'UBS', 'S').scan_in('A100', 'A100_KUR')

    def test_fetch_request(self):

        u = User('testRequestUser1', 'UBS', 'S')

        # Create new request
        req_data = JsonData(filepath=f'test/data/request_test1.json')
        _ = Request(zone='UBS', env='S', data=req_data).create()
        r = u.requests[0]
        self.assertFalse(r.error, 'Error during request creation')

        self.assertEqual(r.data['title'],
                         'The dot-com debacle and the return of reason Louis E.V. Nevaer',
                         'Request title mismatch')

    def test_create_request(self):
        req_data = JsonData(filepath=f'test/data/request_test2.json')
        _ = Request(zone='UBS', env='S', data=req_data).create()
        reqs = User('testRequestUser1', 'UBS', 'S').requests
        self.assertGreater(len(reqs), 0, 'No request found')
        for reqs in reqs:
            self.assertIn(reqs.data['title'],
                          ['The dot-com debacle and the return of reason Louis E.V. Nevaer',
                           'Marketing data science modeling techniques in predictive analytics with R and Python Thomas W. Miller'],
                          'Request title mismatch')

    def test_cancel_request(self):
        req_data = JsonData(filepath=f'test/data/request_test3.json')
        r = Request(zone='UBS', env='S', data=req_data).create()
        req_id = r.data['request_id']
        r.cancel()
        r = Request(request_id=req_id, user_id='testRequestUser1' , zone='UBS', env='S')
        self.assertEqual(r.data['request_status'], 'HISTORY', 'Request status mismatch')
        # print(r)


    @classmethod
    def tearDownClass(cls):
        for primary_id in ['testRequestUser1']:
            u = User(primary_id, 'UBS', 'S')
            u.delete()

if __name__ == '__main__':
    unittest.main()
