import requests
import sys

API_KEY = None
CSE_ID = None

def get_image_url(search_query):
    if API_KEY is None or CSE_ID is None:
        print(
            "You need to include the API Key and CSE ID in 'scanner.py' for this plugin to search for images.",
            file=sys.stderr,
        )

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_query,
        "cx": CSE_ID,
        "key": API_KEY,
        "searchType": "image",
        "num": 1,
    }
    response = requests.get(search_url, params=params)
    response.raise_for_status()
    search_results = response.json()
    if "items" not in search_results:
        raise Exception("No images found")
    return search_results["items"][0]["link"]
