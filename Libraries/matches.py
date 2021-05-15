import os
import json
import urllib3
import requests
import random

from Libraries.maps import get_maps
from Libraries.bot_config import get_config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) #TODO HOW TO MAKE THIS SECURE?

def make_match(cfg, player1_pk, player2_pk, map_pk = None, token=None):

    #TODO: Fetch specific map when API allows this
    if map_pk is not None:
        for imap in get_maps(cfg):
            if imap["pk"] == map_pk:
                chosen_map = imap
                break
        #filter(lambda x: x["pk"] == map_pk, map_list) #TODO: Test
    else:
        chosen_map = random.choice(get_maps(cfg)) # TODO: Hi

    match_details = {
        "players" : [player1_pk, player2_pk],
        "winner" : None,
        "tournament" : None,
        "map" : chosen_map["pk"],
        "map_name" : chosen_map["name"],
        "username" : cfg["USERNAME"],
        "password" : cfg["PASSWORD"]
    }

    return match_details

def get_login_token(cfg, token=None):
    login_url = cfg["BASE_URL"] + cfg["LOGIN"]
    auth_url = cfg["BASE_URL"] + "api-token-auth/"

    current_session = requests.session()
    current_session.get(login_url, verify=False)

    csrf = current_session.cookies['csrftoken']

    resp = current_session.post(auth_url, data={"username": cfg["USERNAME"], "password": cfg["PASSWORD"]}, headers={"Referer": login_url}).json()

    return {"csrf": csrf, "token": resp["token"]}

def add_match(cfg, match_details, token=None):

    if token is None:
        token = get_login_token(cfg)

    match_details["csrfmiddlewaretoken"] = token["csrf"]

    login_url = cfg["BASE_URL"] + cfg["LOGIN"]
    auth_url = cfg["BASE_URL"] + cfg["AUTH"]
    match_list_url = cfg["BASE_URL"] + cfg["MATCH_LIST_REST"]

    post_response = requests.post(match_list_url, 
        headers={
            "Referer": login_url, 
            "Authorization": "Token " + token["token"]
        }, 
        verify=False, 
        data=match_details)

    return post_response.json() #{'pk': INT, 'players': , 'winner':, 'date_played': , 'last_modified': , 'tournament': None, 'map': 14}

def update_result(cfg, match_pk, winner_pk, token=None):

    if token is None:
        token = get_login_token(cfg)

    match_update_url = cfg["BASE_URL"] + cfg["MATCH_UPDATE_REST"] + "/" + str(match_pk) + "/"

    match_details = requests.get(match_update_url, verify=False).json()
    match_details["winner"] = winner_pk

    patch_response = requests.patch(
        match_update_url,
        data = match_details["winner"], #TODO: Try using winner_pk in dict
        headers = {
            "Referer": match_update_url,
            "Authorization": "Token " + token["token"]
        }, 
        verify=False)
    
    return patch_response.json()

def get_player_key(cfg, discord_id):
    url = cfg["BASE_URL"] + cfg["DISCORD_LOOKUP_REST"] + str(discord_id) + "/"
    player_data = requests.get(url, verify=False).json()
    if type(player_data) != dict:
        return False
    player_key = player_data["pk"]
    return player_key

# token = get_login_token(cfg=get_config()) # yay it worked

# match_details = make_match(get_config(), 1, 2)

# add_match(get_config(), match_details, token)

# update_result(cfg=get_config(), match_pk=107, winner_pk=1)