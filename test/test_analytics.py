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

    def test_get_analytics_report_with_filter(self):
        f = '''<sawx:expr xsi:type="sawx:comparison" op="equal"
                xmlns:saw="com.siebel.analytics.web/report/v1.1" 
                xmlns:sawx="com.siebel.analytics.web/expression/v1.1" 
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
                xmlns:xsd="http://www.w3.org/2001/XMLSchema">
                  <sawx:expr xsi:type="sawx:sqlExpression">"Title Creation Date"."Title Creation Year"</sawx:expr>
                  <sawx:expr xsi:type="xsd:string">2023</sawx:expr>
               </sawx:expr>'''
        report = AnalyticsReport('/shared/SLSP Network Zone 41SLSP_NETWORK/Reports/RRE/Almapiwrapper_filter_test', 'NZ', 'P', filter_to_apply=f)

        # Check path
        self.assertEqual(report.path,
                         '/shared/SLSP Network Zone 41SLSP_NETWORK/Reports/RRE/Almapiwrapper_filter_test',
                         'Path is not stored correctly')

        # Check report name
        self.assertEqual(report.report_name,
                         'Almapiwrapper_filter_test')

        # Check content
        self.assertEqual(len(report.data), 1, 'Analytics report should contain 1 row')
        self.assertEqual(report.data.iloc[0, 0],
                         '41SLSP_NETWORK',
                         'Analytics report contains not the expected data (41SLSP_NETWORK')


if __name__ == '__main__':
    unittest.main()
