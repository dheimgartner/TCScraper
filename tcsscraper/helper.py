from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd



class EndOfTable:
    __benchmark = None

    def __init__(self, driver):
        self.driver = driver
    
    def tick(self, verbose=True):
        if verbose:
            print("tick")
        
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



def set_up_driver(headless=True):
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")

    driver = webdriver.Firefox(options=options)
    
    try:
        driver.maximize_window()
        base_url = "https://www.verbrauchskatalog.ch/index.php"
        driver.get(base_url)

    except Exception as e:
        print(e)
        return None

    return driver




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



def scrape_car(driver, cars):