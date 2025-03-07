#%%
import logging
import time
from itertools import compress
from shutil import ExecError

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from . import helper
from .helper import Car, NoSimilarCar, Slider

TIMEOUT = 60
SLEEP = 0.5


def get_base_table(headless=True, verbose=False):

    driver = helper.set_up_driver(headless)

    try:
        wait_variable = WebDriverWait(driver, timeout=TIMEOUT)

        ## change to listenansicht
        listenansicht = wait_variable.until(
            lambda d: d.find_element(
                By.XPATH, "//div[@id='filters']//select[@name='view']"
            )
        )
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

        table = wait_variable.until(
            lambda d: d.find_element(By.XPATH, "//div[@id='cars']/div[@id='list']")
        )

        ## get data
        table_rows = table.find_elements(By.XPATH, "//div[@id='cars']//tr")
        table_rows = table_rows[1:]
        content = helper.scrape_table_rows(table_rows)
        rows = content["rows"]

        data = pd.DataFrame(rows)
        data.columns = colnames

    except Exception as e:
        logging.warning("Exception occured: could not retrieve base table")
        print(e)
        driver.quit()
        return None

    driver.quit()
    return data


def scrape_one_car(driver, car, km, canton, verbose=False):
    """Scrapes the info Betriebskosten, etc. from the popup"""

    wait_variable = WebDriverWait(driver, timeout=TIMEOUT)

    ## popup
    popup = car.find_element(By.CSS_SELECTOR, "td")
    driver.execute_script("arguments[0].click();", popup)

    time.sleep(SLEEP)

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
    car_specs = {
        key.replace("\n", "").replace("*", ""): value
        for (key, value) in car_specs.items()
    }

    ## betriebskosten
    betriebskosten = specifications.find_element(
        By.XPATH, "//ul[@id='lnav']//li[@tab='1']"
    )
    betriebskosten.click()

    srange = wait_variable.until(
        lambda d: d.find_element(By.XPATH, "//div[@id='popup_slider1']/div")
    )
    shandle = wait_variable.until(
        lambda d: d.find_element(By.XPATH, "//div[@id='popup_slider1']/span")
    )

    slider = Slider(driver, shandle)
    slider.move_to_target(target=km)

    costs = wait_variable.until(
        lambda d: d.find_element(By.XPATH, "//div[@id='tco-box']")
    )
    car_costs = costs.text.split("\n")
    car_costs = [cc.strip().replace(":", "") for cc in car_costs]
    it = iter(car_costs)
    car_costs = dict(zip(it, it))

    ## close popup
    close_popup = wait_variable.until(
        lambda d: d.find_element(By.XPATH, "//div[@id='lightbox']/div/div")
    )
    close_popup.click()

    if verbose:
        print(
            "Extracted {} {} {}".format(
                car_specs["Marke"], car_specs["Modell"], car_specs["Ausführung"]
            )
        )

    return {"specs": car_specs, "costs": car_costs, "km": km, "canton": canton}


def scrape_cars(driver, cars, km, canton, verbose=False):
    """Iterates through list of cars and calls scrape one car"""
    content = []
    for c in cars:
        try:
            car = scrape_one_car(driver, c, km, canton, verbose=verbose)
        except Exception as e:
            logging.warning("Exception occured.")
            car = None
        content.append(car)
    return content


def get_cars(
    car_object,
    km,
    canton,
    similar={"flag": True, "buffer": 0.5},
    headless=True,
    verbose=False,
):
    """Scrape cars by providing a Car instance template

    Args:
        car_object (Car): Car instance
        km (int): annual mileage
        canton (str): residence
        similar (dict, optional): Should we retrieve all cars that match
            with the car_object or only similar ones (in terms of fuel_consumption).
            Defaults to {'flag': True, 'buffer': 0.5}.
        headless (bool, optional): No visible headbrowser. Defaults to True.
        verbose (bool, optional): neo. Defaults to False.

    Raises:
        NoSimilarCar: _description_
        e: _description_

    Returns:
        _type_: _description_
    """
    driver = helper.set_up_driver(headless)

    try:
        wait_variable = WebDriverWait(driver, timeout=TIMEOUT)

        ## change to listenansicht
        listenansicht = wait_variable.until(
            lambda d: d.find_element(
                By.XPATH, "//div[@id='filters']//select[@name='view']"
            )
        )
        dropdown = Select(listenansicht)
        dropdown.select_by_visible_text("Listenansicht")

        ## filter by vehicle_class
        vc_element = wait_variable.until(lambda d: d.find_element(By.NAME, "FzKlasse"))
        vc_dropdown = Select(vc_element)
        vc_dropdown.select_by_visible_text(car_object.vehicle_class)

        ## filter by fuel_type
        ft_element = wait_variable.until(
            lambda d: d.find_element(By.NAME, "Treibstoffart")
        )
        ft_dropdown = Select(ft_element)
        ft_dropdown.select_by_visible_text(car_object.fuel_type)

        helper.load_dynamic_table(driver)

        table = wait_variable.until(
            lambda d: d.find_element(By.XPATH, "//div[@id='cars']/div[@id='list']")
        )

        table_rows = table.find_elements(By.XPATH, "//div[@id='cars']//tr")
        table_rows = table_rows[1:]
        content = helper.scrape_table_rows(table_rows)
        table_rows = content["elements"]
        rows = content["rows"]

        if similar["flag"] is True:
            buffer = similar["buffer"]
            data = pd.DataFrame(rows)
            consumption = data[7]
            idx = []
            for index, value in consumption.items():
                nu = value.split(" ")
                number, unit = float(nu[0]), nu[1]
                if (
                    number > car_object.fuel_consumption - buffer
                    and number < car_object.fuel_consumption + buffer
                ):
                    idx.append(True)
                else:
                    idx.append(False)
            relevant_cars = list(compress(table_rows, idx))
        else:
            relevant_cars = table_rows

        if len(relevant_cars) == 0:
            logging.info("No relevant cars found")
            raise NoSimilarCar(
                "No similar cars found. A missmatch between model and consumption? Consider increasing buffer."
            )

        content = scrape_cars(driver, relevant_cars, km, canton, verbose=verbose)

    except Exception as e:
        logging.warning("Exception occured: could not get cars")
        driver.quit()
        raise e

    driver.quit()
    return content
