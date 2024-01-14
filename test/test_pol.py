import unittest
import sys
import os
import time
import pandas as pd

from almapiwrapper.acquisitions import POLine
from almapiwrapper.record import JsonData, XmlData
from almapiwrapper import config_log

config_log("test.log")
if os.getcwd().endswith('test'):
    os.chdir('..')

class TestPOLine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def test_update(self):
        pol =  POLine('POL-UBS-2023-113458', 'UBS', 'S')
        reclaim_interval = pol.data['reclaim_interval']
        if reclaim_interval == '60':
            pol.data['reclaim_interval'] = '30'
        else:
            pol.data['reclaim_interval'] = '60'
        reclaim_interval = pol.data['reclaim_interval']
        pol.update()

        self.assertEqual(pol.data['reclaim_interval'],
                         reclaim_interval,
                         f'POL reclaim interval should be {reclaim_interval}')


if __name__ == '__main__':
    unittest.main()
