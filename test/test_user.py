import unittest
import sys
import os

from almapiwrapper.users import User, NewUser
from almapiwrapper.record import JsonData
from almapiwrapper import config_log

config_log("test.log")


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

    @classmethod
    def tearDownClass(cls):
        u = User('TestUser', 'UBS', 'S')
        if u.data is not None:
            u.delete()


if __name__ == '__main__':
    unittest.main()