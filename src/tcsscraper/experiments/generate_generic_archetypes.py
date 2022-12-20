import pickle

import numpy as np
import pandas as pd
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException)

import tcsscraper.api.scrape as tcs
from tcsscraper.api.helper import Car, NoSimilarCar



def remove_unit(string):
    """Removes unit from string like 17'000 CHF/year -> float(17e3)

    Args:
        string (str): string with unit
    """
    number, unit = string.split(" ")
    number = number.replace("'", "")
    return float(number)



def generate_archetype(similar_cars, ndigits=2):
    """Generates an archetypical car from a list of similar cars

    Args:
        similar_cars (list of dict): returned by get_cars()
        ndigits (int): round average values to
    """
    car_attributes = []
    for c in similar_cars:
        costs = c["costs"]
        attrs = {
            "fix_cost": remove_unit(costs["Fixe Kosten"]),
            "variable_cost": remove_unit(costs["Variable Kosten"]),
            "cost_per_km": remove_unit(costs["Kilometerkosten"]),
        }

        try:
            reach = c["specs"]["Reichweite (NEFZ/WLTP)"].split(" / ")
            reach = float(reach[1])
        except:
            reach = None

        attrs["reach"] = reach
        car_attributes.append(attrs)

    car_attributes = pd.DataFrame(car_attributes)

    archetype = dict(round(car_attributes.mean(), ndigits=ndigits))

    return archetype



## pack everything into a function
def generate_generic_archetypes(km=15e3, canton="ZH", verbose=True, path_save=None):
    """Generate archetype for each vehicle_class x fuel_type combination

    Args:
        km (int, optional): archetypes' annual mileage (reference). Defaults to 15e3.
        canton (str, optional): archetypes' domicile (reference). Defaults to 'AG'.
        verbose (bool, optional): neo. Defaults to True.

    Returns:
        pandas.DataFrame: containing vehicle_class, fuel_type, car_objects, as well as the archetypes (as returned by generate archetype)
    """
    ## generate df of all possible combinations
    archs = np.stack(np.meshgrid(Car.vehicle_classes, Car.fuel_types), axis=-1).reshape(
        -1, 2
    )
    df_archs = pd.DataFrame(archs)
    df_archs.columns = ["vehicle_class", "fuel_type"]

    df_archs["car_objects"] = df_archs.apply(
        lambda row: Car(row["vehicle_class"], row["fuel_type"], fuel_consumption=None),
        axis=1,
    )

    cars = []
    for c in df_archs["car_objects"]:
        if verbose:
            print("---\n{}\n---".format(c))
        try:
            car = tcs.get_cars(
                car_object=c,
                canton=canton,
                km=km,
                similar={"flag": False},
                headless=True,
                verbose=verbose,
            )
        except (NoSimilarCar, NoSuchElementException, StaleElementReferenceException) as e:
            logging.warning("Exception for {} x {}".format(c.vehicle_class, c.fuel_type))
            car = None
        cars.append(car)

    ## save
    if path_save is not None:
        with open(path_save, "wb") as fp:
            pickle.dump(cars, fp)

    generic_archetypes = []
    for c in cars:  ## is list of similar cars
        if c is None:
            generic_archetypes.append(None)
            continue
        ga = generate_archetype(c)
        generic_archetypes.append(ga)

    df_archs["generic_archetypes"] = generic_archetypes

    return df_archs



if __name__ == "__main__":
    ga = generate_generic_archetypes()