import json
import numpy as np
import os
import pandas as pd
import re
import requests
import sys

from time import sleep

SCRYFALL_REQUEST_URL = "https://api.scryfall.com/cards/named?exact="
test_path_1 = "C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\archidekt_standard_export_1.txt"
test_path_2 = "C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\archidekt_standard_export_2.txt"

def readAndFormatDecklist(input_path):
    with open(input_path) as deck_txt_file:
        Lines = deck_txt_file.readlines()
    Lines = [line.strip() for line in Lines if line.strip() != ""]

    deck_dict = {}
    for line in Lines:
        split_line = line.split(" ")
        
        card_count = split_line[0]
        if card_count[-1] == "x":
            card_count = card_count[:-1]
        card_count = int(card_count)
        card_name = " ".join(split_line[1:])
        
        deck_dict[card_name] = {"count": card_count}
    print(deck_dict)
    return deck_dict

def retrieveScryfallData(deck_dict):
    for card_name in deck_dict.keys():
        request_string = f"{SCRYFALL_REQUEST_URL}{card_name.replace(" ", "+")}"
        scryfall_response = requests.get(request_string)
        scryfall_response_json = scryfall_response.json()
        deck_dict[card_name]["mana_cost"] = scryfall_response_json["mana_cost"]
        deck_dict[card_name]["cmc"] = scryfall_response_json["cmc"]
        deck_dict[card_name]["type_line"] = scryfall_response_json["type_line"]
        deck_dict[card_name]["oracle_text"] = scryfall_response_json["oracle_text"]
        print(json.dumps(scryfall_response_json, indent = 1))
        sleep(0.075)
    return deck_dict



if __name__ == "__main__":
    deck_dict_1 = readAndFormatDecklist(test_path_1)
    deck_dict_1 = retrieveScryfallData(deck_dict_1)
    print(json.dumps(deck_dict_1, indent=1))



    
