import pickle
import pandas as pd
from datetime import datetime
import yaml
import time

from geodata import get_geodata, geodata_todb
from pracuj import search_pracuj
from jjit import search_jjit


config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']
TECH_DICT_PATH = config['TECH_DICT_PATH']
BACKUP_PATH = config['BACKUP_PATH']

# if columns below are the same we treat offer as duplicate
duplicates_columns = ['site', 'experience', 'name', 'company']  # TODO przenieść do config


def create_tech_dict():
    try:
        with open(DB_PATH, 'rb') as db_file:
            offers_db = pickle.load(db_file)

        tech_dict = {}

        for offer_list in offers_db['technologies']:
            for tech in offer_list:
                if tech in tech_dict:
                    tech_dict[tech] += 1
                else:
                    tech_dict[tech] = 1

        with open(TECH_DICT_PATH, 'wb') as tech_file:
            pickle.dump(tech_dict, tech_file)

    except FileNotFoundError:
        print("Couldn't prepare tech_dict. Database not found.")


def save_and_backup(new_offers: pd.DataFrame, duplicates=duplicates_columns):
    backup_day = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(DB_PATH, 'rb') as db_file:
            offers_db = pickle.load(db_file)

        backup_file_name = BACKUP_PATH + backup_day
        with open(backup_file_name, 'wb') as backup_file:
            pickle.dump(offers_db, backup_file)

        offers_updated = pd.concat([offers_db, new_offers])
        offers_updated = offers_updated.drop_duplicates(subset=duplicates)
        new_offers_number = offers_updated.shape[0] - offers_db.shape[0]

        with open(DB_PATH, 'wb') as db_file:
            pickle.dump(offers_updated.reset_index(drop=True), db_file)

        return new_offers_number

    except FileNotFoundError:
        with open(DB_PATH, 'wb') as db_file:
            pickle.dump(new_offers.reset_index(drop=True), db_file)
        return "New database was created"


def merge_offers(offers_jjit: pd.DataFrame, offers_pracuj: pd.DataFrame, duplicates=duplicates_columns):

    new_offers = pd.concat([offers_jjit, offers_pracuj])
    new_offers = new_offers.drop_duplicates(subset=duplicates)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_offers['added_at'] = current_time

    return new_offers


def split_categories(list_to_check: list, master_list: list):
    verified = [element for element in list_to_check if element in master_list]
    not_verified = [element for element in list_to_check if element not in master_list]

    return verified, not_verified


def criteria_verification(categories_list: list = []):
    all_categories = ['javascript', 'html', 'php', 'ruby', 'python', 'java', 'net', 'scala', 'c',
                      'mobile', 'testing', 'devops', 'admin', 'ux', 'pm', 'game', 'analytics',
                      'security', 'data', 'go', 'support', 'erp', 'architecture', 'other']

    categories, error_cat = split_categories(categories_list, all_categories)

    if error_cat:
        print(f'Invalid categories: {error_cat}')

    if not categories:
        categories = all_categories
        print('No valid categories given. Search will be performed in default mode (all categories)')

    print('\n---SEARCHING CRITERIA---')
    print(f'CATEGORIES: {categories}\n')

    return categories


def show_duration(end_time, start_time):
    duration = end_time - start_time
    if duration > 60:
        return str(round(duration/60, 1)) + ' minutes'
    else:
        return str(round(duration, 2)) + ' seconds'


def get_new_data(categories_list: list, duplicates=duplicates_columns):
    verified_categories = criteria_verification(categories_list)

    print("--SCRAPING JUSTJOIN.IT--")
    start_time = time.time()
    offers_jjit = search_jjit(verified_categories)
    time1 = time.time()
    print(f"Scraped {offers_jjit.shape[0]} offers in {show_duration(time1,start_time)}\n")

    print("--SCRAPING PRACUJ.PL--")
    offers_pracuj = search_pracuj(verified_categories)
    time2 = time.time()
    print(f"Scraped {offers_pracuj.shape[0]} offers in {show_duration(time2, time1)}\n")

    print("--SAVING TO DATABSE--")
    new_offers = merge_offers(offers_jjit, offers_pracuj)
    new_offers_number = save_and_backup(new_offers, duplicates)
    time3 = time.time()
    print(f"Added {new_offers_number} new offers in {show_duration(time3, time2)}\n")

    print("--CREATING TECHNOLOGIES DICTIONARY--")
    create_tech_dict()
    time4 = time.time()
    print(f"Technologies dictionary created in {show_duration(time4, time3)}\n")

    print("--GATHERING GEOGRAPHIC DATA--")
    get_geodata()
    geodata_todb()
    time5 = time.time()
    print(f"Geographic data added to database in {show_duration(time5, time4)}\n")

    print(f"--WHOLE PROCESS FINISHED SUCESSFULLY IN {show_duration(time5, start_time)}--")

