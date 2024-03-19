import yaml
import os
import sqlite3
import pandas as pd


config_path = '../config.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

DB_PATH = config['DB_PATH']


def create_db_if_not_exists():
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
    offers['technologies'] = offers['technologies'].apply(lambda row: json.dumps(row))
    offers['added_at'] = offers['added_at'].astype(str)
    db_data = list(zip(*[offers[column].tolist() for column in offers.columns]))

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
    select_query = """
        SELECT 
            site, experience, name, company, location, work_mode, salary_avg, 
            salary_low, salary_high, technologies, link, added_at, voivodeship
        FROM offers
        """

    with sqlite3.connect(DB_PATH) as connection:
        db_df = pd.read_sql_query(query, connection)
        db_df['technologies'] = db_df['technologies'].apply(lambda row: json.loads(row))
        db_df['added_at'] = pd.to_datetime(db_df['added_at'])

    return db_df
