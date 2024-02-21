from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

import pandas as pd
import time
import re
import os


def scrap_data_jjit(driver, offers, links):
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for offer in soup.find_all('div', class_="css-2crog7"):

        link = offer.find_all('a', class_="offer_list_offer_link css-4lqp8g")[0]['href']

        if link in links:
            continue

        links.append(link)

        name = offer.find_all('h2', class_="css-1gehlh0")[0].text
        company = offer.find_all('div', class_="css-aryx9u")[0].text
        salary = offer.find_all('div', class_="css-17pspck")[0].text
        location = offer.find_all('div', class_="css-11qgze1")[0].text
        try:
            work_mode = offer.find_all('div', class_="css-7ktfgf")[0].text
        except IndexError:
            work_mode = "Not specified"

        techs = [tech.text for tech in
                 offer.find_all('div', class_="css-yicj0q")[0].find_all('div', class_='css-1am4i4o')]

        new_offer = [name, company, salary, location, work_mode, techs, link]

        offers.append(new_offer)

    return offers, links

def jjit_scroll(url):

    current_dir = os.path.dirname(os.path.abspath(__file__))
    driver_path = os.path.join(current_dir, 'chromedriver.exe')
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service)

    driver.get(url)

    start_point = 0
    height = driver.execute_script("return document.body.scrollHeight")

    offers = []
    links = []

    while True:
        for i in range(start_point, height, 700):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.5)
            offers, links = scrap_data_jjit(driver, offers, links)

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == height:
            break

        start_point = height
        height = new_height

    driver.quit()

    return offers, links


def split_salary(row):
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


def clear_data_jjit(offers_list):
    columns = ['name', 'company', 'salary', 'location', 'work_mode', 'technologies', 'link']
    offers_df = pd.DataFrame(data=offers_list, columns=columns)

    offers_df['link'] = offers_df['link'].apply(lambda row: "https://justjoin.it" + row)

    offers_df['location'] = offers_df['location'].apply(lambda x: x.split(',')[0])
    offers_df['location'] = offers_df['location'].apply(lambda x: x.replace("Warsaw", "Warszawa"))

    offers_df['work_mode'] = offers_df['work_mode'].apply(lambda x: x.replace("Fully remote", "Praca zdalna"))

    offers_df[['salary_low', 'salary_high', 'salary_avg']] = offers_df['salary'].apply(split_salary)

    offers_df = offers_df[['name', 'company', 'location', 'work_mode', 'salary_avg',
                           'salary_low', 'salary_high', 'technologies', 'link']]

    return offers_df


def search_jjit(categories_list, experience_list):
    offers_all = pd.DataFrame(columns=
                              ['experience', 'name', 'company', 'location', 'work_mode', 'salary_avg',
                               'salary_low', 'salary_high', 'technologies', 'link'])

    for category in categories_list:
        for exp in experience_list:
            url = 'https://justjoin.it/all-locations/' + category + '/experience-level_' + exp

            offers, links = jjit_scroll(url)

            if not offers:
                continue

            offers_df = clear_data_jjit(offers)

            offers_df['experience'] = exp

            offers_all = pd.concat([offers_all, offers_df])

    offers_all['site'] = "justjoin.it"

    offers_all = offers_all[['site', 'experience', 'name', 'company', 'location', 'work_mode', 'salary_avg',
                             'salary_low', 'salary_high', 'technologies', 'link']].reset_index(drop=True)

    return offers_all