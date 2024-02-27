import pickle
import pandas as pd
from datetime import datetime

DB_PATH = '../db/offers_db'
TECH_DICT_PATH = '../db/tech_dict'
BACKUP_PATH = '../db/backup'


def create_tech_dict():
    try:
        with open(DB_PATH, 'rb') as file:
            offers_db = pickle.load(file)

        tech_dict = {}

        for offer_list in offers_db['technologies']:
            for tech in offer_list:
                if tech in tech_dict:
                    tech_dict[tech] += 1
                else:
                    tech_dict[tech] = 1

        with open(TECH_DICT_PATH, 'wb') as file:
            pickle.dump(tech_dict, file)

    except FileNotFoundError:
        print("Couldn't prepare tech_dict. Database not found.")


def save_and_backup(new_offers: pd.DataFrame, duplicates_columns: list):
    backup_day = datetime.now().strftime("%Y-%m-%d")

    try:
        with open(DB_PATH, 'rb') as file:
            offers_db = pickle.load(file)

        backup_file_name = BACKUP_PATH + backup_day
        with open(backup_file_name, 'wb') as file:
            pickle.dump(offers_db, file)

        offers_updated = pd.concat([offers_db, new_offers])
        offers_updated = offers_updated.drop_duplicates(subset=duplicates_columns)

        with open(DB_PATH, 'wb') as file:
            pickle.dump(offers_updated.reset_index(drop=True), file)

    except FileNotFoundError:
        with open(DB_PATH, 'wb') as file:
            pickle.dump(new_offers.reset_index(drop=True), file)
        print("New database was created")


def merge_offers(offers_jjit: pd.DataFrame, offers_pracuj: pd.DataFrame):
    # if columns below are the same we treat offer as duplicate
    duplicates_columns = ['site', 'experience', 'name', 'company']

    new_offers = pd.concat([offers_jjit, offers_pracuj])
    new_offers = new_offers.drop_duplicates(subset=duplicates_columns)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_offers['added_at'] = current_time

    save_and_backup(new_offers, duplicates_columns)

    create_tech_dict()
