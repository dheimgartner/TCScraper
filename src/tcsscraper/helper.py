from argparse import Action
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import time



SLIDER_MIN = 5e3
SLIDER_MAX = 50e3
SLIDER_START = 15e3
SLEEP = 0.5



class EndOfTable:
    __benchmark = None

    def __init__(self, driver):
        self.driver = driver
    
    def tick(self, verbose=False):
        if verbose:
            print("Scrolling table...")
        
        xpath = "//div[@id='cars']//tr[last()]"
        compare = self.driver.find_element(By.XPATH, xpath).text
        if compare == self.__benchmark:
            return 1
        else:
            self.__benchmark = compare
            return 0



def load_dynamic_table(driver, sleep=SLEEP, verbose=False):
    end = EndOfTable(driver)
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep)
        if end.tick(verbose=verbose) == 1:
            break



def set_up_driver(headless=True, maximize=False):
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")

    driver = webdriver.Firefox(options=options)
    
    try:
        if maximize:
            driver.maximize_window()
        base_url = "https://www.verbrauchskatalog.ch/index.php"
        driver.get(base_url)

    except Exception as e:
        print(e)
        return None

    return driver



def scrape_table_rows(table_rows):
    rows = []
    for r in table_rows:
        cells = r.find_elements(By.CSS_SELECTOR, "td")
        row = [c.text for c in cells]
        rows.append(row)
    
    return {"elements": table_rows, "rows": rows}



class Car:
    vehicle_classes = [
        "Mikroklasse", 
        "Kleinwagen",
        "Untere Mittelklasse",
        "Mittelklasse",
        "Obere Mittelklasse",
        "Luxusklasse",
        "Coupé / Sportwagen",
        "Cabriolet / Roadster",
        "SUV S",
        "SUV M",
        "SUV L",
        "SUV XL",
        "Minivan S",
        "Minivan M",
        "Minivan L"
        ]

    fuel_types = [
        "Benzin",
        "Diesel",
        "Hybrid Benzin",
        "Hybrid Diesel",
        "Erdgas (CNG)",
        "Elektro",
        "Elektro mit Range Extender",
        "Plug-in Hybrid Benzin",
        "Plug-in Hybrid Diesel",
        "Wasserstoff / Elektro"
        ]

    def __init__(self, vehicle_class, fuel_type, fuel_consumption):
        if vehicle_class not in self.vehicle_classes:
            raise Exception("vehicle_class must be one of {}".format(Car.vehicle_classes))

        if fuel_type not in self.fuel_types:
            raise Exception("fuel_type must be one of {}".format(Car.fuel_types))
        
        self.vehicle_class, self.fuel_type, self.fuel_consumption = vehicle_class, fuel_type, fuel_consumption

    def __str__(self):
        return '{:<17} {}\n{:<17} {}\n{:<17} {}'.format('vehicle_type:', self.vehicle_class, 'fuel_type:', self.fuel_type, 'fuel_consumption:', self.fuel_consumption)


class Slider:
    """Acts on handle
    """

    def __init__(self, driver, slider_handle, step_size=[5, 1e3], min=SLIDER_MIN, max=SLIDER_MAX, position=SLIDER_START):
        """Manipulate slider object

        Args:
            driver: Selenium driver
            slider_handle: Slider handle object
            step_size (list, optional): 5 pix == 1000km. Defaults to [5, 1e3].
            min (int, optional): Slider lower bound. Defaults to SLIDER_MIN.
            max (int, optional): Slider upper bound. Defaults to SLIDER_MAX.
            position(int, optional): Current position of the slider. Defaults to SLIDER_START.
        """
        self.driver, self.slider_handle, self.step_size, self.min, self.max, self.position = driver, slider_handle, step_size, min, max, position
    
    def compute_offset(self, target):
        if target < self.min:
            raise Exception("Target < min of slider range")
        diff = target - self.position
        step = int(diff / self.step_size[1])
        offset = step * self.step_size[0]
        return offset
    
    def drag_and_drop_by_offset(self, x):
        ## by pixels...
        ActionChains(self.driver).drag_and_drop_by_offset(self.slider_handle, x, 0).perform()
        time.sleep(SLEEP)

    def move_to_target(self, target):
        offset = self.compute_offset(target)
        self.drag_and_drop_by_offset(x=offset)
        ## update position
        self.position = target

    def reset_slider(self):
        self.move_to_target(target=self.min)
        ## update position
        self.position = self.min



class NoValidCar(Exception):
    def __init__(self, message):
        super().__init__(message)

class NoSimilarCar(Exception):
    def __init__(self, message):
        super().__init__(message)