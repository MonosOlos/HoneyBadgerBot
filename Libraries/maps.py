import os
import json
import urllib3
import requests
import json
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #TODO HOW TO MAKE THIS SECURE?

def get_maps(cfg):
    # Link to the API endpoint for maplist
    base_url = cfg["BASE_URL"]
    map_list_rest = cfg["MAP_LIST_REST"]

    map_list = []
    url = base_url + map_list_rest
    next_page = base_url + map_list_rest

    while next_page != None:
        response = requests.get(next_page, verify=False)

        map_list += response.json()["results"]
        next_page = response.json()["next"]

    return map_list


def get_map_names(cfg, lower=False):
    maps = get_maps(cfg)
    map_names = []
    
    for map in maps:
        if lower == False:
            map_names.append(map["name"])
        else:
            map_names.append(map["name"].lower())

    return map_names


# ----- Liquipedia API Stuff ------

def liquipedia_get_page(search_title):

    search_name = search_title.lower()

    base_api_url = "https://liquipedia.net/starcraft2/api.php?"

    params = {
        "action": "query",
        "list": "search",
        "format": "json",
        "srsearch": search_name,
    }

    response = requests.get(url=base_api_url, params=params)
    print(response.url)
    data = response.json()

    raw_details = None
    results = data["query"]["search"]
    for result in results:
        if search_name in result["title"].lower():
            raw_details = result
            break
    
    # MAP NOT FOUND
    if raw_details == None:
        return None

    def check_match(regex, search_string=raw_details["snippet"]):
        try:
            return re.search(regex, raw_details["snippet"]).group(1)
        except AttributeError:
            return None

    
    map_details = {
        "pageid" : raw_details["pageid"],
        "page url": liquipedia_get_page_url(raw_details["pageid"]),
        "title" : raw_details["title"],
        "size" : check_match(r"Size: (.+?) \w+"),
        "rush distance" : check_match(r"Rush distance: (.+?\d)\s"),
        "spawn positions" : check_match(r"Spawn Positions: (.+?\d)\s"),
        "ladder" : check_match(r"Ladder: (.+?)$") 
    }
    
    return map_details


def liquipedia_get_image_filename(map_details):
    map_name = map_details["title"]

    base_api_url = "https://liquipedia.net/starcraft2/api.php?"

    params = {
        "action": "query",
        "format": "json",
        "prop": "images",
        "pageids": map_details["pageid"]
    }

    response = requests.get(url=base_api_url, params=params)
    data = response.json()

    page_values = next(iter(data["query"]["pages"].values()))

    for image in page_values["images"]:
        if map_name.split()[0] in image["title"]:
            break
    

    image_filename = image["title"]
    return image_filename


def liquipedia_get_image_url(map_details):
    image_filename = liquipedia_get_image_filename(map_details)

    base_api_url = "https://liquipedia.net/starcraft2/api.php?"

    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "titles": image_filename
    }

    response = requests.get(url=base_api_url, params=params)
    data = response.json()
    page = next(iter(data["query"]["pages"].values()))
    image_info = page["imageinfo"][0]
    image_url = image_info["url"]

    return image_url

def liquipedia_get_page_url(page_id):
    base_api_url = "https://liquipedia.net/starcraft2/api.php?"

    # https://liquipedia.net/starcraft2/api.php?action=query&prop=info&pageids=48483&inprop=url

    page_id = "48483"

    params = {
        "action": "query",
        "format": "json",
        "prop": "info",
        "inprop": "url",
        "pageids": page_id,
    }

    response = requests.get(url=base_api_url, params=params)
    data = response.json()

    url = data["query"]["pages"][page_id]["fullurl"]
    return url