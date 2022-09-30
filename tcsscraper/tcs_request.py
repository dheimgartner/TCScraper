import requests

base_url = "https://www.verbrauchskatalog.ch/?async=1&cars=1"


def tcs_request(page = 100):
    r = requests.get(base_url + "&page=" + str(page))
    r.json()



if __name__ == "__main__":
    out = tcs_request()
    print(out)