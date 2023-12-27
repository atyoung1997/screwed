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

def missLandTurnOne(card_count: int, land_count: int, opening_hand_land_dist: pd.DataFrame):
    # only miss turn one land if start game with 0 lands in hand
    return opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 0]["prob"][0]

def missLandTurnTwo(card_count: int, land_count: int, opening_hand_land_dist: pd.DataFrame):
    # miss land turn two if you start with 1 land and don't draw a land 
    one_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 1]["prob"][1]
    card_count = card_count - len(opening_hand_land_dist) + 1
    land_count = land_count - 1
    return one_land_turn_one * (card_count - land_count) / card_count

def missLandTurnThree(card_count: int, land_count: int, opening_hand_land_dist: pd.DataFrame):
    # scenario 1: miss land turn three if you start with 1 land, draw a land turn two, but not turn three 
    # scenario 2: you start with two lands, and don't draw a land on either turn two or three

    # scenario 1 calculations - we start with an opening hand with 1 land
    one_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 1]["prob"][1]
    card_count_s1 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s1 = land_count - 1 # one of the opening hand cards is a land
    nonland_count_s1 = card_count_s1 - land_count_s1
    # turn 2 draw is a land
    prob_s1 = one_land_turn_one * (land_count_s1 / card_count_s1)
    card_count_s1 -= 1
    land_count_s1 -= 1
    # turn 3 draw is a nonland
    prob_s1 = prob_s1 * (nonland_count_s1 / card_count_s1)

    # scenario 2 calculations - we start with an opening hand with 2 lands
    two_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 2]["prob"][2]
    card_count_s2 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s2 = land_count - 2 # one of the opening hand cards is a land
    nonland_count_s2 = card_count_s2 - land_count_s2
    # turn 2 draw is a nonland
    prob_s2 = two_land_turn_one * (nonland_count_s2 / card_count_s2)
    card_count_s2 -= 1
    nonland_count_s2 -= 1
    # turn 3 draw is a nonland
    prob_s2 = prob_s2 * (nonland_count_s2 / card_count_s2)

    return prob_s1 + prob_s2

def missLandTurnFour(card_count: int, land_count: int, opening_hand_land_dist: pd.DataFrame):
    # scenario 1: 1 land turn one and draw a land on turn two and three but not 4
    # scenarios 2 and 3: 2 lands turn one, draw a land either turn two  or three but not four
    # scenario 4: 3 lands turn one, dont draw a land on turn two, three of four

    # scenario 1 calculations - we start with an opening hand with 1 land
    one_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 1]["prob"][1]
    card_count_s1 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s1 = land_count - 1 # one of the opening hand cards is a land
    nonland_count_s1 = card_count_s1 - land_count_s1
    # turn 2 draw is a land
    prob_s1 = one_land_turn_one * (land_count_s1 / card_count_s1)
    card_count_s1 -= 1
    land_count_s1 -= 1
    # turn 3 draw is a land
    prob_s1 = prob_s1 * (land_count_s1 / card_count_s1)
    card_count_s1 -= 1
    land_count_s1 -= 1
    # turn 4 draw is a nonland
    prob_s1 = prob_s1 * (nonland_count_s1 / card_count_s1)
    print(prob_s1)

    # scenario 2  and 3 calculations (they are the same probability)- we start with an opening hand with 2 lands
    two_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 2]["prob"][2]
    card_count_s2 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s2 = land_count - 2 # two of the opening hand cards are lands
    nonland_count_s2 = card_count_s2 - land_count_s2
    # turn two draw a land
    prob_s2 = two_land_turn_one * (land_count_s2 / card_count_s2)
    card_count_s2 -= 1 
    land_count_s2 -= 1 
    # turn 3 draw a nonland
    prob_s2 = prob_s2 * (nonland_count_s2 / card_count_s2)
    card_count_s2 -= 1
    nonland_count_s2 -= 1
    # turn 4 draw a nonland
    prob_s2 = prob_s2 * (nonland_count_s2 / card_count_s2)
    print(prob_s2)

    # scenario 4 calculations - we start with 3 lands
    three_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 3]["prob"][3]
    # after drawing opening hand
    card_count_s4 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s4 = land_count - 3 # three of the opening hand cards are lands
    nonland_count_s4 = card_count_s4 - land_count_s4
    # turn two draw a nonland
    prob_s4 = three_land_turn_one * (nonland_count_s4 / card_count_s4)
    card_count_s4 -= 1 
    nonland_count_s4 -= 1 
    # turn 3 draw a nonland
    prob_s4 = prob_s4 * (nonland_count_s4 / card_count_s4)
    card_count_s4 -= 1
    nonland_count_s4 -= 1
    # turn 4 draw a nonland
    prob_s4 = prob_s4 * (nonland_count_s4 / card_count_s4)
    print(prob_s4)

    return prob_s1 + (2 * prob_s2) + prob_s4

def missLandTurnFive(card_count: int, land_count: int, opening_hand_land_dist: pd.DataFrame):
    # scenario 1: 1 land turn one and draw a land on turn 2,3,4 but not 5
    # scenario 2 and 3: 2 land turn one, draw a land on turn 2,3, or 3,4 but not 5
    # scenario 3, 4 and 5: 3 land turn one, draw a land on turn 2, 3, or 4 but not 5
    # scenario 6: 4 land turn one, don't draw a land on turn 2, 3, 4 or 5

    # scenario 1 calculations - we start with an opening hand with 1 land
    one_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 1]["prob"][1]
    card_count_s1 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s1 = land_count - 1 # one of the opening hand cards is a land
    nonland_count_s1 = card_count_s1 - land_count_s1
    # turn 2 draw is a land
    prob_s1 = one_land_turn_one * (land_count_s1 / card_count_s1)
    card_count_s1 -= 1
    land_count_s1 -= 1
    # turn 3 draw is a land
    prob_s1 = prob_s1 * (land_count_s1 / card_count_s1)
    card_count_s1 -= 1
    land_count_s1 -= 1
    # turn 4 draw is a nonland
    prob_s1 = prob_s1 * (nonland_count_s1 / card_count_s1)
    print(prob_s1)

    # scenario 2  and 3 calculations (they are the same probability)- we start with an opening hand with 2 lands
    two_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 2]["prob"][2]
    card_count_s2 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s2 = land_count - 2 # two of the opening hand cards are lands
    nonland_count_s2 = card_count_s2 - land_count_s2
    # turn two draw a land
    prob_s2 = two_land_turn_one * (land_count_s2 / card_count_s2)
    card_count_s2 -= 1 
    land_count_s2 -= 1 
    # turn 3 draw a nonland
    prob_s2 = prob_s2 * (nonland_count_s2 / card_count_s2)
    card_count_s2 -= 1
    nonland_count_s2 -= 1
    # turn 4 draw a nonland
    prob_s2 = prob_s2 * (nonland_count_s2 / card_count_s2)
    print(prob_s2)

    # scenario 4 calculations - we start with 3 lands
    three_land_turn_one = opening_hand_land_dist.loc[opening_hand_land_dist["num_lands_drawn"] == 3]["prob"][3]
    # after drawing opening hand
    card_count_s4 = card_count - len(opening_hand_land_dist) + 1 # we've drawn the opening hand
    land_count_s4 = land_count - 3 # three of the opening hand cards are lands
    nonland_count_s4 = card_count_s4 - land_count_s4
    # turn two draw a nonland
    prob_s4 = three_land_turn_one * (nonland_count_s4 / card_count_s4)
    card_count_s4 -= 1 
    nonland_count_s4 -= 1 
    # turn 3 draw a nonland
    prob_s4 = prob_s4 * (nonland_count_s4 / card_count_s4)
    card_count_s4 -= 1
    nonland_count_s4 -= 1
    # turn 4 draw a nonland
    prob_s4 = prob_s4 * (nonland_count_s4 / card_count_s4)
    print(prob_s4)

    return prob_s1 + (2 * prob_s2) + prob_s4

def playLandEachTurn(card_count: int, land_count: int, turn_number: int, on_play: bool):
    opening_hand_size = 7 + ~on_play
    print(opening_hand_size)



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

    print(missLandTurnOne(card_count, land_count, opening_hand_land_dist))
    print(missLandTurnTwo(card_count, land_count, opening_hand_land_dist))
    print(missLandTurnThree(card_count, land_count, opening_hand_land_dist))
    missLandTurnFour(card_count, land_count, opening_hand_land_dist)


    #print(json.dumps(deck_dict, indent=1))



    
