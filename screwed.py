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

    cum_prob_list = []
    inv_cum_prob_list = []
    cum_prob = 0
    for prob in prob_list:
        cum_prob += prob
        cum_prob_list.append(cum_prob)
        inv_cum_prob_list.append(1-cum_prob)
    
    df = pd.DataFrame({
        "num_lands_drawn": range(0, num_cards_drawn+1),
        "prob": prob_list,
        "cum_prob": cum_prob_list,
        "inv_cum_prob": inv_cum_prob_list
        }
    )
    return df

def noLandsDrawn(card_count: int, land_count: int, num_cards_drawn: int):
    nonland_count = card_count - land_count

    for i in range(0, num_cards_drawn):
        if i == 0:
            prob = nonland_count / card_count
        else:
            prob = prob * (nonland_count - i) / (card_count - i)
    return prob

def playLandEachTurn(card_count: int, land_count: int, turn_number: int, on_play):
    """
    Prob of being able to play a land each turn up till turn x, calculated by first seeing what the prob of not being able to play a land on any turn 1-X
     - turn 1 you can't play a land if you have no lands in hand 
     - turn 2 you can't play a land if you didn't have a land in hand turn 1 and you didn't draw a land turn 2, or if you had only 1 land in hand turn 1 
    """
    if on_play:
        opening_hand_land_dist = getLandDistribution(card_count, land_count, 7)

        noLandTurnOne = opening_hand_land_dist["num_lands_drawn"]
        
        for i in range(1,turn_number+1):
            print("helllo")
    print("hello")



if __name__ == "__main__":
    deck_dict = readAndFormatDecklist(test_path_1)
    deck_dict = retrieveScryfallData(deck_dict)
    land_count = getLandCount(deck_dict)
    card_count = getCardCount(deck_dict)
    print(f"Your deck has: {land_count} lands in it out of {card_count} total cards. This means {land_count/card_count:.0%} of your deck is made up of lands.")
    opening_hand_land_dist = getLandDistribution(card_count, land_count, 7)
    print(noLandsDrawn(card_count, land_count, 7))
    print("Your opening hand land draw probabilities are: ")
    print(opening_hand_land_dist)
    print(type(opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 0]["prob"][0]))
    print(noLandsDrawn(card_count, land_count, 6))
    print("If you mull to 6 the distribution changes to this:")
    single_mull_land_dist = getLandDistribution(card_count, land_count, 6)
    print(single_mull_land_dist)



    #print(json.dumps(deck_dict, indent=1))



    
