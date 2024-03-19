import yaml
import pickle
import pandas as pd
import requests

from database import load_from_db, update_voivodeship

config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']
GEO_DICT_PATH = config['GEO_DICT_PATH']


def extract_geofeatures(geodata: dict):
    """
    This function parses a dictionary containing geographic data to extract the latitude, longitude,
    and the voivodeship. It identifies the voivodeship based on the address components in the geodata,
    with special handling for certain areas. If a voivodeship cannot be determined, it defaults to 'Not specified'.

    Parameters:
    - geodata (dict): A dictionary containing geographic data, including 'lat', 'lon', and
                      'display_name' keys.

    Returns:
    - tuple: A tuple containing the latitude, longitude, and the identified voivodeship.
    """
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
    """
     This function reads the job offers database, extracts unique cities with unspecified voivodeships,
     and queries the Nominatim API for each city to obtain geographic data. It then processes this data
     to extract latitude, longitude, and voivodeship, storing the results in a dictionary. This dictionary
     is then saved to a file.
     """
    offers_db = load_from_db()

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

    with open(GEO_DICT_PATH, 'wb') as geo_file:
        pickle.dump(geo_dict, geo_file)


def fill_empty_voivodeship(row: pd.Series, geo_dict: dict):
    """
    This function checks if the 'voivodeship' field in a given job offer (represented as a pandas Series)
    is missing. If so, it attempts to fill this field using the corresponding voivodeship from the
    geographic data dictionary, based on the offer's location. If the location is not in the dictionary,
    or if the voivodeship is already specified, the function returns the current voivodeship value.

    Parameters:
    - row (pd.Series): A pandas Series representing a single job offer, including 'location' and
                       'voivodeship' fields.
    - geo_dict (dict): A dictionary containing geographic data, mapping locations to their
                       respective voivodeships.

    Returns:
    - str: The voivodeship of the job offer, either retrieved from the geographic data dictionary or
           the original value in the Series.
    """
    if pd.isna(row['voivodeship']):
        if row['location'] in geo_dict:
            return geo_dict[row['location']]['voivodeship']
        else:
            return 'Not specified'
    else:
        return row['voivodeship']


def geodata_todb():
    """
    This function reads the existing job offers database and a geographic data dictionary from their
    respective files. It then updates each job offer in DataFrame, filling in missing voivodeship
    information using the geographic data dictionary. The updated DataFrame is used to update DB
    """
    offers_db = load_from_db()

    with open(GEO_DICT_PATH, 'rb') as geo_file:
        geo_dict = pickle.load(geo_file)

    offers_db['voivodeship'] = offers_db.apply(lambda row: fill_empty_voivodeship(row, geo_dict), axis=1)

    update_voivodeship(offers_db)
