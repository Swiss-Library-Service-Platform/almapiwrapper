import unittest
from almapiwrapper import config_log
config_log("test.log")

from almapiwrapper.inventory.collection import fetch_collections

class TestFetchCollections(unittest.TestCase):
    def test_fetch_collections_1(self):
        collections = fetch_collections(zone='UBS', env='S')
        self.assertTrue(20 > len(collections) > 5)
        collection = collections[4]['collection']
        self.assertEqual(collection.zone, 'UBS')

    def test_fetch_collections_2(self):
        collections = fetch_collections(zone='UBS', env='S', level=10)
        nb = 0
        for col1 in collections:
            nb += 1
            for col2 in col1['children']:
                nb += 1
                for col3 in col2['children']:
                    nb += 1
                    for col4 in col3['children']:
                        nb += 1
                        for col5 in col4['children']:
                            nb += 1

        self.assertTrue(150 > nb > 100)
        collection = collections[4]
        self.assertEqual(collection['collection'].zone, 'UBS')


if __name__ == '__main__':
    unittest.main()

