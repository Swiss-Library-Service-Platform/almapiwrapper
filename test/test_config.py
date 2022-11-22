import unittest
import sys
import os

from almapiwrapper.users import User, NewUser
from almapiwrapper.config import RecSet
from almapiwrapper.record import JsonData
from almapiwrapper import config_log

config_log("test.log")


class TestRecSet(unittest.TestCase):

    def test_fetch_members_of_user_set(self):

        # Fetch set data
        s = RecSet('12901610260005504', 'UBS', 'S')
        members = s.get_members()

        self.assertEqual(len(members), s.get_members_number(), 'Not able to fetch all members')
        self.assertEqual(s.get_content_type(), 'USER', f'Bad type of content, should be "USER" '
                                                       f'and is "{s.get_content_type()}"')

    def test_fetch_members_of_bib_set(self):

        # Fetch set data
        s = RecSet('12901610390005504', 'UBS', 'S')
        members = s.get_members()

        self.assertEqual(len(members), s.get_members_number(), 'Not able to fetch all members')
        self.assertEqual(s.get_content_type(), 'IEP', f'Bad type of content, should be "IEP" '
                                                      f'and is "{s.get_content_type()}"')


if __name__ == '__main__':
    unittest.main()
