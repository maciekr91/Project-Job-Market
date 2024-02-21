import pickle
import pandas as pd
from datetime import datetime

from jjit import search_jjit
from pracuj import search_pracuj

db_path = 'offers_db'

def prepare_tech_dict():

    offers_db = pickle.load(open(db_path, 'rb'))

    tech_dict = {}

    for offer_list in offers_db['technologies']:
        for tech in offer_list:
            if tech in tech_dict:
                tech_dict[tech] += 1
            else:
                tech_dict[tech] = 1

    with open('tech_dict', 'wb') as file:
        pickle.dump(tech_dict, file)

def search_offers(pracuj_url, jjit_categories, jjit_experience):
    offers_jjit = search_jjit(jjit_categories, jjit_experience)
    offers_pracuj = search_pracuj(pracuj_url)

    new_offers = pd.concat([offers_jjit, offers_pracuj])
    new_offers = new_offers.drop_duplicates(subset=new_offers.columns[:-2])

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    new_offers['added_at'] = current_time

    try:
        offers_db = pickle.load(open(db_path, 'rb'))
        backup_file_name = current_time[:10] + '_backup'
        pickle.dump(offers_db, open(backup_file_name, 'wb'))
        offers_updated = pd.concat([offers_db, new_offers])
        offers_updated = offers_updated.drop_duplicates(subset=offers_db.columns[:-3])
        with open(db_path, 'wb') as file:
            pickle.dump(offers_updated.reset_index(drop=True), file)

    except FileNotFoundError:
        with open(db_path, 'wb') as file:
            pickle.dump(new_offers.reset_index(drop=True), file)

    prepare_tech_dict()
