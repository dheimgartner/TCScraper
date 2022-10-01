#%%
import pandas as pd
from itertools import compress
from shutil import ExecError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from . import helper
from .helper import Car, Slider


TIMEOUT = 60


def get_base_table(headless=True, verbose=False):

    driver = helper.set_up_driver(headless)
    
    try:
        wait_variable = WebDriverWait(driver, timeout=TIMEOUT)
        
        ## change to listenansicht
        listenansicht = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='filters']//select[@name='view']"))
        dropdown = Select(listenansicht)
        dropdown.select_by_visible_text("Listenansicht")
        
        ## legend
        legend = wait_variable.until(lambda d: d.find_element(By.ID, "legend"))
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




def scrape_one_car(driver, car, km, canton, verbose=False):

    wait_variable = WebDriverWait(driver, timeout=TIMEOUT)

    ## popup
    popup = car.find_element(By.CSS_SELECTOR, "td")
    driver.execute_script("arguments[0].click();", popup)

    time.sleep(0.5)

    xpath = "//div[@id='lightbox-content']"

    box = wait_variable.until(lambda d: d.find_element(By.XPATH, xpath))
    select_element = box.find_element(By.CSS_SELECTOR, "select")
    canton_dropdown = Select(select_element)
    canton_dropdown.select_by_visible_text(canton)

    ## spezifikationen
    specifications = wait_variable.until(lambda d: d.find_element(By.XPATH, xpath))
    table_rows = specifications.find_elements(By.CSS_SELECTOR, "tr")
    content = helper.scrape_table_rows(table_rows)
    rows = content["rows"]

    ## some cleaning
    car_specs = {r[0]: r[1] for r in rows if r[0].strip()}
    car_specs.pop("Kanton")
    car_specs = {key.replace("\n", "").replace("*", ""): value for (key, value) in car_specs.items()}

    
    ## betriebskosten
    betriebskosten = specifications.find_element(By.XPATH, "//ul[@id='lnav']//li[@tab='1']")
    betriebskosten.click()


    srange = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='popup_slider1']/div"))
    shandle = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='popup_slider1']/span"))

    slider = Slider(driver, shandle)
    slider.reset_and_move(target=km)

    costs = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='tco-box']"))
    car_costs = costs.text.split("\n")
    car_costs = [cc.strip().replace(":", "") for cc in car_costs]
    it = iter(car_costs)
    car_costs = dict(zip(it, it))

    ## close popup
    close_popup = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='lightbox']/div/div"))
    close_popup.click()

    if verbose:
        print("Extracted {} {} {}".format(car_specs["Marke"], car_specs["Modell"], car_specs["Ausführung"]))

    return {"specs": car_specs, "costs": car_costs, "km": km, "canton": canton}



def scrape_cars(driver, cars, km, canton, verbose=False):

    content = []
    for c in cars:
        car = scrape_one_car(driver, c, km, canton, verbose=verbose)
        content.append(car)
    return content



## multiple vehicle_class and fuel_types should be accepted... however dropdown => can only select one! => iterate
def get_similar_cars(vehicle_class, fuel_type, fuel_consumption, km, canton, buffer=0.5, headless=True, verbose=False):

    car = Car(vehicle_class, fuel_type, fuel_consumption)

    driver = helper.set_up_driver(headless)
    
    try:
        wait_variable = WebDriverWait(driver, timeout=TIMEOUT)
        
        ## change to listenansicht
        listenansicht = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='filters']//select[@name='view']"))
        dropdown = Select(listenansicht)
        dropdown.select_by_visible_text("Listenansicht")

        ## filter by vehicle_class
        vc_element = wait_variable.until(lambda d: d.find_element(By.NAME, "FzKlasse"))
        vc_dropdown = Select(vc_element)
        vc_dropdown.select_by_visible_text(car.vehicle_class)

        ## filter by fuel_type
        ft_element = wait_variable.until(lambda d: d.find_element(By.NAME, "Treibstoffart"))
        ft_dropdown = Select(ft_element)
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
            if number > car.fuel_consumption - buffer and number < car.fuel_consumption + buffer:
                idx.append(True)
            else:
                idx.append(False)

        relevant_cars = list(compress(table_rows, idx))

        if len(relevant_cars) == 0:
            raise Exception("No similar cars found. A missmatch between model and consumption? Consider increasing buffer.")

        content = scrape_cars(driver, relevant_cars, km, canton, verbose=verbose)


    
    except Exception as e:
        print(e)
        driver.quit()
        return None

    driver.quit()
    return content



#%%
if __name__ == "__main__":
    # data = get_base_table(headless=True)
    cars = get_similar_cars("SUV S", "Benzin", fuel_consumption=5, km=10e3, canton="AG", buffer=1, headless=True, verbose=True)



# %%