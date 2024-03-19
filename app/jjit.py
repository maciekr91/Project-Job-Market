from bs4 import BeautifulSoup
from bs4.element import Tag
import pandas as pd
import time

from commons import get_driver


def extract_features_jjit(offer: Tag, links: list):
    """
    Extracts key features from a single job offer.

    This function processes a BeautifulSoup Tag representing a job offer and extracts
    various details like name, company, salary, location, work mode, and technologies.
    It also keeps track of processed links to avoid duplicates.

    Parameters:
    - offer (Tag): A BeautifulSoup Tag object representing the job offer.
    - links (list): A list of links that have already been processed.

    Returns:
    - tuple: A tuple containing the extracted offer details and the updated list of links.
    """
    link = offer.find('a', class_="offer_list_offer_link css-4lqp8g")['href']

    if link in links:
        return None, links

    links.append(link)

    name = offer.find('h2', class_="css-1gehlh0").text
    company = offer.find('div', class_="css-aryx9u").text
    salary = offer.find('div', class_="css-17pspck").text
    location = offer.find('div', class_="css-11qgze1").text
    try:
        work_mode = offer.find('div', class_="css-7ktfgf").text
    except (IndexError, AttributeError):
        work_mode = "Not specified"
    technology = offer.find('div', class_="css-yicj0q").find_all('div', class_='css-1am4i4o')
    techs = [tech.text for tech in technology]

    new_offer = [name, company, salary, location, work_mode, techs, link]

    return new_offer, links


def parse_data_jjit(driver, offers: list, links: list):
    """
    Parses the job offers from the page source obtained via the WebDriver.

    Initializes the soup object, iterate over the job offers in the page source
    and extracts details from each offer.
    It uses the 'extract_features_jjit' function to extract details of each offer.

    Parameters:
    - driver: The Selenium WebDriver used to navigate the page.
    - offers (list): A list to collect the data of each job offer.
    - links (list): A list of links that have already been processed.

    Returns:
    - tuple: A tuple containing the list of offers and the list of processed links.
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for offer in soup.find_all('div', class_="css-2crog7"):

        new_offer, links = extract_features_jjit(offer, links)

        if new_offer:
            offers.append(new_offer)

    return offers, links


def scrape_jjit(url: str):
    """
    Scrapes job offers from a given URL using a Selenium WebDriver.

    Initializes a WebDriver, navigates to the given URL, and repeatedly scrolls through
    the page to load all job offers. Scrolling is necessary because site doesn't reveal
    all offers. Instead, they appear while user scrolls down.
    Extracts the data from each offer and compiles it into a list.

    Parameters:
    - url (str): The URL of the website to scrape.

    Returns:
    - list: A list of extracted job offers.
    """
    driver = get_driver()
    driver.get(url)

    start_point = 0
    height = driver.execute_script("return document.body.scrollHeight")

    offers = []
    links = []

    while True:
        for i in range(start_point, height, 700):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
            offers, links = parse_data_jjit(driver, offers, links)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == height:
            break

        start_point = height
        height = new_height

    driver.quit()

    return offers, links


def split_salary_jjit(row):
    """
    Splits salary strings into lowest, highest and average salary.
    If salary in offer is undisclosed returs empty pd.Series

    Parameters:
    - row (str): salary.

    Returns:
    - pd.Series: salary ranges and mean if exists.
    """
    if 'Undisclosed Salary' in row:
        return pd.Series([None, None, None])
    elif '-' in row:
        parts = row.split('-')
        salary_low = int(parts[0].replace(" ", ""))
        salary_high, _ = parts[1].rsplit(" ", 1)
        salary_high = int(salary_high.replace(" ", ""))
        salary_avg = (salary_low + salary_high) / 2
        return pd.Series([salary_low, salary_high, salary_avg])
    else:
        salary, _ = row.rsplit(" ", 1)
        salary = int(salary.replace(" ", ""))
        return pd.Series([salary, salary, salary])


def clear_data_jjit(offers_list: list):
    """
    Turns lists into DataFrame and performs basic cleaning operations

    Parameters:
    - offers_list (list): list of all offers.

    Returns:
    - pd.DataFrame: df of offers after cleaning.
    """
    columns = ['name', 'company', 'salary', 'location', 'work_mode', 'technologies', 'link']
    offers_df = pd.DataFrame(data=offers_list, columns=columns)

    offers_df['link'] = offers_df['link'].apply(lambda row: "https://justjoin.it" + row)
    offers_df['location'] = offers_df['location'].apply(lambda x: x.split(',')[0])
    offers_df['location'] = offers_df['location'].apply(lambda x: x.replace("Warsaw", "Warszawa"))
    offers_df['work_mode'] = offers_df['work_mode'].apply(lambda x: x.replace("Fully remote", "Praca zdalna"))
    offers_df[['salary_low', 'salary_high', 'salary_avg']] = offers_df['salary'].apply(split_salary_jjit)

    offers_df = offers_df[['name', 'company', 'location', 'work_mode', 'salary_avg',
                           'salary_low', 'salary_high', 'technologies', 'link']]

    return offers_df


def merge_new_offers_jjit(url: str, exp: str, offers_all: pd.DataFrame):
    """
    Perfoms scraping one url, cleans results and merges them with previous results

    Parameters:
    - url (str): url
    - exp (str): currently scrapping level of experience
    - offers_all (pd.DataFrame): previosuly scraped offers

    Returns:
    - offers_all (pd.DataFrame): df of merged offers.
    """
    offers, links = scrape_jjit(url)

    if offers:
        new_offers = clear_data_jjit(offers)
        new_offers['experience'] = exp
        return pd.concat([offers_all, new_offers])

    else:
        return offers_all


def search_jjit(categories_list: list):
    """
    Searches and aggregates job offers from JustJoin.It for specified categories and experience levels.
    This function iterates over a list of job categories and predefined experience levels, constructing URLs
    to scrape job offers from JustJoin.It. It compiles the offers into a pd.DataFrame

    Parameters:
    - categories_list (list): A list of job categories to be searched (e.g., ['it', 'marketing']).

    Returns:
    - DataFrame: A pandas DataFrame containing the aggregated job offers.
    """
    offers_all = pd.DataFrame(columns=['experience', 'name', 'company', 'location', 'work_mode', 'salary_avg',
                                       'salary_low', 'salary_high', 'technologies', 'link'])

    experience_list = ['junior', 'mid', 'senior', 'c-level']

    for category in categories_list:
        for exp in experience_list:

            url = f'https://justjoin.it/all-locations/{category}/experience-level_{exp}'
            offers_all = merge_new_offers_jjit(url, exp, offers_all)

    offers_all['site'] = "justjoin.it"

    offers_all = offers_all[['site', 'experience', 'name', 'company', 'location', 'work_mode', 'salary_avg',
                             'salary_low', 'salary_high', 'technologies', 'link']].reset_index(drop=True)

    return offers_all
