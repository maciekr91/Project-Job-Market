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
duplicates_columns = ['site', 'experience', 'name', 'company']


def create_tech_dict():
    """
    This function reads the job offers database and compiles a dictionary where each key
    is a technology and its value is the count of how many times that technology appears
    in the database. The resulting dictionary is then saved to a file. If the database file
    is not found, an error message is printed.
    """
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
    """
    This function updates the existing offers database with new offers. It first creates a backup
    of the current database, then appends the new offers to the database, removing any duplicates
    based on specified columns. It also handles the creation of a new database file if it doesn't
    already exist.

    Parameters:
    - new_offers (pd.DataFrame): A DataFrame containing new job offers to be added to the database.
    - duplicates (list, optional): A list of columns to consider when removing duplicates.

    Returns:
    - int or str: The number of new offers added to the database, or a message indicating that a
                  new database was created.
    """
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
    """
    This function combines job offers from JustJoin.It and Pracuj.pl into a single DataFrame.
    It removes duplicates based on specified columns and adds a timestamp indicating when the
    offers were added to the merged dataset. The offers have been standardized to a common format
    in respectively files

    Parameters:
    - offers_jjit (pd.DataFrame): A DataFrame containing job offers from JustJoin.It.
    - offers_pracuj (pd.DataFrame): A DataFrame containing job offers from Pracuj.pl.
    - duplicates (list): A list of columns to consider when removing duplicates.

    Returns:
    - pd.DataFrame: A DataFrame containing the merged and deduplicated job offers, with an
                   added timestamp for each offer.
    """
    new_offers = pd.concat([offers_jjit, offers_pracuj])
    new_offers = new_offers.drop_duplicates(subset=duplicates)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_offers['added_at'] = current_time

    return new_offers


def split_categories(list_to_check: list, master_list: list):
    """
    This function takes a list of categories and checks each category against a master
    list of valid categories. It separates the categories into two lists: one containing
    categories that are verified (present in the master list) and another containing
    categories that are not verified (not present in the master list).
    """
    verified = [element for element in list_to_check if element in master_list]
    not_verified = [element for element in list_to_check if element not in master_list]

    return verified, not_verified


def criteria_verification(categories_list: list = []):
    """
    This function checks if the provided categories are valid against a predefined list
    of all available categories. It informs the user about any invalid categories and
    defaults to using all categories if none are valid or provided. The function also
    displays the search criteria being used.

    Parameters:
    - categories_list (list): A list of categories to be used in the job search.
                                        Defaults to an empty list, which means all categories.

    Returns:
    - list: A list of valid categories to be used in the search. Defaults to all categories
            if the provided list is empty or contains only invalid categories.
    """
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
    """
    This function displays duration in seconds or minutes regradless which is more appropriate
    """
    duration = end_time - start_time
    if duration > 60:
        return str(round(duration/60, 1)) + ' minutes'
    else:
        return str(round(duration, 2)) + ' seconds'


def get_new_data(categories_list: list, duplicates=duplicates_columns):
    """
    Compiles the entire process of data acquisition, processing, and storage.

    This function takes a list of categories and oversees the scraping of job offers from
    JustJoin.It and Pracuj.pl, based on verified categories. It merges the offers from both sources,
    removes duplicates, and saves the updated offers to the database. Additionally, the function
    creates a technologies dictionary and gathers geographic data for the offers. Execution times
    for each step are printed.

    Parameters:
    - categories_list (list): A list of categories based on which the job offers are scraped.
    - duplicates (list, optional): Columns to consider when removing duplicates from the offers.
                                   Defaults to `duplicates_columns`.

    """
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

