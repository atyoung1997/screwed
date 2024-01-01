import json
import numpy as np
import os
import pandas as pd
import pickle
import re
import requests
import sys

from math import comb
from time import sleep

SCRYFALL_REQUEST_URL = "https://api.scryfall.com"
LAND_REGEX = r"( Land | Land$|^Land |^Land$)"
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
        if re.search(LAND_REGEX, deck_dict[card_name]["type_line"]):
            land_count += deck_dict[card_name]["count"]
    return land_count

def getCardCount(deck_dict: dict):
    card_count = 0
    for card_name in deck_dict.keys():
        card_count += deck_dict[card_name]["count"]
    return card_count

def getAverageCMC(deck_dict: dict):
    card_count = 0
    total_cmc = 0
    for card_name in deck_dict.keys():
        if not re.search(LAND_REGEX, deck_dict[card_name]["type_line"]):
            card_count += deck_dict[card_name]["count"]
            total_cmc += deck_dict[card_name]["cmc"] * deck_dict[card_name]["count"]
    return total_cmc / card_count


def getLandDistribution(card_count: int, land_count: int, num_cards_drawn: int):
    nonland_count = card_count - land_count
    prob_list = []
    for num_lands_drawn in range(0, num_cards_drawn+1):
        prob = comb(land_count, num_lands_drawn) * comb(nonland_count, num_cards_drawn - num_lands_drawn) / comb(card_count, num_cards_drawn)
        prob_list.append(prob)

    return prob_list

def playLandEachTurn(card_count: int, land_count: int, turn_number: int, starting_hand_size: int):
    num_cards_drawn_at_turn = turn_number - 1 + starting_hand_size
    land_dist = getLandDistribution(card_count, land_count, num_cards_drawn_at_turn)
    print(np.sum(land_dist[turn_number:]))

def analyzeMulligans(card_count: int, land_count: int, min_lands_keep: int = 3, max_lands_keep: int = 5, hard_stop: int = 4, starting_hand_size: int = 7):
    mull_land_dist_list = [getLandDistribution(card_count, land_count, num_cards_drawn) for num_cards_drawn in range(starting_hand_size, 0, -1)]
    if min_lands_keep > starting_hand_size or min_lands_keep < 0:
        raise ValueError(f"min_lands_keep must be a value between 0 and {starting_hand_size} (starting_hand_size)")
    if max_lands_keep > starting_hand_size or max_lands_keep < 1:
        raise ValueError(f"max_lands_keep must be a value between 1 and {starting_hand_size} (starting_hand_size)")

    # calculate mull and keep probability for each number of cards drawn
    keep_prob_list, mull_prob_list = [], []
    for land_dist in mull_land_dist_list:
        if land_dist == []:
            keep_prob = 0
        else:
            keep_prob = sum(land_dist[min_lands_keep : max_lands_keep + 1])
        keep_prob_list.append(keep_prob)
        mull_prob_list.append(1 - keep_prob)
    print(keep_prob_list)
    print(mull_prob_list)

    # probability of mulling exactly a certain number of times
    for num_mulls in range(len(keep_prob_list)):
        if num_mulls == 0:
            exact_mull_prob_list = [keep_prob_list[num_mulls]]
        else:
            exact_mull_prob_list.append(np.prod(mull_prob_list[0:num_mulls]) * keep_prob_list[num_mulls])
    
    # based on parameters, you may reach a point where mulling further will make it impossible to meet the param requirements
    prob_find_keepable_mull = sum(exact_mull_prob_list)
    if prob_find_keepable_mull < 1:
        i = len(exact_mull_prob_list) - 1
        while i >= 0:
            if exact_mull_prob_list[i] != 0:
                last_possible_mull = i
                break
            i -= 1
    print(f"With {land_count} lands in a {card_count} card deck, if you mull until you hit {min_lands_keep}-{max_lands_keep} lands, there will be a {1 - prob_find_keepable_mull:.2%} chance that you mull {last_possible_mull} times and never hit the required lands.")
    print(f"{last_possible_mull=}")
    
    

    print(f"{exact_mull_prob_list=}")
    print(f"{sum(exact_mull_prob_list)=}")
        



    
        
    
    # print(json.dumps(mull_analysis_dict, indent = 1))

def playLandEachTurnWithMulligan(card_count: int, land_count: int, turn_number: int, mull_to: int):
    print("tbd")

def playXLandsInYTurns(card_count: int, land_count: int, lands_played: int, turn_number: int):
    print("tbd")

if __name__ == "__main__":
    # deck_dict = readAndFormatDecklist(test_path_1)
    # deck_dict = retrieveScryfallData(deck_dict)
    # deck_dict.keys()
    # print(deck_dict)
    # with open("C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\formatted_file.p", 'wb') as formatted_file:   
    #     pickle.dump(deck_dict, formatted_file)
    with open("C:\\Users\\atyou\\github_repos\\screwed\\testing_files\\formatted_file.p", 'rb') as formatted_file:
        deck_dict = pickle.load(formatted_file)
    # print(deck_dict[list(deck_dict.keys())[0]])
    # print(json.dumps(deck_dict, indent = 1))
    land_count = getLandCount(deck_dict)
    card_count = getCardCount(deck_dict)

    analyzeMulligans(card_count, land_count, min_lands_keep=2, max_lands_keep=5, hard_stop=4, starting_hand_size=7)
    analyzeMulligans(card_count, land_count, min_lands_keep=3, max_lands_keep=5, hard_stop=4, starting_hand_size=7)
    print(getAverageCMC(deck_dict))
    #print(json.dumps(deck_dict, indent=1))



    
