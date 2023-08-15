import unittest

from almapiwrapper.analytics import AnalyticsReport
from almapiwrapper.record import JsonData
from almapiwrapper import config_log

config_log("test.log")


class TestgetAnalyticsReport(unittest.TestCase):

    def test_get_analytics_report(self):

        report = AnalyticsReport('/shared/SLSP Network Zone 41SLSP_NETWORK/Reports/RRE/Almapiwrapper_test', 'NZ', 'P')


        # Check path
        self.assertEqual(report.path,
                         '/shared/SLSP Network Zone 41SLSP_NETWORK/Reports/RRE/Almapiwrapper_test',
                         'Path is not stored correctly')

        # Check report name
        self.assertEqual(report.report_name,
                         'Almapiwrapper_test')

        # Check content
        self.assertGreater(len(report.data), 6, 'Analytics report contains not enough data')
        self.assertEqual(report.data.iloc[0, 0],
                         '41SLSP_NETWORK',
                         'Analytics report contains not the expected data (41SLSP_NETWORK')


if __name__ == '__main__':
    unittest.main()
