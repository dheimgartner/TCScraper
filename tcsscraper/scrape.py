from shutil import ExecError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

import time

import helper
from helper import Car

from itertools import compress


def get_base_table(headless=True):

    driver = helper.set_up_driver(headless)
    
    try:
        wait_variable = WebDriverWait(driver, timeout=60)
        
        ## change to listenansicht
        dropdown = Select(driver.find_element(By.XPATH, "//div[@id='filters']//select[@name='view']"))
        dropdown.select_by_visible_text("Listenansicht")
        
        ## legend
        legend = driver.find_element(By.ID, "legend")
        legend_values = legend.find_elements(By.CLASS_NAME, "number-desc")
        colnames = []
        for item in legend_values:
            v = item.text
            v = v.replace("\n", " ")
            colnames.append(v)


        helper.load_dynamic_table(driver)


        table = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='cars']/div[@id='list']"))

        ## get data
        table_rows = table.find_elements(By.XPATH, "//div[@id='cars']//tr")
        table_rows = table_rows[1:]
        content = helper.scrape_table_rows(table_rows)
        rows = content["rows"]  
            
        data = pd.DataFrame(rows)
        data.columns = colnames


    
    except Exception as e:
        print(e)
        driver.quit()
        return None

    driver.quit()
    return data









## multiple vehicle_class and fuel_types should be accepted...
def get_similar_cars(vehicle_class, fuel_type, fuel_consumption, km, canton, bound = 0.5, headless=True):

    car = Car(vehicle_class, fuel_type, fuel_consumption)

    driver = helper.set_up_driver(headless)
    
    try:
        wait_variable = WebDriverWait(driver, timeout=60)
        
        ## change to listenansicht
        dropdown = Select(driver.find_element(By.XPATH, "//div[@id='filters']//select[@name='view']"))
        dropdown.select_by_visible_text("Listenansicht")

        ## filter by vehicle_class
        vc_dropdown = Select(driver.find_element(By.NAME, "FzKlasse"))
        vc_dropdown.select_by_visible_text(car.vehicle_class)

        ## filter by fuel_type
        ft_dropdown = Select(driver.find_element(By.NAME, "Treibstoffart"))
        ft_dropdown.select_by_visible_text(car.fuel_type)


        helper.load_dynamic_table(driver)

        table = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='cars']/div[@id='list']"))
        
        table_rows = table.find_elements(By.XPATH, "//div[@id='cars']//tr")
        table_rows = table_rows[1:]
        content = helper.scrape_table_rows(table_rows)
        table_rows = content['elements']
        rows = content['rows']  
            
        data = pd.DataFrame(rows)
        consumption = data[7]
        idx = []
        for index, value in consumption.items():
            nu = value.split(" ")
            number, unit = float(nu[0]), nu[1]
            if number > car.fuel_consumption - bound and number < car.fuel_consumption + bound:
                idx.append(True)
            else:
                idx.append(False)

        relevant_cars = list(compress(table_rows, idx))

        content = helper.scrape_cars(driver, relevant_cars, km, canton)


    
    except Exception as e:
        print(e)
        driver.quit()
        return None

    driver.quit()
    return content






if __name__ == "__main__":
    # data = get_base_table()
    # print(data)

    cars = get_similar_cars("Mikroklasse", "Benzin", 5, 20e3, "AI", headless=False)
    
    import pdb
    pdb.set_trace()
    
    print(cars)
