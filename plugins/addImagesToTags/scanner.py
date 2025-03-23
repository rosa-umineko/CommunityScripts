import sys
import time
import requests

API_KEY = None
CSE_ID = None

def get_image_url(search_query):
    if API_KEY is None or CSE_ID is None:
        print(
            "You need to include the API Key and CSE ID in 'scanner.py' for this plugin to search for images.",
            file=sys.stderr,
        )

    time.sleep(3)

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": search_query,
        "cx": CSE_ID,
        "key": API_KEY,
        "searchType": "image",
        "num": 1,
    }
    response = requests.get(search_url, params=params)

    # Check for a 429 status code (Too Many Requests)
    if response.status_code == 429:
        print("429 Too Many Requests. Exiting.", file=sys.stderr)
        sys.exit(1)

    response.raise_for_status()
    search_results = response.json()
    if "items" not in search_results:
        raise Exception("No images found")
    return search_results["items"][0]["link"]
