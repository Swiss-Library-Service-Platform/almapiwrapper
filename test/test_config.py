import unittest
import sys
import os

from almapiwrapper.config import RecSet, NewLogicalSet, NewItemizedSet, Job, Reminder, fetch_reminders
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

class TestReminder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        if len(reminders) > 0:
            for r in reminders:
                r.delete()

        data = JsonData(filepath='test/data/reminder_test1.json')

        r = Reminder(zone='NZ', env='S', data=data, create_reminder=True)

    def test_get_reminder(self):
        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        self.assertEqual(len(reminders), 1, 'Not able to fetch the reminder')
        self.assertEqual(reminders[0].entity_id, '991170687152205501', 'Reminder linked to the wrong record')
        self.assertEqual(reminders[0].reminder_type, 'Additional edition',
                         'Bad reminder type, should be "Additional edition"')
        self.assertEqual(reminders[0].status, 'NEW', 'Bad reminder status, should be "NEW"')


    def test_delete_reminder(self):
        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        self.assertEqual(len(reminders), 1, 'Not able to fetch the reminder')
        self.assertEqual(reminders[0].entity_id, '991170687152205501', 'Reminder linked to the wrong record')
        reminders[0].delete()
        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        self.assertEqual(len(reminders), 0, 'Not able to delete the reminder')

        data = JsonData(filepath='test/data/reminder_test1.json')
        Reminder(zone='NZ', env='S', data=data, create_reminder=True)

    def test_update_reminder(self):
        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        self.assertEqual(len(reminders), 1, 'Not able to fetch the reminder')
        self.assertEqual(reminders[0].entity_id, '991170687152205501', 'Reminder linked to the wrong record')
        reminders[0].data['text'] = 'Test update'
        reminders[0].update()

        reminders = fetch_reminders(zone='NZ', env='S', entity_id='991170687152205501')
        self.assertEqual(len(reminders), 1, 'Not able to fetch the reminder')
        self.assertEqual(reminders[0].entity_id, '991170687152205501', 'Reminder linked to the wrong record')
        self.assertEqual(reminders[0].data['text'], 'Test update', 'Reminder not updated')


class TestRecSet(unittest.TestCase):

    def test_fetch_members_of_user_set(self):

        # Fetch set data
        s = RecSet('17866160420005504', 'UBS', 'S')
        members = s.get_members()

        self.assertEqual(len(members), s.get_members_number(), 'Not able to fetch all members')
        self.assertEqual(s.get_content_type(), 'USER', f'Bad type of content, should be "USER" '
                                                       f'and is "{s.get_content_type()}"')

    def test_fetch_members_of_bib_set(self):

        # Fetch set data (IEP is related to physical titles)
        s = RecSet('8020260160005504', 'UBS', 'S')
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

        instance = job.get_instance_info('17797121220005504')
        self.assertFalse(job.error, 'Not able to fetch a job instance')

        state = job.check_instance_state('17797121220005504')
        self.assertEqual(state['progress'], 100, 'Impossible to get instance info')
        self.assertEqual(state['status'], 'COMPLETED_SUCCESS', 'Impossible to get instance info')

        instances = job.get_instances()
        self.assertTrue(instances.content['total_record_count'] > 20)


if __name__ == '__main__':
    unittest.main()
