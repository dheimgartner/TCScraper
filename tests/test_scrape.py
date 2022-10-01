## https://docs.python.org/3/library/unittest.html
## https://code.visualstudio.com/docs/python/testing


import unittest

from tcsscraper import scrape as tcs


class TestTcsScraper(unittest.TestCase):

    def test_get_base_table(self):
        base_table = tcs.get_base_table(headless=True)
        self.assertTrue(base_table is not None)

    def test_get_similar_cars(self):
        similar_cars = tcs.get_similar_cars("SUV S", "Benzin", fuel_consumption=5, km=10e3, canton="AG", buffer=1)
        self.assertTrue(similar_cars is not None)



if __name__ == "__main__":
    unittest.main()




