import json
import numpy as np
import os
import pandas as pd
import re
import requests
import sys

from math import comb
from time import sleep

SCRYFALL_REQUEST_URL = "https://api.scryfall.com"
test_path_1 = "C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\archidekt_standard_export_1.txt"
test_path_2 = "C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\archidekt_standard_export_2.txt"



def readAndFormatDecklist(input_path: str):
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

def retrieveScryfallData(deck_dict: dict):
    for card_name in deck_dict.keys():
        request_string = f"{SCRYFALL_REQUEST_URL}/cards/named?exact={card_name.replace(" ", "+")}"
        scryfall_response = requests.get(request_string)
        scryfall_response_json = scryfall_response.json()
        deck_dict[card_name]["mana_cost"] = scryfall_response_json["mana_cost"]
        deck_dict[card_name]["cmc"] = scryfall_response_json["cmc"]
        deck_dict[card_name]["type_line"] = scryfall_response_json["type_line"]
        deck_dict[card_name]["oracle_text"] = scryfall_response_json["oracle_text"]
        sleep(0.075)
    return deck_dict

def getLandCount(deck_dict: dict):
    land_count = 0
    for card_name in deck_dict.keys():
        if re.search(r"( Land | Land$|^Land |^Land$)", deck_dict[card_name]["type_line"]):
            land_count += deck_dict[card_name]["count"]
    return land_count

def getCardCount(deck_dict: dict):
    card_count = 0
    for card_name in deck_dict.keys():
        card_count += deck_dict[card_name]["count"]
    return card_count

def getLandDistribution(card_count: int, land_count: int, num_cards_drawn: int):
    nonland_count = card_count - land_count
    prob_list = []
    for num_lands_drawn in range(0, num_cards_drawn+1):
        prob = comb(land_count, num_lands_drawn) * comb(nonland_count, num_cards_drawn - num_lands_drawn) / comb(card_count, num_cards_drawn)
        prob_list.append(prob)

    return np.array(prob_list)

def playLandEachTurn(card_count: int, land_count: int, turn_number: int, starting_hand_size: int):
    num_cards_drawn_at_turn = turn_number - 1 + starting_hand_size
    land_dist = getLandDistribution(card_count, land_count, num_cards_drawn_at_turn)
    print(np.sum(land_dist[turn_number:]))

def analyzeMulligans(card_count: int, land_count: int, min_lands_keep: int = 3, max_lands_keep: int = 5, hard_stop: int = 4, starting_hand_size: int = 7):
    mull_analysis_dict = {num_cards_drawn: {"land_dist": getLandDistribution(card_count, land_count, num_cards_drawn)} for num_cards_drawn in range(1, starting_hand_size + 1)}
    
    if min_lands_keep > starting_hand_size or min_lands_keep < 0:
        raise ValueError(f"min_lands_keep must be a value between 0 and {starting_hand_size} (starting_hand_size)")
    if max_lands_keep > starting_hand_size or max_lands_keep < 1:
        raise ValueError(f"max_lands_keep must be a value between 1 and {starting_hand_size} (starting_hand_size)")

    #print(json.dumps(mull_analysis_dict, indent = 1))
    for num_cards_drawn in mull_analysis_dict.keys():
        mull_analysis_dict[num_cards_drawn]["keep_prob"] = mull_analysis_dict[num_cards_drawn]["land_dist"][min_lands_keep : max_lands_keep + 1]
        mull_analysis_dict[num_cards_drawn]["mull_prob"] = 1 - mull_analysis_dict[num_cards_drawn]["keep_prob"]
        #print(mull_analysis_dict[num_cards_drawn]["land_dist"][:max_lands_keep])
    # hand_size = starting_hand_size
    # while hand_size >= min_lands_keep:
    #     land_dist = 

    if starting_hand_size <= min_lands_keep:
        return 1
    
    print("helllo")

def playLandEachTurnWithMulligan(card_count: int, land_count: int, turn_number: int, mull_to: int):
    print("tbd")

def playXLandsInYTurns(card_count: int, land_count: int, lands_played: int, turn_number: int):
    print("tbd")

if __name__ == "__main__":
    deck_dict = readAndFormatDecklist(test_path_1)
    deck_dict = retrieveScryfallData(deck_dict)
    land_count = getLandCount(deck_dict)
    card_count = getCardCount(deck_dict)
    print(f"Your deck has: {land_count} lands in it out of {card_count} total cards. This means {land_count/card_count:.0%} of your deck is made up of lands.")
    opening_hand_land_dist = getLandDistribution(card_count, land_count, 7)
    print("Your opening hand land draw probabilities are: ")
    print(opening_hand_land_dist)
    print("If you mull to 6 the distribution changes to this:")
    single_mull_land_dist = getLandDistribution(card_count, land_count, 6)
    print(single_mull_land_dist)

    playLandEachTurn(card_count, land_count, 4, 7)
    playLandEachTurn(card_count, land_count, 4, 8)
    analyzeMulligans(card_count, land_count, min_lands_keep=2, max_lands_keep=5, hard_stop=4, starting_hand_size=7)

    #print(json.dumps(deck_dict, indent=1))



    
