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



class EndOfTable:
    __benchmark = None

    def __init__(self, driver):
        self.driver = driver
    
    def tick(self, verbose=True):
        if verbose:
            print("Scrolling table...")
        
        xpath = "//div[@id='cars']//tr[last()]"
        compare = self.driver.find_element(By.XPATH, xpath).text
        if compare == self.__benchmark:
            return 1
        else:
            self.__benchmark = compare
            return 0



def load_dynamic_table(driver, sleep=0.5):
    end = EndOfTable(driver)
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(sleep)
        if end.tick() == 1:
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
            raise Exception("vehicle_class must be one of Car.vehicle_classes")

        if fuel_type not in self.fuel_types:
            raise Exception("fuel_type must be one of Car.fuel_types")
        
        self.vehicle_class, self.fuel_type, self.fuel_consumption = vehicle_class, fuel_type, fuel_consumption



class Slider:
    """Acts on handle
    """

    def __init__(self, driver, slider_handle, step_size=[5, 1e3], min=SLIDER_MIN, max=SLIDER_MAX, start=SLIDER_START):
        """Manipulate slider object

        Args:
            driver: Selenium driver
            slider_handle: Slider handle object
            step_size (list, optional): 5 pix == 1000km. Defaults to [5, 1e3].
            min (int, optional): Slider lower bound. Defaults to SLIDER_MIN.
            max (int, optional): Slider upper bound. Defaults to SLIDER_MAX.
            start(int, optional): Slider initial position. Defaults to SLIDER_START.
        """
        self.driver, self.slider_handle, self.step_size, self.min, self.max, self.start = driver, slider_handle, step_size, min, max, start
    
    def compute_offset(self, target, start):
        diff = target - start
        step = int(diff / self.step_size[1])
        offset = step * self.step_size[0]
        return offset
    
    def drag_and_drop_by_offset(self, x):
        ## by pixels...
        ActionChains(self.driver).drag_and_drop_by_offset(self.slider_handle, x, 0).perform()

    def move_to_target_from_position(self, target, position):
        offset = self.compute_offset(target, position)
        self.drag_and_drop_by_offset(x=offset)

    def reset_slider(self, position=None):
        if position is None:
            position = self.start
        self.move_to_target_from_position(target=self.min, position=position)

    def reset_and_move(self, target):
        self.reset_slider()
        self.move_to_target_from_position(target=target, position=self.start)



