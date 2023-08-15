import unittest

from almapiwrapper.users import User, NewUser, force_synchro
from almapiwrapper.record import JsonData
from almapiwrapper import config_log
import os

config_log("test.log")

if os.getcwd().endswith('test'):
    os.chdir('..')

class TestCreateUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        u = User('TestUser1', 'UBS', 'S')
        if u.data is not None:
            u.delete()

        u = User('TestUser2', 'UBS', 'S')
        if u.data is not None:
            u.delete()

        u = User('TestUser3', 'UBS', 'S')
        if u.data is not None:
            u.delete()

        u = User('TestUser5', 'UBS', 'S')
        if u.data is not None:
            u.delete()

        u = User('TestLoanUser3', 'NZ', 'S')
        if u.data is not None:
            u.delete()

        u = User('TestLoanUser3', 'UBS', 'S')
        if u.data is not None:
            u.delete()

    def test_create_user1(self):

        # Create new user
        data = JsonData(filepath='test/data/user_test1.json')
        u = NewUser('UBS', 'S', data)

        self.assertEqual(u.primary_id, 'TestUser1', 'Bad primary ID')
        self.assertIsNotNone(u.data, 'Unable to load json data')
        self.assertFalse(u.error, 'Error in record before creating the user')

        u = u.create()

        self.assertFalse(u.error, 'Error in record after creating the user')

        # Delete user
        u.delete()

    def test_duplicated_create_user2(self):

        # Create new user
        data = JsonData(filepath='test/data/user_test2.json')
        u1 = NewUser('UBS', 'S', data)
        u1 = u1.create()
        self.assertFalse(u1.error, 'duplicated record creation: error in first user')

        u2 = NewUser('UBS', 'S', data)
        u2 = u2.create()
        self.assertTrue(u2.error, 'duplicated record creation: no error in second user')

        u1.delete()
        self.assertFalse(u1.error, 'Error existing after deleting user')

    def test_duplicated_update_user3(self):

        # Create new user
        data = JsonData(filepath='test/data/user_test3.json')
        u1 = NewUser('UBS', 'S', data)
        u1 = u1.create()
        self.assertFalse(u1.error, 'error during user creation')

        u1 = User('TestUser3', 'UBS', 'S')
        u1.set_password('123new_pw123').update()
        self.assertFalse(u1.error, 'unable to update password')

        u1.delete()
        self.assertFalse(u1.error, 'Error existing after deleting user')

    def test_fetch_not_existing_record(self):
        # Fetch not existing user
        u = User('TestUser_not_existing', 'UBS', 'S')
        self.assertIsNone(u.data, 'Unable to fetch data with api of a not existing record')
        self.assertTrue(u.error, 'No error when fetching not existing user')

    def test_synchro_note(self):
        # Create new user
        data = JsonData(filepath='test/data/user_test5.json')
        u = NewUser('UBS', 'S', data).create()

        self.assertFalse(u.check_synchro_note(), 'User has already synchronization note')
        u.add_synchro_note()

        u = User('TestUser5', 'UBS', 'S')
        self.assertTrue(u.check_synchro_note(), 'User has no synchronization note')

        u.remove_synchro_note()

        u = User('TestUser5', 'UBS', 'S')
        self.assertFalse(u.check_synchro_note(), 'User has still a synchronization note')

        u.delete()

    def test_force_synchro(self):
        # Create new user
        data = JsonData(filepath='test/data/user_testLoanUser3.json')
        _ = NewUser('NZ', 'S', data).create()
        iz_u = User('TestLoanUser3', 'UBS', 'S')
        nz_u = User('TestLoanUser3', 'NZ', 'S')

        _ = iz_u.data
        _ = nz_u.data

        force_synchro(nz_u)
        self.assertTrue(User('TestLoanUser3', 'UBS', 'S').data['user_group']['value'] == '01',
                         'User has bad user group after force synchro')

        iz_u.data['user_group']['value'] = '02'
        iz_u.data['user_note'].append({
                                      "note_type": {
                                        "value": "OTHER",
                                        "desc": "Other"
                                      },
                                          "note_text": "User 7500000000007@eduid.ch has been merged to this user",
                                          "user_viewable": False,
                                          "popup_note": False,
                                          "created_by": "System",
                                          "created_date": "2023-05-31T05:44:15.264Z",
                                          "segment_type": "Internal"
                                      })
        iz_u.update(override=['user_group'])
        nz_u.data['user_note'].append({
                                      "note_type": {
                                        "value": "OTHER",
                                        "desc": "Other"
                                      },
                                      "note_text": "Registration Info: Initial registration via IZ hesso.",
                                      "user_viewable": False,
                                      "popup_note": False,
                                      "created_by": "registration.slsp.ch",
                                      "created_date": "2022-12-08T01:43:45Z",
                                      "segment_type": "External"
                                    })
        nz_u.update()
        force_synchro(nz_u)
        iz_u = User('TestLoanUser3', 'UBS', 'S')
        nz_u = User('TestLoanUser3', 'NZ', 'S')
        _ = iz_u.data
        _ = nz_u.data

        self.assertTrue(iz_u.data['user_group']['value'] == '01',
                         'User has bad user group after force synchro')
        self.assertTrue(len(iz_u.data['user_note']) == 2,
                         'IZ user should have 2 notes after force synchro')

        iz_u.delete()
        nz_u.delete()

    @classmethod
    def tearDownClass(cls):
        u = User('TestUser', 'UBS', 'S')
        if u.data is not None:
            u.delete()


if __name__ == '__main__':
    unittest.main()
