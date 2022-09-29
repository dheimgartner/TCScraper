from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import time
import pandas as pd



def batch_scrape(driver, colnames, xpath = "//div[@id='cars']//tr"):

    raise(DeprecationWarning)
    
    last = driver.find_element(By.XPATH, xpath + "[last()]")
    compare = last.text
    driver.execute_script("arguments[0].scrollIntoView();", last)

    time.sleep(2)

    new_last = driver.find_element(By.XPATH, xpath)
    if new_last.text == compare:
        return None

    table_rows = driver.find_elements(By.XPATH, xpath)
    rows = []
    for r in table_rows:
        cells = r.find_elements(By.CSS_SELECTOR, "td")
        row = [c.text for c in cells]
        rows.append(row)
            
            
    table_data = pd.DataFrame(rows)
    table_data.columns = colnames

    return table_data




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
    vehicle_class = [
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

    fuel_type = [
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