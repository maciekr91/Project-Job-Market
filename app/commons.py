import pickle
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import yaml

from geodata import get_geodata, geodata_todb

config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']
TECH_DICT_PATH = config['TECH_DICT_PATH']
BACKUP_PATH = config['BACKUP_PATH']


def get_driver():
    current_dir = os.getcwd()
    driver_path = os.path.join(current_dir, 'chromedriver.exe')
    service = Service(executable_path=driver_path)
    chrome_options = Options()
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(2048, 1536)

    return driver


def close_popup(driver, css_selector: str):
    try:
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, css_selector)))
        close_button = driver.find_element(By.CSS_SELECTOR, css_selector)
        close_button.click()
    except Exception as e:
        print("Exception while closing popup: ", e)


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

# TODO przenieść to do innej funkcji

    create_tech_dict()
    # get_geodata()
    # geodata_todb()

