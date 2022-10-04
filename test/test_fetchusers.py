import unittest
import time
from almapiwrapper.users import User, NewUser, fetch_users
from almapiwrapper.record import JsonData
from almapiwrapper import config_log

config_log("test.log")


class TestFetchUsers(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        u = User('TestUser4', 'UBS', 'S')
        if u.data is not None:
            u.delete()

    def test_find_user4(self):

        # Create new user
        data = JsonData(filepath='test/data/user_test4.json')
        u1 = NewUser('UBS', 'S', data).create()

        self.assertFalse(u1.error, 'Error in record after creating the user')
        time.sleep(3)
        users = fetch_users('primary_id~TestUser4', 'UBS', 'S')

        self.assertEqual(len(users), 1, "Nombre d'utilisateurs trouvés différent de 1")

        # Delete user
        u1.delete()

    def test_find_not_existing_user(self):

        users = fetch_users('primary_id~testUser_not_existing', 'UBS', 'S')
        self.assertEqual(len(users), 0, "Nombre d'utilisateurs trouvés différent de 0"
                                        "pour un utilisateur non existant")

    @classmethod
    def tearDownClass(cls):
        u = User('TestUser4', 'UBS', 'S')
        if u.data is not None:
            u.delete()


if __name__ == '__main__':
    unittest.main()
