import json
import yaml
import os
import sqlite3
import pandas as pd


config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']


def create_db_if_not_exists():
    """
    This function checks for the existence of a database at the specified DB_PATH. If the
    database does not exist, it creates a new SQLite database and defines the 'offers' table
    with columns for job offer details. If the database already exists, it simply connects
    to the database without modifying it.
    """
    create_offers_table = """
    CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site TEXT NOT NULL,
    experience TEXT NOT NULL, 
    name TEXT NOT NULL,
    company TEXT NOT NULL, 
    location TEXT,
    work_mode TEXT,
    salary_avg FLOAT,
    salary_low FLOAT,
    salary_high FLOAT,
    technologies TEXT,
    link TEXT,
    added_at TEXT,
    voivodeship TEXT
    );
    """

    if os.path.exists(DB_PATH):
        print("Succesfully connected to Database")
    else:
        with sqlite3.connect(DB_PATH) as connection:
            cursor = connection.cursor()
            cursor.execute(create_offers_table)
            connection.commit()
        print("New database created")


def save_to_db(offers: pd.DataFrame):
    """
    This function processes the job offers DataFrame to prepare it for database insertion.
    It converts the 'technologies' column to a JSON string and the 'added_at' column to a string type.
    Then, it constructs the data for insertion, excluding the 'id' column, as it is auto-incremented
    by the database. The function uses a SQL INSERT query to add the job offers to the 'offers' table
    in the database.

    Parameters:
    - offers (pd.DataFrame): A DataFrame containing job offer data with columns corresponding to the
                             fields in the 'offers' database table.
    """
    offers['technologies'] = offers['technologies'].apply(lambda row: json.dumps(row))
    offers['added_at'] = offers['added_at'].astype(str)
    db_data = list(zip(*[offers[column].tolist() for column in offers.columns if column != 'id']))

    add_offer_to_db = """
    INSERT INTO 
        offers (site, experience, name, company, location, work_mode, salary_avg, 
                salary_low, salary_high, technologies, link, added_at, voivodeship)
    VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.executemany(add_offer_to_db, db_data)
        connection.commit()


def load_from_db():
    """
    This function executes a SQL query to select all columns from the 'offers' table in the database.
    Function is loading the data into a DataFrame, on which format other operations are performed
    It processes the 'technologies' column, converting JSON-formatted strings back into list object.

    Returns:
    - pd.DataFrame: A DataFrame containing all the data from the 'offers' table.
    """
    select_query = """
        SELECT 
            id, site, experience, name, company, location, work_mode, salary_avg, 
            salary_low, salary_high, technologies, link, added_at, voivodeship
        FROM offers
        """

    with sqlite3.connect(DB_PATH) as connection:
        db_df = pd.read_sql_query(select_query, connection)

        db_df['technologies'] = db_df['technologies'].apply(lambda row: json.loads(row))

    return db_df


def update_voivodeship(updated_df: pd.DataFrame):
    """
    This function takes a pandas DataFrame that contains updated 'voivodeship' information
    alongside corresponding 'id' values. It constructs a set of tuples containing the new
    'voivodeship' values and their associated 'id's. These tuples are then used in a SQL UPDATE
    query to modify the 'voivodeship' values in the database.

    Parameters:
    - updated_df (pd.DataFrame): A DataFrame containing 'voivodeship' and 'id' columns with updated
                                information to be saved to the database.
    """
    update_query = """
        UPDATE offers
        SET voivodeship = ?
        WHERE id = ?
        """

    update_data = list(zip(updated_df['voivodeship'], updated_df['id']))

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.executemany(update_query, update_data)
