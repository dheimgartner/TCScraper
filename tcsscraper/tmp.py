import argparse
import os
import time

import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Specify input and output paths.")
parser.add_argument('--input_path', type=str, help='Input path to csv file containing parking garage data.',
                    default="/home/tchervec/Documents/projects/parking/data/parking/zurich_public_parking_garages_csv/data/stzh.poi_parkhaus_view.csv")
parser.add_argument('--output_path', type=str, help='Output path to csv file containing scraped parking garage data.',
                    default="/home/tchervec/Documents/projects/parking/data/parking/garage_parkopedia_data.csv")

args = parser.parse_args()
print(vars(args))
input_path = args.input_path
output_path = args.output_path


def get_parking_data(garage_id, garage_name, garage_address, headless=True):
    options = webdriver.FirefoxOptions()
    if headless:
        options.add_argument('-headless')
    driver = webdriver.Firefox(options=options)

    try:
        driver.maximize_window()
        wait_variable = WebDriverWait(driver, timeout=10)

        # connect to Parkopedia website
        driver.get("https://ch.parkopedia.com/")

        # get search bar
        search_bar = WebDriverWait(driver, timeout=10).until(
            lambda d: d.find_element(By.CLASS_NAME, "PlaceSearch__input"))

        # enter address in search bar and press enter
        search_bar.send_keys(garage_address + ", Zurich" + Keys.ENTER)

        # get list of suggested address and find the one that matches our input
        suggestion_list = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "SuggestionList"))
        garage_address = [a for a in suggestion_list.text.split("\n") if ("Zurich" in a)].pop(0)

        if len(garage_address) == 0:
            print("No matching address!")

        # click on the matchin address in the suggested list
        for e in suggestion_list.find_elements(By.TAG_NAME, "li"):
            if e.text == garage_address:
                e.click()
                break

        # get "Find Parking" submit button and click on it
        submit_button = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "SubmitButton__value"))
        submit_button.click()

        # now, we will be redirected to the results page

        # check if we have reached the request limit
        # try:
        #     wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "ResultsPage__blockwarning__message"))
        # except NoSuchElementException:
        #     # we did not find the element, so we can continue
        #     pass
        # else:
        #     # we found the element, therefore the request failed
        #     driver.quit()
        #     return None

        # find the parking location in the results that matches the name we are looking for
        location_list = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "LocationsList"))
        location_list = location_list.find_elements(By.CLASS_NAME, "LocationListItem__title")

        # always start with the first location in the list
        matched_locations = [location_list[0]]

        # try to find additional matches based on the name of the parking garage
        for l in location_list[0:np.min([10, len(location_list)])]:
            if garage_name in l.text:
                matched_locations.append(l)
                break
            elif " ".join(garage_name.split("-")) in l.text:
                matched_locations.append(l)
                break
            else:
                for string in " ".join(garage_name.split("-")).split(" "):
                    if string in l.text:
                        matched_locations.append(l)

        # if we have more than one matche, then we found at least one better match on top of the first element
        # therefore, we remove this first element
        if len(matched_locations) > 1:
            matched_locations.pop(0)

        # click through all the matched locations
        frames = []
        for i, location in enumerate(matched_locations):

            # print(location.text)

            # click on location link
            driver.execute_script("arguments[0].click();", location)

            # get title bar
            field = "TitleBar"
            content = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "LocationDetails%s" % field)).text
            df = pd.DataFrame({"id": [garage_id],
                               "name": [garage_name],
                               "address": [garage_address],
                               "match_nr": [i],
                               "field": [field],
                               "content": [content]})
            frames.append(df)

            # get contact details
            field = "ContactDetails"
            content = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "LocationDetails%s" % field)).text
            df = pd.DataFrame({"id": [garage_id],
                               "name": [garage_name],
                               "address": [garage_address],
                               "match_nr": [i],
                               "field": [field],
                               "content": [content]})
            frames.append(df)

            # get rest of data
            fields = wait_variable.until(lambda d: d.find_elements(By.CLASS_NAME, "LocationDetailsSection__title"))
            fields = [''.join(e.text.split()) for e in fields]

            for field in fields:
                content = wait_variable.until(lambda d: d.find_element(By.CLASS_NAME, "LocationDetails%s" % field)).text
                df = pd.DataFrame({"id": [garage_id],
                                   "name": [garage_name],
                                   "address": [garage_address],
                                   "match_nr": [i],
                                   "field": [field],
                                   "content": [content]})

                frames.append(df)

            # close window
            close_button = wait_variable.until(
                lambda d: d.find_element(By.CLASS_NAME, "LocationDetailsTitleBar__closeButton"))
            close_button.click()

        # concatonate into dataframe
        frames = pd.concat(frames)

    except:
        driver.quit()
        return None

    driver.quit()
    return frames


def scrape_data(garage_parking, df_garage=[], headless=True, persistant=False, delay=0,
                save_interim=True, output_path=None):

    if (save_interim) & (output_path is None):
        print("save_interim=True, please provide output path.")
        return df_garage

    # determine parking spots which were already scraped
    scraped_ids = []
    if len(df_garage) > 0:
        scraped_ids = list(df_garage["id"].unique())

        # initialize a list with current data
        df_garage = [df_garage]

    # determine which parking spots need to be scraped
    f = ~garage_parking["id"].isin(scraped_ids)

    # scrape parking data
    pbar = tqdm(total=len(garage_parking[f]))
    for i, garage in garage_parking[f].reset_index(drop=True).iterrows():

        # get data
        pbar.set_description("Scraping parking data for %s at %s" % (garage["name"], garage["adresse"]))
        df = get_parking_data(int(garage["id"]),
                              garage["name"],
                              garage["adresse"],
                              headless)

        # if we want to continue retrying the query
        if persistant:
            # something went wrong (we probably hit the request limit)
            while df is None:
                # so we wait a bit...
                pbar.reset(total=delay)
                pbar.set_description("Request limit hit. Waiting for %s seconds..." % str(delay))
                for _ in np.arange(0, delay, 1):
                    time.sleep(1)
                    pbar.update()

                # and try again
                pbar.reset(total=len(garage_parking[f]))
                pbar.set_description("Scraping parking data for %s" % garage["name"])
                df = get_parking_data(int(garage["id"]),
                                      garage["name"],
                                      garage["adresse"],
                                      headless)

            # append
            df_garage.append(df)

            # write to file
            if save_interim:
                df_garage = pd.concat(df_garage).reset_index(drop=True)
                pbar.set_description("Updating output file.")
                df_garage.to_csv(output_path, sep=";", index=False)
                time.sleep(1)

                # re-initialize to a list
                df_garage = [df_garage]

            # update pbar
            pbar.update(1)

        elif df is None:
            pbar.close()
            print("Request failed and persistant=False. Aborting!")
            break

        else:
            # append
            df_garage.append(df)

            # write to file
            if save_interim:
                df_garage = pd.concat(df_garage).reset_index(drop=True)
                pbar.set_description("Updating output file.")
                df_garage.to_csv(output_path, sep=";", index=False)

                # re-initialize to a list
                df_garage = [df_garage]

            # update pbar
            pbar.update(1)

    df_garage = pd.concat(df_garage).reset_index(drop=True)
    pbar.close()

    return df_garage


# load garage parking shapefile
print("Loading parking data from: %s" % input_path)
garage_parking = pd.read_csv(input_path)

# get garages that do not have a PLS link
f = garage_parking["link_pls"].isna()
garage_parking = garage_parking[f].reset_index(drop=True)

df_garage = []

# load already scraped data if it exists
if os.path.exists(output_path):
    print("Loading already scraped data from: %s" % output_path)
    df_garage = pd.read_csv(output_path, sep=";")
    print("Total of %s garages already scraped!" % len(df_garage["id"].unique()))

# scrape the Parkopedia data
df_garage = scrape_data(garage_parking=garage_parking,
                        df_garage=df_garage,
                        headless=True,
                        persistant=False, delay=600,
                        save_interim=True, output_path=output_path)
print("Total of %s garages scraped!" % len(df_garage["id"].unique()))

print("Writing output to: %s" % output_path)
df_garage.to_csv(output_path, sep=";", index=False)