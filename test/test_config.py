import unittest
import shutil
import os
from datetime import date, timedelta

from almapiwrapper.config import (RecSet, NewLogicalSet, NewItemizedSet, Job, Reminder,
                                  fetch_reminders, fetch_libraries, Library, Location, Desk, Department)
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log
from config.library import Department, fetch_departments

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

        instances = job.get_instances()
        instance = instances.content['job_instance'][0]

        self.assertFalse(job.error, 'Not able to fetch a job instance')

        state = job.check_instance_state(instance['id'])
        self.assertEqual(state['progress'], 100, 'Impossible to get instance info')
        self.assertEqual(state['status'], 'COMPLETED_SUCCESS', 'Impossible to get instance info')

        instances = job.get_instances()
        self.assertTrue(instances.content['total_record_count'] > 20)


class TestLibrary(unittest.TestCase):

    def test_fetch_libraries(self):
        libraries = fetch_libraries(zone='UBS', env='S')
        self.assertTrue(len(libraries) > 10, 'No libraries found')
        self.assertEqual(libraries[20].data['code'], libraries[20].code, 'Library object corrupted')

    def test_get_library(self):
        lib = Library('A100', 'UBS', 'S')
        self.assertEqual(lib.data['code'], 'A100', 'Library object corrupted')
        self.assertEqual(lib.data['name'], 'Basel - UB Hauptbibliothek', 'Library name not correct')

    def test_departments(self):
        lib = Library('A100', 'UBS', 'S')
        departments = lib.departments
        self.assertTrue(len(departments) > 0, 'No departments found')
        self.assertEqual(departments[0].data['code'], departments[0].code, 'Department object corrupted')
        self.assertEqual(departments[0].data['owner']['value'], 'A100', 'Department linked to the wrong library')

    def test_get_departments(self):
        lib = Library('A191', 'UBS', 'S')
        departments = lib.departments
        self.assertTrue(len(departments) > 0, 'No departments found')
        self.assertEqual(departments[0].data['type']['value'], 'AcqWorkOrder')


class TestLocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        loc = Location('UBS', 'A100', '100FH', 'S')
        if loc.fulfillment_unit != 'IZ_Glob_OS':
            loc.fulfillment_unit = 'IZ_Glob_OS'
            loc.update()

    def test_fetch_locations(self):
        lib = Library('A100', 'UBS', 'S')
        locations = lib.locations
        self.assertTrue(len(locations) > 10, 'No locations found')
        self.assertEqual(locations[20].data['code'], locations[20].code, 'Location object corrupted')

    def test_get_location(self):
        loc1 = Location('UBS', 'A100', '100FH', 'S')
        self.assertEqual(loc1.data['code'], '100FH', 'Location object corrupted')
        self.assertEqual(loc1.fulfillment_unit, 'IZ_Glob_OS', 'fulfillment unit should be "IZ_Glob_OS"')
        loc1.fulfillment_unit = 'IZ_ClosLib'
        loc1.update()
        loc2 = Location('UBS', 'A100', '100FH', 'S')
        self.assertEqual(loc2.fulfillment_unit, 'IZ_ClosLib', 'fulfillment unit should be "IZ_ClosLib"')

    def test_create_location(self):
        loc1 = Location('UBS', 'A100', '100FH', 'S')
        loc1.data['name'] = 'new test loc A100'
        loc1.data['external_name'] = 'new test loc A100'
        loc1.data['code'] = 'newlocA100'

        loc2 = Location('UBS', 'A100', env='S', data=loc1.data)
        _ = loc2.data

        loc2.create()

        loc3 = Location('UBS', 'A100', code='newlocA100', env='S')
        _ = loc3.data

        self.assertFalse(loc2.error, 'error when creating new location')
        self.assertFalse(loc3.error, 'error when fetching new location data')

        loc3.delete()
        loc3 = Location('UBS', 'A100', code='newlocA100', env='S')
        _ = loc3.data
        self.assertTrue(loc3.error, 'location should not exist anymore')

    @classmethod
    def tearDownClass(cls):
        loc = Location('UBS', 'A100', '100FH', 'S')
        loc.fulfillment_unit = 'IZ_Glob_OS'
        loc.update()


class TestOpenHours(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass
        # loc = Location('UBS', 'A100', '100FH', 'S')
        # cls.oh = loc.open_hours

    def test_get_open_hours(self):
        lib = Library('A100', 'UBS', 'S')

        self.assertTrue(len(lib.open_hours.data['open_hour']) > 0, 'No open hours found')
        self.assertTrue('Silvester' in lib.open_hours.data['open_hour'][-1]['desc'], 'Sylvester must be last exception')

    def test_update_open_hours(self):
        new_open_hours = {
            "type": {
                "value": "EXCEPTION",
                "desc": "Exception"
            },
            "inherited": False,
            "desc": "test_exception",
            "from_date": f"{date.today()}Z",
            "to_date": f"{date.today() + timedelta(days=3)}Z",
            "from_hour": "00:00",
            "to_hour": "23:59",
            "status": {
                "value": "CLOSE",
                "desc": "Closed"
            }
        }
        lib1 = Library('A100', 'UBS', 'S')
        lib1.open_hours.data['open_hour'].append(new_open_hours)
        lib1.open_hours.update()
        self.assertEqual(lib1.open_hours.data['open_hour'][-1]['desc'],
                         'test_exception',
                         'Open hours object not updated')

        lib2 = Library('A100', 'UBS', 'S')
        is_test_exception = False
        for oh in lib2.open_hours.data['open_hour']:
            if oh['desc'] == 'test_exception':
                is_test_exception = True

        self.assertTrue(is_test_exception, 'Test exception not found')

        lib2.open_hours.data['open_hour'] = [oh for oh in lib2.open_hours.data['open_hour']
                                             if oh['desc'] != 'test_exception' or '2025' in oh['from_date']]

        lib2.open_hours.update()

        lib3 = Library('A100', 'UBS', 'S')
        is_test_exception = False
        for oh in lib3.open_hours.data['open_hour']:
            if oh['desc'] == 'test_exception':
                is_test_exception = True
        self.assertFalse(is_test_exception, 'Test exception not deleted')

    @classmethod
    def tearDownClass(cls):
        pass

class TestDesk(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_get_desk(self):
        desk1 = Desk('UBS', 'A100', 'A100_KUR', 'S')
        self.assertEqual(desk1.data['code'], desk1.code, 'Desk object corrupted')

        locations = desk1.get_locations()
        self.assertGreater(len(locations), 10, 'There should be more than 10 locations')

        location = next((loc for loc in locations if loc.code == '100FH'), locations[0])

        self.assertEqual(location.data['accession_placement']['value'],
                         '852j',
                         'accession_placement should be 852j')

    @classmethod
    def tearDownClass(cls):
        pass

class TestConfigLog(unittest.TestCase):
    @classmethod
    def setUp(cls):
        if os.path.exists('logs'):
            shutil.rmtree('logs', ignore_errors=True)
        if os.path.exists('log/custom_test_log.txt'):
            os.remove('log/custom_test_log.txt')

    def test_log_config(self):
        import logging
        log_file = "custom_test_log.txt"
        config_log(log_file)
        logging.info("Test log message")

        self.assertTrue(os.path.isfile(os.path.join('log', log_file)), f"Log file was not created: {log_file}")

        log_file = "logs/custom_test_log.txt"
        config_log(log_file)
        logging.info("Test log message")

        self.assertTrue(os.path.isfile(os.path.join(log_file)), f"Log file was not created: {log_file}")

        config_log("test.log")

    @classmethod
    def tearDown(cls):
        if os.path.exists('logs'):
            shutil.rmtree('logs', ignore_errors=True)
        if os.path.exists('log/custom_test_log.txt'):
            os.remove('log/custom_test_log.txt')

class TestDepartment(unittest.TestCase):
    @classmethod
    def setUp(cls):
        pass

    def test_get_department_1(self):
        department = Department(library_code='A100', code='AcqDeptA100', zone='UBS', env='S')
        self.assertEqual(department.data['owner']['value'], 'A100')
        self.assertEqual(department.dep_type, 'AcqWorkOrder')

    def test_get_department_2(self):
        department = Department(library_code='A100', code='AcqDeptA100_bad', zone='UBS', env='S')
        _ = department.data
        self.assertTrue(department.error)

    def test_get_department_3(self):
        department = Department(code='WOTD-IZ3-01', zone='UBS', env='S')
        _ = department.data
        self.assertEqual(department.data['owner']['value'], '41SLSP_UBS')
        self.assertEqual(department.dep_type, 'WOT-IZ3-01')

    def test_fetch_department_1(self):
        departments = fetch_departments(zone='UBS', env='S', library_code='A100')
        for department in departments:
            self.assertEqual(department.library_code, 'A100')
        self.assertGreater(len(departments), 0, 'There should be more than 0 departments')

    def test_fetch_department_2(self):
        departments = fetch_departments(zone='UBS', env='S')
        for department in departments:
            self.assertEqual(department.library_code, 'INST')
        self.assertGreater(len(departments), 0, 'There should be more than 0 departments')



if __name__ == '__main__':
    unittest.main()
