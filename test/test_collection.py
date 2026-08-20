import unittest
from almapiwrapper import config_log
config_log("test.log")

from almapiwrapper.inventory.collection import Collection, fetch_collections

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

class TestCollection(unittest.TestCase):
    def test_collection(self):
        collection = Collection('81390314220005504', 'UBS', 'S')
        self.assertEqual(collection.zone, 'UBS')
        data = collection.data
        data['library']['value'] = 'A100'
        data['name'] = 'Test Collection'
        collection_copy = Collection(data=data, zone='UBS', env='S').create()
        self.assertEqual(collection_copy.data['library']['value'], 'A100')
        collection_copy.delete()
        self.assertFalse(collection_copy.error)

if __name__ == '__main__':
    unittest.main()

