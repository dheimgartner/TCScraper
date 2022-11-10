## https://docs.python.org/3/library/unittest.html
## https://code.visualstudio.com/docs/python/testing

## e.g. run with python -m unittest -v tests.test_scrape.TestTcsScraper.test_get_cars

import unittest

from tcsscraper import scrape as tcs
from tcsscraper.helper import Car


class TestTcsScraper(unittest.TestCase):
    def test_get_base_table(self):
        base_table = tcs.get_base_table(headless=True)
        self.assertTrue(base_table is not None)

    def test_get_cars(self):
        car = Car("Mittelklasse", "Benzin", fuel_consumption=2)
        similar_cars = tcs.get_cars(
            car, km=10e3, canton="AG", similar={"flag": True, "buffer": 5}
        )
        self.assertTrue(similar_cars is not None)

    def test_buffer(self):
        car = Car("Luxusklasse", "Benzin", fuel_consumption=8)
        init = 1
        max_buffer = 2
        while init < max_buffer + 1:
            try:
                sc = tcs.get_cars(
                    car,
                    15e3,
                    "AI",
                    similar={"flag": True, "buffer": init},
                    verbose=False,
                    headless=False,
                )
            except Exception:
                init += 1
                continue
        self.assertTrue(sc is not None)


if __name__ == "__main__":
    unittest.main()
