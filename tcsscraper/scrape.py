from shutil import ExecError
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

import time

import helper


def get_base_table(headless=True):

    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument("-headless")

    driver = webdriver.Firefox(options=options)
    
    try:
        driver.maximize_window()
        wait_variable = WebDriverWait(driver, timeout=60)
        
        base_url = "https://www.verbrauchskatalog.ch/index.php"
        
        driver.get(base_url)
        
        
        ## change to listenansicht
        dropdown = Select(driver.find_element(By.NAME, "view"))
        dropdown.select_by_visible_text("Listenansicht")
        
        ## legend
        legend = driver.find_element(By.ID, "legend")
        legend_values = legend.find_elements(By.CLASS_NAME, "number-desc")
        colnames = []
        for item in legend_values:
            v = item.text
            v = v.replace("\n", " ")
            colnames.append(v)


        helper.load_dynamic_table()


        table = wait_variable.until(lambda d: d.find_element(By.XPATH, "//div[@id='cars']/div[@id='list']"))

        ## get data
        table_rows = table.find_elements(By.XPATH, "//div[@id='cars']//tr")
        table_rows = table_rows[1:]  ## drop header row
        rows = []
        for r in table_rows:
            cells = r.find_elements(By.CSS_SELECTOR, "td")
            row = [c.text for c in cells]
            rows.append(row)
            
            
        data = pd.DataFrame(rows)
        data.columns = colnames


    
    except Exception as e:
        print(e)
        driver.quit()
        return None

    driver.quit()
    return data






if __name__ == "__main__":
    data = get_base_table(headless=False)
    print(data)

