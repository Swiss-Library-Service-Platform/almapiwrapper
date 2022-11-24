import unittest
import sys
import os

from almapiwrapper.users import User, NewUser
from almapiwrapper.config import RecSet, Job
from almapiwrapper.record import JsonData, XmlData
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

    @unittest.skip
    def test_run_job(self):

        parameters = XmlData(filepath='test/data/config_job_parameters1.xml')

        job = Job('44', 'UBS', 'S')
        result = job.run(parameters)
        self.assertIsNotNone(result, "No return value when starting the job")
        self.assertFalse(job.error, 'The job cannot be started')
        self.assertIsNotNone(job.instance_id, "A job ID doesn't exist")

        instance = job.get_instance_info()
        self.assertIsNotNone(instance, "A job instance cannot be retrieved")

    def test_monitor_job(self):
        job = Job('44', 'UBS', 'S')

        instance = job.get_instance_info('12901746310005504')
        self.assertFalse(job.error, 'Not able to fetch a job instance')

        state = job.check_instance_state('12901746310005504')
        self.assertEqual(state['progress'], 100, 'Impossible to get instance info')
        self.assertEqual(state['status'], 'COMPLETED_SUCCESS', 'Impossible to get instance info')

        instances = job.get_instances()
        self.assertTrue(instances.content['total_record_count'] > 50)


if __name__ == '__main__':
    unittest.main()
