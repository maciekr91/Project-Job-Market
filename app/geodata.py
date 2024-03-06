import yaml
import pickle
import pandas as pd
import requests

config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']
GEO_DICT_PATH = config['GEO_DICT_PATH']


def extract_geofeatures(geodata: dict):
    lat = geodata['lat']
    lon = geodata['lon']

    address_parts = geodata['display_name'].split(',')
    for part in address_parts:
        if "województwo" in part:
            voivodeship = part.strip().split(' ')[1]
            break
        elif "Metropolia" in part or "Częstochowa" in part or "Bielsko-Biała" in part:
            voivodeship = 'śląskie'
            break
        else:
            voivodeship = 'Not specified'

    return lat, lon, voivodeship


def get_geodata():
    with open(DB_PATH, 'rb') as file:
        offers_db = pickle.load(file)
    cities = offers_db[offers_db['voivodeship'].isna()]['location'].drop_duplicates()

    geo_dict = {}

    nominatim_url = "https://nominatim.openstreetmap.org/search?format=json&country=Poland&city="

    for city in cities:
        geodata = requests.get(nominatim_url + city).json()

        if geodata:
            lat, lon, voivodeship = extract_geofeatures(geodata[0])
            geo_dict[city] = {
                'lat': lat,
                'lon': lon,
                'voivodeship': voivodeship
            }

    with open(GEO_DICT_PATH, 'wb') as file:
        pickle.dump(geo_dict, file)


def fill_empty_voivodeship(row: pd.Series, geo_dict: dict):
    if pd.isna(row['voivodeship']):
        if row['location'] in geo_dict:
            return geo_dict[row['location']]['voivodeship']
        else:
            return 'Not specified'
    else:
        return row['voivodeship']


def geodata_todb():
    with open(DB_PATH, 'rb') as file:
        offers_db = pickle.load(file)
    with open(GEO_DICT_PATH, 'rb') as file:
        geo_dict = pickle.load(file)

    offers_db['voivodeship'] = offers_db.apply(lambda row: fill_empty_voivodeship(row, geo_dict), axis=1)

    with open(DB_PATH, 'wb') as file:
        pickle.dump(offers_db, file)
