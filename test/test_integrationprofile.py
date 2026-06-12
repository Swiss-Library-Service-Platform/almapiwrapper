import unittest
from almapiwrapper.config import IntegrationProfile, fetch_integration_profiles

class TestIntegrationProfile(unittest.TestCase):
    def setUp(self):
        pass

    def test_fetch_integration_profiles(self):

        profiles = fetch_integration_profiles('NZ', env='S')
        self.assertGreater(len(profiles), 10)

    @unittest.skip("Test skipped to avoid creating multiple copies of the same profile")
    def test_copy_integration_profile(self):
        int_prof = IntegrationProfile('90795366970005501', 'NZ', 'S')
        int_prof.data['code'] = 'TEST_SLSP_STAFF_TEMP'
        int_prof.data['name'] = 'TEST_SLSP_STAFF_TEMP'
        int_prof_copy = IntegrationProfile(data=int_prof.data, zone='NZ' , env='S').create()
        prof_id = int_prof_copy.profile_id
        self.assertEqual(IntegrationProfile(prof_id, 'NZ', 'S').data['code'], 'TEST_SLSP_STAFF_TEMP')

    def test_update_integration_profile(self):
        int_prof = IntegrationProfile('112022830000231', 'NZ', 'S')
        int_prof.data['name'] = 'TEST'
        int_prof.update()
        int_prof = IntegrationProfile('112022830000231', 'NZ', 'S')
        self.assertEqual(int_prof.data['name'], 'TEST')
        int_prof.data['name'] = 'OASIS NEW ORDER API'
        int_prof.update()
        int_prof = IntegrationProfile('112022830000231', 'NZ', 'S')
        self.assertEqual(int_prof.data['name'], 'OASIS NEW ORDER API')


if __name__ == '__main__':
    unittest.main()



