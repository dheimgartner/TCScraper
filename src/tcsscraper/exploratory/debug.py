import pickle
import api.scrape as tcs

import logging

# logging.basicConfig(
#     format="%(asctime)s %(levelname)s %(funcName)s %(message)s",
#     filename="logging.log",
#     level=logging.INFO,
# )

# with open("data/df_archs", "rb") as fp:
#     df_archs = pickle.load(fp)

# pc = df_archs.iloc[2]["car_objects"]

# car = tcs.get_cars(pc, 15e3, "ZH", similar={"flag": False}, headless=True, verbose=True)


car = tcs.get_cars(
    car_object=tcs.Car("Kleinwagen", "Benzin", None),
    canton="ZH",
    km=15e3,
    similar={"flag": False},
    headless=True,
    verbose=True,
)
