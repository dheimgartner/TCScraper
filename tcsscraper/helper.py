from argparse import Action
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import time
import pandas as pd
import json


SLIDER_MIN = 5e3
SLIDER_MAX = 50e3
SLIDER_START = 15e3


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



def scrape_one_car(driver, car, km, canton):

    wait_variable = WebDriverWait(driver, timeout=10)

    ## popup
    popup = wait_variable.until(lambda x: car.find_element(By.CSS_SELECTOR, "td"))
    driver.execute_script("arguments[0].click();", popup)

    time.sleep(0.5)

    xpath = "//div[@id='lightbox-content']"

    box = driver.find_element(By.XPATH, xpath)

    canton_dropdown = Select(box.find_element(By.CSS_SELECTOR, "select"))
    canton_dropdown.select_by_visible_text(canton)

    ## spezifikationen
    specifications = wait_variable.until(lambda d: d.find_element(By.XPATH, xpath))
    table_rows = specifications.find_elements(By.CSS_SELECTOR, "tr")
    content = scrape_table_rows(table_rows)
    rows = content["rows"]

    ## some cleaning
    car_specs = {r[0]: r[1] for r in rows if r[0].strip()}
    car_specs.pop("Kanton")
    car_specs = {key.replace("\n", ""): value for (key, value) in car_specs.items()}

    
    ## betriebskosten
    specifications.find_element(By.XPATH, "//ul[@id='lnav']//li[@tab='1']").click()

    ## slider
    slider = driver.find_element(By.XPATH, "//div[@id='popup_slider1']/span")
    move = ActionChains(driver)
    range = SLIDER_MAX - SLIDER_MIN
    offset = 100 / range * (km - SLIDER_START)
    move.click_and_hold(slider).move_by_offset(offset, 0).release().perform()

    costs = driver.find_element(By.XPATH, "//div[@id='tco-box']")
    car_costs = costs.text.split("\n")
    car_costs = [cc.strip().replace(":", "") for cc in car_costs]
    it = iter(car_costs)
    car_costs = dict(zip(it, it))

    ## close popup
    close_popup = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='lightbox']/div/div"))
    close_popup.click()

    return {"specs": car_specs, "costs": car_costs}



    



def scrape_cars(driver, cars, km, canton):

    content = []
    for c in cars:
        car = scrape_one_car(driver, c, km, canton)
        content.append(car)
    return content