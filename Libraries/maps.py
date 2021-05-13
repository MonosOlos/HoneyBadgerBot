import os
import json
import urllib3
import requests

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


