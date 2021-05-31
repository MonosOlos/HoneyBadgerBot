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


def get_map_details(cfg, map_name):
    maps = get_maps(cfg)

    for map in maps:
        if map["name"].lower() == map_name.lower():
            return map


def fetch_image_link(map_name):

    base_api_url = "https://liquipedia.net/starcraft2/api.php?"

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "images",
        "titles": map_name
    }

    response = requests.get(url=base_api_url, params=params)
    data = response.json()

    # If there's an error, try adding LE and retry
    if "images" not in data["query"]["pages"][0] and "LE" not in params["titles"]:
         params["titles"] = params["titles"] + " LE"
         response = requests.get(url=base_api_url, params=params)
         data = response.json()

    # Doing a regex query to ensure I get an image that corresponds with the map instead of e.g. a random icon
    for mapinfo in data["query"]["pages"][0]["images"]:
        mapname = re.search("File:(.+?)\.", mapinfo["title"]).group(1) # File:Mapname.jpg -> Mapname
        if mapname in map_name:
            break

    map_title = mapinfo["title"] # File:Mapname.jpg

    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url",
        "titles": map_title
    }

    response = requests.get(url=base_api_url, params=params)
    data = response.json()
    page = next(iter(data["query"]["pages"].values()))
    image_info = page["imageinfo"][0]
    image_url = image_info["url"]

    return image_url