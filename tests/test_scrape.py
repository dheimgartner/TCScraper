## https://docs.python.org/3/library/unittest.html
## https://code.visualstudio.com/docs/python/testing


import unittest

from tcsscraper import scrape as tcs
from tcsscraper.helper import Car


class TestTcsScraper(unittest.TestCase):

    def test_get_base_table(self):
        base_table = tcs.get_base_table(headless=True)
        self.assertTrue(base_table is not None)

    def test_get_cars(self):
        car = Car("SUV S", "Benzin", fuel_consumption=5)
        similar_cars = tcs.get_cars(car, km=10e3, canton="AG", similar={'flag': True, 'buffer': 1})
        self.assertTrue(similar_cars is not None)



if __name__ == "__main__":
    unittest.main()




